import json
import tempfile
import time
import uuid

from asgiref.sync import async_to_sync
from celery import chord, signature
from channels.layers import get_channel_layer
from langchain_core.messages import HumanMessage
from django.utils import timezone
from django.db.models import Count

from backend.celery import app
from prelo.aws.s3_utils import file_exists, upload_file_to_s3, download_file_from_s3
from prelo.chat.history import get_prelo_message_history
from prelo.events import record_prelo_event, record_smd_event
from prelo.investor.analysis import check_deck_against_thesis
from prelo.models import InvestmentFirm, PitchDeck, PitchDeckAnalysis, PitchDeckSlide, Investor, Company, ConversationDeckUpload, \
    PitchDeckAnalysisError, MessageToConfirm
from prelo.notifications.investor import investor_created
from prelo.pitch_deck.analysis import analyze_deck, investor_analysis, compare_deck_to_previous_version, \
    initial_analysis, gtm_strategy
from prelo.pitch_deck.investor.concerns import concerns_analysis
from prelo.pitch_deck.investor.founders import extract_founder_info
from prelo.pitch_deck.processing import pdf_to_images, encode_image, cleanup_local_file
from prelo.pitch_deck.reporting import combine_into_report, create_risk_report
from prelo.prompts.prompts import PITCH_DECK_SLIDE_PROMPT
from prelo.submind.Investor import InvestorSubmind
from submind.llms.submind import SubmindModelFactory


@app.task(name="prelo.tasks.check_for_decks")
def check_for_decks():
    decks = PitchDeck.objects.filter(status=PitchDeck.CREATED).all()
    for deck in decks:
        # check s3 path to see if a file exists yet
        # if it does, change status to UPLOADED
        if file_exists(deck.s3_path):
            deck.status = PitchDeck.UPLOADED
            # get deck version from s3 path:
            version = deck.s3_path.split("/")[-2]
            deck.version = version if version.isnumeric() else 1
            deck.save()
            company_to_populate = Company.objects.filter(deck_uuid=deck.uuid).first()
            print(f"Company to populate: {company_to_populate}")
            if not company_to_populate:
                process_deck.delay(deck.id)
            else:
                process_deck.delay(deck.id, company_to_populate.id)


@app.task(name="prelo.tasks.check_for_analysis")
def check_for_analysis():
    decks_to_analyze = PitchDeckAnalysis.objects.filter(deck__status=PitchDeck.READY_FOR_ANALYSIS).all()
    for deck_analysis in decks_to_analyze:
        analyze_deck_task.delay(deck_analysis.id)


@app.task(name="prelo.tasks.check_for_reporting")
def check_for_reporting():
    decks_to_report = PitchDeckAnalysis.objects.filter(deck__status=PitchDeck.READY_FOR_REPORTING).all()
    for deck_analysis in decks_to_report:
        create_report_for_deck.delay(deck_analysis.id)


@app.task(name="prelo.tasks.thesis_check")
def thesis_check(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    investor_report = check_deck_against_thesis(pitch_deck_analysis)


@app.task(name="prelo.tasks.create_report_for_deck")
def create_report_for_deck(pitch_deck_analysis_id: int, investor_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    investor = Investor.objects.get(id=investor_id)
    investor_report = check_deck_against_thesis(pitch_deck_analysis, investor)
    report = combine_into_report(pitch_deck_analysis, investor_report)
    print(report)


@app.task(name="prelo.tasks.identify_biggest_risk")
def identify_biggest_risk(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    top_concern, objections, how_to_overcome = create_risk_report(pitch_deck_analysis)
    analysis = concerns_analysis(pitch_deck_analysis)

    try:
        scores = pitch_deck_analysis.deck.scores
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning
            },
            'product': {
                'score': scores.product,
                'reason': scores.product_reasoning
            },
            'traction': {
                'score': scores.traction,
                'reason': scores.traction_reasoning
            },
            'final': {
                'score': scores.final_score,
                'reason': scores.final_reasoning
            }
        }
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                {"type": "deck.report.update",
                                                 "top_concern": top_concern, "objections": objections,
                                                 "how_to_overcome": how_to_overcome,
                                                 'pitch_deck_analysis': analysis,
                                                 "scores": score_object})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return


