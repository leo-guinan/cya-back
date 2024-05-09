import tempfile
import time
import uuid
from asgiref.sync import async_to_sync
from celery import group, chord, signature
from channels.layers import get_channel_layer
from decouple import config
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from backend.celery import app
from prelo.aws.s3_utils import file_exists, upload_file_to_s3, download_file_from_s3
from prelo.models import PitchDeck, PitchDeckAnalysis, PitchDeckSlide
from prelo.pitch_deck.analysis import analyze_deck
from prelo.pitch_deck.processing import prep_deck_for_analysis, pdf_to_images, encode_image, cleanup_local_file
from prelo.pitch_deck.reporting import combine_into_report, create_risk_report
from prelo.prompts.prompts import PITCH_DECK_SLIDE_PROMPT
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride


@app.task(name="prelo.tasks.check_for_decks")
def check_for_decks():
    decks = PitchDeck.objects.filter(status=PitchDeck.CREATED).all()
    for deck in decks:
        # check s3 path to see if a file exists yet
        # if it does, change status to UPLOADED
        if file_exists(deck.s3_path):
            deck.status = PitchDeck.UPLOADED
            deck.save()
            process_deck.delay(deck.id)

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


@app.task(name="prelo.tasks.create_report_for_deck")
def create_report_for_deck(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    report = combine_into_report(pitch_deck_analysis)

    message_history = MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{pitch_deck_analysis.deck.uuid}_chat',
        database_name=config('SCORE_MY_DECK_DATABASE_NAME'),
        collection_name=config('SCORE_MY_DECK_COLLECTION_NAME')
    )
    message_history.add_ai_message(report)
    try:

        scores = pitch_deck_analysis.deck.company.scores.first()
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning
            },
            'founder': {
                'score': scores.founder_market_fit,
                'reason': scores.founder_market_reasoning
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
                                                {"type": "deck.score.update", "message": report,
                                                 "id": pitch_deck_analysis.deck.id, "scores": score_object})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return

@app.task(name="prelo.tasks.identify_biggest_risk")
def identify_biggest_risk(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    risk_report = create_risk_report(pitch_deck_analysis)
    message_history = MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{pitch_deck_analysis.deck.uuid}_chat',
        database_name=config('SCORE_MY_DECK_DATABASE_NAME'),
        collection_name=config('SCORE_MY_DECK_COLLECTION_NAME')
    )
    message_history.add_ai_message(risk_report)
    try:
        scores = pitch_deck_analysis.deck.company.scores.first()
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning
            },
            'founder': {
                'score': scores.founder_market_fit,
                'reason': scores.founder_market_reasoning
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
                                                {"type": "deck.score.update", "message": risk_report,
                                                 "id": pitch_deck_analysis.deck.id, "scores": score_object})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return

@app.task(name="prelo.tasks.analyze_deck")
def analyze_deck_task(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.ANALYZING
    pitch_deck_analysis.deck.save()
    analyze_deck(pitch_deck_analysis)
    if pitch_deck_analysis.deck.target_audience == "Founder":
        identify_biggest_risk.delay(pitch_deck_analysis.id)
    else:
        create_report_for_deck.delay(pitch_deck_analysis.id)
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                {"type": "deck.status.update", "message": "",
                                                 "id": pitch_deck_analysis.deck.id,
                                                 "status": pitch_deck_analysis.deck.status,
                                                 "name": pitch_deck_analysis.deck.name
                                                 })
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return

@app.task(name="process_slide")
def process_slide(slide_id):
    slide = PitchDeckSlide.objects.get(id=slide_id)

    image_uri = download_file_from_s3(slide.s3_path)

    print(f"Analyzing image: {image_uri}")
    base64_image = encode_image(image_uri)
    model = ChatOpenAI(
        model="gpt-4-turbo",
        openai_api_key=config("OPENAI_API_KEY"),
        model_kwargs={
            "extra_headers": {
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                "Helicone-Property-UUID": slide.deck.uuid

            }
        },
        openai_api_base="https://oai.hconeai.com/v1",
    )
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
def processing_callback(results, deck_id, start_time):
    deck = PitchDeck.objects.get(id=deck_id)
    print(f"Processing callback for deck: {deck.name}")
    print(f'Start_time: {start_time}')
    # print("All slides analyzed, cleaning data")
    # cleaned_data = clean_data(raw_slides)
    combined = "\n".join([f"Page: {slide.order}\n{slide.content}" for slide in deck.slides.all()])
    print("Data ingested. Starting analysis")
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
    analyze_deck_task.delay(analysis.id)


@app.task(name="prelo.tasks.process_deck")
def process_deck(deck_id):
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
    callback = signature('processing_callback', args=(), kwargs={'deck_id': deck.id, "start_time": start_time})

    # Executes all tasks in the group in parallel
    result_chord = task_chord(callback)



@app.task(name="prelo.tasks.send_message_to_submind")
def send_message_to_submind(submind_id, message):

    pass