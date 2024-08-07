import json
import time
import uuid

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import permission_classes, renderer_classes, api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from prelo.aws.s3_utils import create_presigned_url, upload_uploaded_file_to_s3
from prelo.chat.history import get_message_history, get_prelo_message_history
from prelo.events import record_prelo_event, record_smd_event
from prelo.models import PitchDeck, Company, DeckReport, ConversationDeckUpload, InvestorReport, RejectionEmail, \
    Investor, MeetingEmail, RequestInfoEmail, InviteCoinvestorEmail
from prelo.pitch_deck.generate import create_report_for_deck
from prelo.pitch_deck.investor.deck_select import identify_pitch_deck_to_use
from prelo.pitch_deck.investor.meeting import write_meeting_email
from prelo.pitch_deck.investor.more_info import request_more_info
from prelo.pitch_deck.investor.rejection import write_rejection_email
from prelo.prompts.functions import functions
from prelo.prompts.prompts import CHAT_WITH_DECK_SYSTEM_PROMPT, CHOOSE_PATH_PROMPT, \
    INTERVIEW_SYSTEM_PROMPT_WITH_CUSTOMIZATION, INTERVIEW_SYSTEM_PROMPT_PLAIN
from prelo.tasks import check_for_decks
from prelo.tools.company import lookup_investors
from prelo.tools.emails import write_cold_outreach_message, write_forwardable_message
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Goal, SubmindClient, Submind
from submind.tasks import think


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def ask(request):
    body = json.loads(request.body)
    question = body["question"]
    fast_mode = body.get("fast_mode", False)
    client_id = body["prelo_client_id"]
    submind_id = config("PRELO_SUBMIND_ID")
    print(f"Client Id: {client_id}")
    goal = Goal.objects.create(content=question, submind_id=submind_id, fast=fast_mode, client_id=client_id,
                               uuid=str(uuid.uuid4()))

    think.delay(goal.id)

    return Response({'request_id': goal.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def check_for_answer(request):
    body = json.loads(request.body)
    goal_id = body["request_id"]
    goal = Goal.objects.get(id=goal_id)
    if goal.completed and goal.results:
        return Response({'answer': goal.results})
    else:
        return Response({'message': 'Still thinking...'})


@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def details(request):
    body = json.loads(request.body)
    print(body)
    return Response({'message': 'Hello, World!'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def create_client(request):
    body = json.loads(request.body)
    uuid_for_client = body["uuid"]

    new_client = SubmindClient.objects.create(uuid=uuid_for_client, name="Prelo Client")

    return Response({'client_id': new_client.id})


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_upload_url(request):
    # get filename from request parameters
    filename = request.query_params.get('filename')
    uuid_for_document = request.query_params.get('uuid')
    client = request.query_params.get('client', '')
    deck_version = request.query_params.get('deck_version', '')
    user_id = request.query_params.get('user_id', '')
    investor_id = request.query_params.get('investor_id', '')
    firm_id = request.query_params.get('firm_id', '')
    if user_id:
        company = Company.objects.filter(user_id=user_id).first()
        if not company:
            print("Company doesn't exist yet, creating one.")
            company = Company.objects.create(user_id=user_id, deck_uuid=uuid_for_document)
    if client and firm_id and investor_id and user_id and deck_version:
        object_name = f'pitch_decks/{client}/{firm_id}/{investor_id}/{deck_version}/{filename}'
    elif client and user_id and deck_version:
        object_name = f'pitch_decks/{client}/{user_id}/{deck_version}/{filename}'
    else:
        object_name = f'pitch_decks/default/1/{filename}'

    bucket_name = config('PRELO_AWS_BUCKET')
    # Generate a PUT URL for uploads
    url = create_presigned_url(bucket_name, object_name)
    pitch_deck = PitchDeck.objects.create(s3_path=object_name, name=filename, uuid=uuid_for_document, user_id=user_id,
                                          version=deck_version)
    return Response({'upload_url': url, 'pitch_deck_id': pitch_deck.id})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def download_deck_report(request):
    body = json.loads(request.body)
    deck_id = body["pitch_deck_id"]
    deck = PitchDeck.objects.filter(id=deck_id).first()
    try:
        if deck.report:
            report = deck.report.s3_path
        else:
            download_path = create_report_for_deck(deck)
            DeckReport.objects.create(deck=deck, s3_path=download_path)
            report = download_path

    except Exception as e:
        # assume report doesn't exist, so create one.
        print(e)
        download_path = create_report_for_deck(deck)
        DeckReport.objects.create(deck=deck, s3_path=download_path)
        report = download_path

    bucket_name = config('PRELO_AWS_BUCKET')
    # Generate a PUT URL for uploads
    url = create_presigned_url(bucket_name, report, method='GET')

    return Response({'download_url': url})


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_scores(request):
    print("getting scores")
    pitch_deck_id = request.query_params.get('pitch_deck_id')
    pitch_deck = PitchDeck.objects.get(id=pitch_deck_id)
    previous_deck = PitchDeck.objects.filter(user_id=pitch_deck.user_id, version=pitch_deck.version - 1).first()
    try:
        scores = pitch_deck.scores
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning,
                'delta': scores.market_opportunity - previous_deck.scores.market_opportunity if previous_deck else 0
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning,
                'delta': scores.team - previous_deck.scores.team if previous_deck else 0
            },
            'product': {
                'score': scores.product,
                'reason': scores.product_reasoning,
                'delta': scores.product - previous_deck.scores.product if previous_deck else 0
            },
            'traction': {
                'score': scores.traction,
                'reason': scores.traction_reasoning,
                'delta': scores.traction - previous_deck.scores.traction if previous_deck else 0

            },
            'final': {
                'score': scores.final_score,
                'reason': scores.final_reasoning,
                'delta': scores.final_score - previous_deck.scores.final_score if previous_deck else 0
            }
        }
    except Exception as e:
        print(e)
        score_object = {

        }

    try:
        name = pitch_deck.company.name
    except Exception as e:
        name = ""

    return Response({'scores': score_object, 'name': name})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_founder_chat_message(request):
    body = json.loads(request.body)
    conversation_uuid = body["uuid"]
    message = body["message"]
    credits = body.get("credits", 0)
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(conversation_uuid, "chat", 0.0)
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?

    choose_path_prompt = ChatPromptTemplate.from_template(CHOOSE_PATH_PROMPT)

    path = choose_path_prompt | model.bind(function_call={"name": "choose_path"},
                                           functions=functions) | JsonOutputFunctionsParser()

    tools_available = """
    Id: 1, Name: Investor Lookup, Description: Find investors
    Id: 2, Name: Write Cold Outreach, Description: Write a cold outreach email
    Id: 3, Name: Write Forwardable Introduction email, Description: Write an introductory email someone can forward to an investor
    """

    path_response = path.invoke({
        "message": message,
        "tools": tools_available
    })

    chat_history = get_message_history(conversation_uuid)
    headers = {
        "Content-Type": "application/json",
        "Authorization": config('TELEMETRY_API_KEY')
    }
    if path_response['use_tool']:
        if path_response['tool_id'] == '1':
            if credits < 2:
                return Response({"message": "Not enough credits remaining. Please add credits to continue.", "credits_used": 0})
            response = lookup_investors(message)
            chat_history.add_user_message(message)

            chat_history.add_ai_message(response)
            end_time = time.perf_counter()
            print(f"Chat with lookup took {end_time - start_time} seconds")

            record_smd_event({
                "event": "chat_message",
                "type": "investor_lookup",
                "conversation": conversation_uuid,
                "duration": end_time - start_time,
                "credits_used": 2
            })
            return Response({"message": response, "credits_used": 2})
        elif path_response['tool_id'] == '2':
            if credits < 5:
                return Response({"message": "Not enough credits remaining. Please add credits to continue.", "credits_used": 0})
            response = write_cold_outreach_message(message, conversation_uuid, submind)
            end_time = time.perf_counter()
            print(f"Chat with cold email writing took {end_time - start_time} seconds")
            record_smd_event({
                "event": "chat_message",
                "type": "cold_outreach",
                "conversation": conversation_uuid,
                "duration": end_time - start_time,
                "credits_used": 5
            })


            return Response({"message": response, "credits_used": 5})
        elif path_response['tool_id'] == '3':
            if credits < 5:
                return Response({"message": "Not enough credits remaining. Please add credits to continue.", "credits_used": 0})
            response = write_forwardable_message(message, conversation_uuid, submind)
            end_time = time.perf_counter()
            print(f"Chat with forwardable email writing took {end_time - start_time} seconds")
            record_smd_event({
                "event": "chat_message",
                "type": "forwardable_email",
                "conversation": conversation_uuid,
                "duration": end_time - start_time,
                "credits_used": 5
            })

            return Response({"message": response, "credits_used": 5})
    if credits < 1:
        return Response({"message": "Not enough credits remaining. Please add credits to continue.", "credits_used": 0})
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                CHAT_WITH_DECK_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model

    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    pitch_deck = PitchDeck.objects.filter(uuid=conversation_uuid).first()
    submind_document = remember(submind)
    answer = with_message_history.invoke(
        {
            "input": message,
            "mind": submind_document,
            "deck": pitch_deck.analysis.compiled_slides,
            "analysis": pitch_deck.analysis.extra_analysis,
            "top_concern": pitch_deck.analysis.top_concern,
            "objections": pitch_deck.analysis.objections,
            "derisking": pitch_deck.analysis.how_to_overcome
        },
        config={"configurable": {"session_id": conversation_uuid}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    record_smd_event({
        "event": "chat_message",
        "type": "chat",
        "conversation": conversation_uuid,
        "duration": end_time - start_time,
    })

    return Response({"message": answer.content, "credits_used": 1})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_investor_chat_message(request):
    body = json.loads(request.body)
    conversation_uuid = body["uuid"]
    message = body["message"]
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(conversation_uuid, "chat", 0.0)
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?

    choose_path_prompt = ChatPromptTemplate.from_template(CHOOSE_PATH_PROMPT)

    path = choose_path_prompt | model.bind(function_call={"name": "choose_path"},
                                           functions=functions) | JsonOutputFunctionsParser()

    tools_available = """
    Id: 1, Name: Investor Lookup, Description: Find investors

    """

    path_response = path.invoke({
        "message": message,
        "tools": tools_available
    })

    print(path_response)

    if path_response['use_tool']:
        if path_response['tool_id'] == '1':
            response = lookup_investors(message)
            get_message_history(conversation_uuid).add_ai_message(response)
            end_time = time.perf_counter()
            print(f"Chat with lookup took {end_time - start_time} seconds")

            return Response({"message": response})

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                CHAT_WITH_DECK_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model

    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    pitch_deck = PitchDeck.objects.filter(uuid=conversation_uuid).first()
    submind_document = remember(submind)
    answer = with_message_history.invoke(
        {
            "input": message,
            "mind": submind_document,
            "deck": pitch_deck.analysis.compiled_slides,
            "analysis": pitch_deck.analysis.extra_analysis,
            "top_concern": pitch_deck.analysis.top_concern,
            "objections": pitch_deck.analysis.objections,
            "derisking": pitch_deck.analysis.how_to_overcome
        },
        config={"configurable": {"session_id": conversation_uuid}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")

    print(answer.content)

    return Response({"message": answer.content})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_deck_name(request):
    body = json.loads(request.body)
    deck_id = body["deck_id"]

    deck = PitchDeck.objects.filter(id=deck_id).first()
    return Response({'name': deck.name if deck else ""})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def check_decks(request):
    check_for_decks.delay()
    return Response({'status': 'Successful'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_deck_report(request):
    try:
        body = json.loads(request.body)
        deck_id = body["deck_id"]
        user_id = body.get("user_id", "")
        company = Company.objects.filter(user_id=user_id).first()
        gtm_strategy = company.go_to_market.first().strategy if company else ""
        deck = PitchDeck.objects.get(id=deck_id)
        analysis = deck.analysis
        return Response({
            'top_concern': analysis.top_concern,
            'objections': analysis.objections,
            'how_to_overcome': analysis.how_to_overcome,
            'pitch_deck_analysis': analysis.concerns,
            'gtm_strategy': gtm_strategy
        })
    except Exception as e:
        print(e)
        return Response({
            'top_concern': "",
            'objections': "",
            'how_to_overcome': "",
            'pitch_deck_analysis': "",
            'gtm_strategy': ""
        })


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_investor_deck_report(request):
    try:
        body = json.loads(request.body)
        deck_uuid = body["deck_uuid"]
        deck = PitchDeck.objects.get(uuid=deck_uuid)
        analysis = deck.analysis
        if analysis.investor_report.investment_potential_score > 70:
            recommendation = "contact"
        elif analysis.investor_report.investment_potential_score > 50:
            recommendation = "maybe"
        else:
            recommendation = "pass"
        company = Company.objects.filter(deck_uuid=deck_uuid).first()
        company_name = company.name
        amount_raising = company.funding_amount
        scores = deck.scores
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning,
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning,
            },
            'product': {
                'score': scores.product,
                'reason': scores.product_reasoning,
            },
            'traction': {
                'score': scores.traction,
                'reason': scores.traction_reasoning,
            },
            'final': {
                'score': analysis.investor_report.investment_potential_score,
                'reason': analysis.investor_report.recommendation_reasons,

            }
        }
        score_explanation = {
            'market': scores.market_reasoning,
            'team': scores.team_reasoning,
            'product': scores.product_reasoning,
            'traction': scores.traction_reasoning,

        }
        founders = analysis.founder_summary
        return Response({
            "concerns": analysis.concerns,
            "believe": analysis.believe,
            "traction": analysis.traction,
            "summary": analysis.summary,
            "executive_summary": analysis.investor_report.executive_summary,
            "recommendation": recommendation,
            "recommendation_reasons": analysis.investor_report.recommendation_reasons,
            "investment_potential_score": analysis.investor_report.investment_potential_score,
            "recommendation_summary": analysis.investor_report.summary,
            "recommended_next_steps": analysis.investor_report.recommended_next_steps,
            "company_name": company_name,
            "amount_raising": amount_raising,
            "scores": score_object,
            "founders": founders,
            "founders_contact_info": analysis.founder_contact_info,
            "score_explanation": score_explanation,
            "report_uuid": analysis.investor_report.uuid


        })
    except Exception as e:
        print(e)
        return Response({
            "concerns": "",
            "believe": "",
            "traction": "",
            "summary": "",
            "recommendation": "",
            "recommendation_reasons": "",
        })

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_investor_deck_status(request):
    try:
        body = json.loads(request.body)
        deck_uuid = body["deck_uuid"]
        deck = PitchDeck.objects.get(uuid=deck_uuid)
        investor_report = deck.analysis.investor_report
        return Response({
            "report_uuid": investor_report.uuid,
            "status": "complete",
            "match_score": investor_report.investment_potential_score
        })
    except Exception as e:
        print(e)
        return Response({
            "status": "processing"
        })

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_shared_report(request):
    body = json.loads(request.body)
    report_uuid = body["report_uuid"]
    deck_uuid = body["deck_uuid"]
    investor_report = InvestorReport.objects.get(uuid=report_uuid)
    company = Company.objects.filter(deck_uuid=deck_uuid).first()
    company_name = company.name
    return Response({
        "company_name": company_name,
        "executive_summary": investor_report.executive_summary,
    })

@api_view(('POST',))
@parser_classes([JSONParser, MultiPartParser])
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_interview_chat_message(request):
    try:
        conversation_uuid = request.data.get('uuid')
        message = request.data.get('message')
        submind_id = request.data.get('submind_id')
        submind = Submind.objects.get(id=submind_id)
        comparison_view = request.data.get('comparison_view', False)
        start_time = time.perf_counter()
        investor_id = request.data.get('investor_id')

        # Access optional file uploads
        optional_file = request.data.get('file', None)
        headers = {
            "Content-Type": "application/json",
            "Authorization": config('TELEMETRY_API_KEY')
        }
        # Add your logic here to handle the optional file if present
        if optional_file:
            client = request.data.get('client')
            firm_id = request.data.get('firm_id')
            object_name = f'pitch_decks/{client}/{firm_id}/{investor_id}/{optional_file.name}'
            upload_uploaded_file_to_s3(object_name, optional_file)
            Company.objects.create(user_id=investor_id, deck_uuid=conversation_uuid)
            print(f'Uploaded to: {object_name}')
            deck_uuid = str(uuid.uuid4())
            pitch_deck = PitchDeck.objects.create(s3_path=object_name, name=optional_file.name, uuid=deck_uuid,
                                                  user_id=investor_id)
            Company.objects.create(user_id=investor_id, deck_uuid=deck_uuid)
            ConversationDeckUpload.objects.create(conversation_uuid=conversation_uuid, deck_uuid=deck_uuid)
            check_for_decks.delay()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(conversation_uuid,
                                                    {"type": "deck.received",
                                                     "deck_uuid": deck_uuid
                                                     })
            history = get_prelo_message_history(f'custom_claude_{conversation_uuid}')
            history.add_user_message(f"Uploaded pitch deck {optional_file.name}")
            history.add_ai_message("Deck has been uploaded and I'm analyzing it now.")
            end_time = time.perf_counter()
            telemetry_response = requests.post(f"{config('TELEMETRY_BASE_URL')}/log",
                                               headers=headers,
                                               json={
                                                   "data": {
                                                       "event": "chat_message",
                                                       "type": "deck_upload",
                                                       "conversation": conversation_uuid,
                                                       "duration": end_time - start_time,
                                                   },
                                                   "table": config('PRELO_TELEMETRY_TABLE')
                                               }
                                               )
            return Response({"message": "Deck has been uploaded and I'm analyzing it now.", "type": "deck_uploaded"})
        # Needs a submind to chat with. How does this look in practice?
        # Should have tools to pull data, knowledge to respond from, with LLM backing.


        choose_path_prompt = ChatPromptTemplate.from_template(CHOOSE_PATH_PROMPT)

        model = SubmindModelFactory.get_model(conversation_uuid, "interview_chat", 0.0)

        path = choose_path_prompt | model.bind(function_call={"name": "choose_path"},
                                               functions=functions) | JsonOutputFunctionsParser()

        tools_available = """
            Id: 1, Name: Write Rejection Email, Description: Write an empathetic rejection email
            Id: 2, Name: Write Meeting Request Email, Description: Write an email requesting a meeting
            Id: 3, Name: Write Request More Info Email, Description: Write an email requesting more information
            Id: 4, Name: Write Invite Coinvestor Email, Description: Write an email inviting a coinvestor to invest
            """

        path_response = path.invoke({
            "message": message,
            "tools": tools_available
        })

        chat_history = get_message_history(f'custom_claude_{conversation_uuid}')
        headers = {
            "Content-Type": "application/json",
            "Authorization": config('TELEMETRY_API_KEY')
        }
        investor = Investor.objects.filter(lookup_id=investor_id).first()

        if path_response['use_tool']:
            # step 1: have to identify the deck to pick.
            deck = identify_pitch_deck_to_use(investor_id, conversation_uuid, message)

            if not deck:
                return Response({"message": "No pitch deck found. Please upload a pitch deck first."})


            if path_response['tool_id'] == '1':
                pitch_deck = PitchDeck.objects.get(uuid=deck.uuid)
                rejection_email = RejectionEmail.objects.filter(deck_uuid=deck.uuid, investor=investor).first()
                if not rejection_email:
                    rejection_email = write_rejection_email(pitch_deck.analysis, investor, submind)

                # return Response({"email": rejection_email.email, "content": rejection_email.content,
                #                  "subject": rejection_email.subject})
                chat_history.add_user_message(message)

                chat_history.add_ai_message(rejection_email.content)
                end_time = time.perf_counter()
                record_prelo_event({
                    "event": "chat_message",
                    "type": "rejection_email",
                    "conversation": conversation_uuid,
                    "duration": end_time - start_time,
                    "deck_uuid": deck.uuid,
                })

                return Response({"message": rejection_email.content})

            elif path_response['tool_id'] == '2':
                pitch_deck = PitchDeck.objects.get(uuid=deck.uuid)
                meeting_email = MeetingEmail.objects.filter(deck_uuid=deck.uuid, investor=investor).first()
                if not meeting_email:
                    meeting_email = write_meeting_email(pitch_deck.analysis, investor, submind)
                # return Response({"email": rejection_email.email, "content": rejection_email.content,
                #                  "subject": rejection_email.subject})
                chat_history.add_user_message(message)

                chat_history.add_ai_message(meeting_email.content)
                end_time = time.perf_counter()
                record_prelo_event({
                    "event": "chat_message",
                    "type": "meeting_email",
                    "conversation": conversation_uuid,
                    "duration": end_time - start_time,
                    "deck_uuid": deck.uuid,
                })

                return Response({"message": meeting_email.content})
            elif path_response['tool_id'] == '3':
                pitch_deck = PitchDeck.objects.get(uuid=deck.uuid)
                request_info_email = RequestInfoEmail.objects.filter(deck_uuid=deck.uuid, investor=investor).first()
                if not request_info_email:
                    request_info_email = request_more_info(pitch_deck.analysis, investor, submind)

                chat_history.add_user_message(message)

                chat_history.add_ai_message(request_info_email.content)
                end_time = time.perf_counter()
                record_prelo_event({
                    "event": "chat_message",
                    "type": "request_info_email",
                    "conversation": conversation_uuid,
                    "duration": end_time - start_time,
                    "deck_uuid": deck.uuid,
                })

                return Response({"message": request_info_email.content})
            elif path_response['tool_id'] == '4':
                pitch_deck = PitchDeck.objects.get(uuid=deck.uuid)
                invite_coinvestor_email = InviteCoinvestorEmail.objects.filter(deck_uuid=deck.uuid, investor=investor).first()
                if not invite_coinvestor_email:
                    invite_coinvestor_email = invite_coinvestor(pitch_deck.analysis, investor, submind)
                chat_history.add_user_message(message)

                chat_history.add_ai_message(invite_coinvestor_email.content)
                end_time = time.perf_counter()
                record_prelo_event({
                    "event": "chat_message",
                    "type": "invite_coinvestor_email",
                    "conversation": conversation_uuid,
                    "duration": end_time - start_time,
                    "deck_uuid": deck.uuid,
                })

                return Response({"message": invite_coinvestor_email.content})



        custom_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    INTERVIEW_SYSTEM_PROMPT_WITH_CUSTOMIZATION
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
        investor_runnable = custom_prompt | model


        investor_message_history = RunnableWithMessageHistory(
            investor_runnable,
            get_prelo_message_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        submind_document = remember(submind)
        investor_answer = investor_message_history.invoke(
            {
                "input": message,
                "mind": submind_document,
            },
            config={"configurable": {"session_id": f'custom_claude_{conversation_uuid}'}},

        )

        end_time = time.perf_counter()
        record_prelo_event({
            "event": "chat_message",
            "type": "investor_chat",
            "conversation": conversation_uuid,
            "duration": end_time - start_time,

        })
        return Response({"message": investor_answer.content})
    except Exception as e:
        conversation_uuid = request.data.get('uuid')
        print(f"Error: {e}")
        record_prelo_event({
            "event": "chat_message",
            "type": "error",
            "conversation": conversation_uuid,
            "error": str(e)
        })
        return Response({"message": "Sorry, an error occurred. Please try again. If the error persists, please contact support."})

@api_view(('POST',))
@parser_classes([JSONParser, MultiPartParser])
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_rejection_email(request):
    body = json.loads(request.body)
    deck_uuid = body["deck_uuid"]
    investor_id = body["investor_id"]
    submind_id = body["submind_id"]
    submind = Submind.objects.get(id=submind_id)
    investor = Investor.objects.filter(lookup_id=investor_id).first()
    pitch_deck = PitchDeck.objects.get(uuid=deck_uuid)
    rejection_email = RejectionEmail.objects.filter(deck_uuid=deck_uuid, investor=investor).first()
    if not rejection_email:
        rejection_email = write_rejection_email(pitch_deck.analysis, investor, submind)

    return Response({"email": rejection_email.email, "content": rejection_email.content, "subject": rejection_email.subject})

@api_view(('POST',))
@parser_classes([JSONParser, MultiPartParser])
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_meeting_email(request):
    body = json.loads(request.body)
    deck_uuid = body["deck_uuid"]
    investor_id = body["investor_id"]
    submind_id = body["submind_id"]
    submind = Submind.objects.get(id=submind_id)
    investor = Investor.objects.filter(lookup_id=investor_id).first()
    pitch_deck = PitchDeck.objects.get(uuid=deck_uuid)
    meeting_email = MeetingEmail.objects.filter(deck_uuid=deck_uuid, investor=investor).first()
    if not meeting_email:
        meeting_email = write_meeting_email(pitch_deck.analysis, investor, submind)

    return Response({"email": meeting_email.email, "content": meeting_email.content, "subject": meeting_email.subject})

@api_view(('POST',))
@parser_classes([JSONParser, MultiPartParser])
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_more_info_email(request):
    body = json.loads(request.body)
    deck_uuid = body["deck_uuid"]
    investor_id = body["investor_id"]
    submind_id = body["submind_id"]
    submind = Submind.objects.get(id=submind_id)
    investor = Investor.objects.filter(lookup_id=investor_id).first()
    pitch_deck = PitchDeck.objects.get(uuid=deck_uuid)
    request_info_email = RequestInfoEmail.objects.filter(deck_uuid=deck_uuid, investor=investor).first()
    if not request_info_email:
        request_info_email = request_more_info(pitch_deck.analysis, investor, submind)

    return Response({"email": request_info_email.email, "content": request_info_email.content, "subject": request_info_email.subject})

@api_view(('POST',))
@parser_classes([JSONParser, MultiPartParser])
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def invite_coinvestor(request):
    body = json.loads(request.body)
    deck_uuid = body["deck_uuid"]
    investor_id = body["investor_id"]
    submind_id = body["submind_id"]
    submind = Submind.objects.get(id=submind_id)
    investor = Investor.objects.filter(lookup_id=investor_id).first()
    pitch_deck = PitchDeck.objects.get(uuid=deck_uuid)
    invite_coinvestor_email = InviteCoinvestorEmail.objects.filter(deck_uuid=deck_uuid, investor=investor).first()
    if not invite_coinvestor_email:
        invite_coinvestor_email = invite_coinvestor(pitch_deck.analysis, investor, submind)
    return Response({"email": invite_coinvestor_email.email, "content": invite_coinvestor_email.content, "subject": invite_coinvestor_email.subject})