@app.task(name="prelo.tasks.populate_company_data")
def populate_company_data(company_id, pitch_deck_analysis_id):
    initial_analysis(pitch_deck_analysis_id, company_id)
    gtm_strategy(pitch_deck_analysis_id, company_id)


@app.task(name="prelo.tasks.analyze_deck")
def analyze_deck_task(pitch_deck_analysis_id: int, company_id=None):
    print(f"ANALYZING DECK WITH COMPANY ID: {company_id}")
    start_time = time.perf_counter()
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.ANALYZING
    pitch_deck_analysis.deck.save()
    step = "Initial Analysis"
    try:
        if "prelovc" in pitch_deck_analysis.deck.s3_path:
            initial_analysis(pitch_deck_analysis_id, company_id)
            step = "Extract Founder Info"
            extract_founder_info(pitch_deck_analysis)
            step = "Analyze Deck"
            analyze_deck(pitch_deck_analysis)
            step = "Investor Analysis"
            investor_analysis(pitch_deck_analysis)
            end_time = time.perf_counter()
            record_prelo_event({
                "deck_uuid": pitch_deck_analysis.deck.uuid,
                "event": "Deck Analyzed",
                "processing_time": end_time - start_time
            })
            try:
                channel_layer = get_channel_layer()
                # deck_uuid = event["deck_uuid"]
                #         deck_score = event["deck_score"]
                #         recommended_next_steps = event["recommended_next_steps"]
                #         report_summary = event["report_summary"]
                #         report_uuid = event["report_uuid"]
                conversation = ConversationDeckUpload.objects.get(deck_uuid=pitch_deck_analysis.deck.uuid)
                company = Company.objects.filter(deck_uuid=pitch_deck_analysis.deck.uuid).first()

                # need to add the deck report to the conversation history in a way that can rebuild it. save message as JSON blob?
                history = get_prelo_message_history(f'custom_claude_{conversation.conversation_uuid}')
                history.add_ai_message(json.dumps({
                    "deck_uuid": pitch_deck_analysis.deck.uuid,
                    "status": "analyzed",
                    "deck_score": pitch_deck_analysis.investor_report.investment_potential_score,
                    "recommended_next_steps": pitch_deck_analysis.investor_report.recommended_next_steps,
                    "report_summary": pitch_deck_analysis.investor_report.summary,
                    "report_uuid": pitch_deck_analysis.investor_report.uuid,
                    "company_name": company.name
                }))
                async_to_sync(channel_layer.group_send)(conversation.conversation_uuid,
                                                        {"type": "deck.analyzed",
                                                         "deck_uuid": pitch_deck_analysis.deck.uuid,
                                                         "report_uuid": pitch_deck_analysis.investor_report.uuid,
                                                         "deck_score": pitch_deck_analysis.investor_report.investment_potential_score,
                                                         "report_summary": pitch_deck_analysis.investor_report.summary,
                                                         "recommended_next_steps": pitch_deck_analysis.investor_report.recommended_next_steps,
                                                         "company_name": company.name,
                                                         })
                return
            except Exception as e:
                print(e)
                return
                # not vital, just try to return response to chat if possible.
        else:
            if pitch_deck_analysis.deck.version > 1:
                print("Checking updated version")
                # need to compare new version results to old version
                step = "Compare Deck to Previous Version"
                top_concern, objections, how_to_overcome, analysis, previous_scores, updated_scores = compare_deck_to_previous_version(
                    pitch_deck_analysis)
                end_time = time.perf_counter()
                record_smd_event({
                    "deck_uuid": pitch_deck_analysis.deck.uuid,
                    "event": "Deck Compared To Previous Version",
                    "processing_time": end_time - start_time
                })
                print(f"Top Concern: {top_concern}")
                try:
                    scores = pitch_deck_analysis.deck.scores
                    print(f"Scores: {scores}")
                    score_object = {
                        'market': {
                            'score': scores.market_opportunity,
                            'reason': scores.market_reasoning,
                            'delta': updated_scores.market_opportunity - previous_scores.market_opportunity
                        },
                        'team': {
                            'score': updated_scores.team,
                            'reason': updated_scores.team_reasoning,
                            'delta': updated_scores.team - previous_scores.team

                        },
                        'product': {
                            'score': updated_scores.product,
                            'reason': updated_scores.product_reasoning,
                            'delta': updated_scores.product - previous_scores.product
                        },
                        'traction': {
                            'score': updated_scores.traction,
                            'reason': updated_scores.traction_reasoning,
                            'delta': updated_scores.traction - previous_scores.traction
                        },
                        'final': {
                            'score': updated_scores.final_score,
                            'reason': updated_scores.final_reasoning,
                            'delta': updated_scores.final_score - previous_scores.final_score
                        }
                    }
                    channel_layer = get_channel_layer()

                    async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                            {"type": "deck.report.update",
                                                             "top_concern": top_concern, "objections": objections,
                                                             "how_to_overcome": how_to_overcome,
                                                             'pitch_deck_analysis': analysis,
                                                             "scores": score_object})
                except Exception as e:
                    print(e)
                    return
            else:
                step = "Initial Analysis"
                analyze_deck(pitch_deck_analysis)
                step = "Risk Report"
                top_concern, objections, how_to_overcome = create_risk_report(pitch_deck_analysis)
                step = "Concerns Analysis"
                analysis = concerns_analysis(pitch_deck_analysis)
                end_time = time.perf_counter()
                record_smd_event({
                    "deck_uuid": pitch_deck_analysis.deck.uuid,
                    "event": "Deck Analyzed",
                    "processing_time": end_time - start_time
                })
                try:
                    scores = pitch_deck_analysis.deck.scores
                    score_object = {
                        'market': {
                            'score': scores.market_opportunity,
                            'reason': scores.market_reasoning
                        },
                        'team': {
                            'score': scores.team,
                            'reason': scores.team_reasoning
                        },
                        'product': {
                            'score': scores.product,
                            'reason': scores.product_reasoning
                        },
                        'traction': {
                            'score': scores.traction,
                            'reason': scores.traction_reasoning
                        },
                        'final': {
                            'score': scores.final_score,
                            'reason': scores.final_reasoning
                        }
                    }
                    channel_layer = get_channel_layer()

                    async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                            {"type": "deck.report.update",
                                                             "top_concern": top_concern, "objections": objections,
                                                             "how_to_overcome": how_to_overcome,
                                                             'pitch_deck_analysis': analysis,
                                                             "scores": score_object})
                except Exception as e:
                    print(e)
                    # not vital, just try to return response to chat if possible.
                if company_id is not None:
                    populate_company_data.delay(company_id, pitch_deck_analysis_id)
    except Exception as e:
        print(e)
        error = PitchDeckAnalysisError.objects.create(
            analysis=pitch_deck_analysis,
            step=step,
            error=str(e)
        )
        record_prelo_event({
            "error": str(e),
            "step": step,
            "deck_uuid": pitch_deck_analysis.deck.uuid
        })
        analyze_deck_task.retry(countdown=60, max_retries=5, args=[pitch_deck_analysis_id, company_id])
        # how to record error and attempt retry?


@app.task(name="process_slide")
def process_slide(slide_id):
    slide = PitchDeckSlide.objects.get(id=slide_id)

    image_uri = download_file_from_s3(slide.s3_path)

    print(f"Analyzing image: {image_uri}")
    base64_image = encode_image(image_uri)
    model = SubmindModelFactory.get_model(slide.deck.uuid, "pitch_deck_slide_analysis")
    message = HumanMessage([
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "auto"
            }
        },
        {
            "type": "text",
            "text": PITCH_DECK_SLIDE_PROMPT
        }
    ])
    response = model.invoke([message])

    slide.content = response.content
    slide.save()

    cleanup_local_file(image_uri)


@app.task(name="processing_callback")
def processing_callback(results, deck_id, start_time, company_id=None):
    print(f"PROCESSING CALLBACK WITH COMPANY ID: {company_id}")

    deck = PitchDeck.objects.get(id=deck_id)
    print(f"Processing callback for deck: {deck.name}")
    print(f'Start_time: {start_time}')
    # print("All slides analyzed, cleaning data")
    # cleaned_data = clean_data(raw_slides)
    combined = "\n".join([f"Page: {slide.order}\n{slide.content}" for slide in deck.slides.all()])
    print("Data ingested. Starting analysis")
    analysis = PitchDeckAnalysis.objects.filter(deck=deck).first()
    if analysis:
        analysis.compiled_slides = combined
        analysis.save()
        record_prelo_event({
            "deck_uuid": deck.uuid,
            "event": "Updating Deck Compiled Slides",
        })
    else:
        analysis = PitchDeckAnalysis.objects.create(
            deck=deck,
            compiled_slides=combined
        )

    deck.status = PitchDeck.READY_FOR_ANALYSIS
    deck.save()
    end_time = time.perf_counter()
    analysis.processing_time = end_time - start_time
    analysis.save()
    print(f"Analysis time: {analysis.processing_time} seconds.")
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(deck.uuid,
                                                {"type": "deck.status.update",
                                                 "message": "",
                                                 "id": deck.id, "status": deck.status})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    if company_id is None:
        analyze_deck_task.delay(analysis.id)
    else:
        analyze_deck_task.delay(analysis.id, company_id)


@app.task(name="prelo.tasks.process_deck")
def process_deck(deck_id, company_id=None):
    print(f"PROCESSING DECK WITH COMPANY ID: {company_id}")

    deck = PitchDeck.objects.get(id=deck_id)
    # process the deck
    deck.status = PitchDeck.PROCESSING
    deck.save()
    # analysis = prep_deck_for_analysis(deck)

    start_time = time.perf_counter()
    temp_file = download_file_from_s3(deck.s3_path)

    image_dir = tempfile.gettempdir()
    imgs = pdf_to_images(temp_file, image_dir)

    raw_slides = []
    slides_to_process = []
    for img in imgs:
        image_uri = img['path']
        img_key = f"{deck_id}/{image_uri.split('/')[-1]}"
        upload_file_to_s3(img_key, image_uri)
        slide = PitchDeckSlide.objects.create(
            deck=deck,
            s3_path=img_key,
            order=img['page'],
            uuid=str(uuid.uuid4())
        )
        raw_slides.append(slide)
        slides_to_process.append(process_slide.s(slide.id))

    task_chord = chord(slides_to_process)
    if company_id is None:
        callback = signature('processing_callback', args=(), kwargs={'deck_id': deck.id, "start_time": start_time})
    else:
        callback = signature('processing_callback', args=(),
                             kwargs={'deck_id': deck.id, "start_time": start_time, "company_id": company_id})

    # Executes all tasks in the group in parallel
    result_chord = task_chord(callback)


@app.task(name="prelo.tasks.send_message_to_submind")
def send_message_to_submind(submind_id, message):
    pass


@app.task(name="prelo.tasks.lookup_investors")
def lookup_investors(message: str, session_uuid: str):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(session_uuid,
                                            {"type": "chat.message",
                                             "message": "",
                                             "id": ""})


@app.task(name="prelo.tasks.acknowledge_received")
def acknowledge_received(conversation_uuid: str, deck_uuid: str):
    # look up message
    # delete from db
    message = MessageToConfirm.objects.filter(conversation_uuid=conversation_uuid, deck_uuid=deck_uuid,
                                              type="deck_received").first()
    if message:
        message.acknowledged = True
        message.save()


@app.task(name="prelo.tasks.acknowledged_analyzed")
def acknowledged_analyzed(conversation_uuid:str, deck_uuid:str, report_uuid:str):
    # look up message
    # delete from db
    message = MessageToConfirm.objects.filter(conversation_uuid=conversation_uuid, deck_uuid=deck_uuid, report_uuid=report_uuid, type="deck_analyzed").first()
    if message:
        message.acknowledged = True
        message.save()

@app.task(name="prelo.tasks.acknowledged_created")
def acknowledged_created(conversation_uuid:str):
    # look up message
    # delete from db
    message = MessageToConfirm.objects.filter(conversation_uuid=conversation_uuid, type="submind_created").all()
    if message:
        message.acknowledged = True
        message.save()




@app.task(name="prelo.tasks.resend_messages")
def resend_unacknowledged_messages():
    channel_layer = get_channel_layer()
    messages = MessageToConfirm.objects.filter(acknowledged=False).all()

    for message in messages:
        try:
            print(f"Resending message: {message.type}")
            print(f"Message: {message.message}")
            print(f"Conversation UUID: {message.conversation_uuid}")
            
            message_data = {"type": message.type.replace("_", ".")}
            message_data.update(json.loads(message.message))

            async_to_sync(channel_layer.group_send)(
                message.conversation_uuid,
                message_data
            )

        except Exception as e:
            record_prelo_event({
                "event": "Error Resending Message",
                "message_id": message.id,
                "error": str(e),
                "message": message.message
            })
            print(f"Error resending message: {e}")
            message.acknowledged = True
            message.error = str(e)
            message.save()


@app.task(name="prelo.tasks.create_submind_for_investor")
def create_submind_for_investor(first_name: str, last_name: str, user_id: str, organization_id: int, firm_name: str, firm_url: str, conversation_uuid: str, slug: str, email: str):
    start_time = time.perf_counter()
    investor_name = f"{first_name} {last_name}"
    # Does investor already exist?
    investor = Investor.objects.filter(lookup_id=user_id).first()
    if not investor:    
        investor = Investor.objects.create(first_name=first_name, last_name=last_name, name=investor_name, lookup_id=user_id, email=email)
    else:
        investor.first_name = first_name
        investor.last_name = last_name
        investor.name = investor_name
        investor.email = email
        investor.save()
    investor_submind = InvestorSubmind.create_submind_for_investor(investor_name, firm_name, firm_url)
    investor_submind.learn_about_person(investor_name)    
    investor_submind.compress_knowledge()
    passion = investor_submind.ask("What is your passion?")
    thesis = investor_submind.ask("What is your thesis?")
    check_size = investor_submind.ask("What is your preferred check size?")
    industries = investor_submind.ask("What industries do you invest in?")
    investor.slug = slug
    investor.passion = passion
    investor.thesis = thesis
    investor.check_size = check_size
    investor.industries = industries
    investor.save()
    investment_firm = InvestmentFirm.objects.create(name=firm_name, website=firm_url, lookup_id=organization_id, thesis=thesis)
    investment_firm.save()
    investment_firm.investors.add(investor)
    end_time = time.perf_counter()
    record_prelo_event({
        "event": "Submind Created",
        "investor_id": investor.id,
        "firm_id": investment_firm.id,
        "processing_time": end_time - start_time
    })

    print(f"Submind created for investor: {investor.id}, processing time: {end_time - start_time} seconds.")
    # notify by email.
    investor_created(investor)
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(conversation_uuid,
                                                            {"type": "submind.created",
                                                             "submind_id": investor_submind._submind.id,
                                                             "investor_id": investor.id,
                                                             "firm_id": investment_firm.id,
                                                             "thesis": thesis,
                                                             "passion": passion,
                                                             "check_size": check_size,
                                                             "industries": industries,
                                                             "status": "configured",
                                                             "slug": slug,
                                                             "company": investment_firm.name,
                                                             "name": investor.name
                                                             })

    

@app.task(name="prelo.tasks.cleanup_messages_to_confirm")
def cleanup_messages_to_confirm():
    now = timezone.now()
    total_messages = MessageToConfirm.objects.count()
    
    # Group by type and count
    type_counts = MessageToConfirm.objects.values('type').annotate(count=Count('id'))
    
    # Prepare metrics
    metrics = {
        'total_messages': total_messages,
        'type_counts': {item['type']: item['count'] for item in type_counts},
        'timestamp': now.isoformat()
    }
    
    # Record event with metrics
    record_prelo_event({
        "event": "MessageToConfirm Cleanup",
        "metrics": metrics
    })
    
    # Delete all MessageToConfirm objects
    deleted_count = MessageToConfirm.objects.all().delete()[0]
    
    return f"Cleaned up {deleted_count} MessageToConfirm objects at {now}"
