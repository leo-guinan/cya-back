import json
import time
import uuid
from datetime import datetime, date

from decouple import config
from django.views.decorators.csrf import csrf_exempt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from prelo.aws.s3_utils import create_presigned_url
from prelo.models import PitchDeck
from prelo.prompts.prompts import CHAT_WITH_DECK_SYSTEM_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Goal, SubmindClient, Submind
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride
from submind.tasks import think
from prelo.tasks import check_for_decks

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
    object_name = f'pitch_decks/{filename}'
    bucket_name = config('PRELO_AWS_BUCKET')
    # Generate a PUT URL for uploads
    url = create_presigned_url(bucket_name, object_name)
    pitch_deck = PitchDeck.objects.create(s3_path=object_name, name=filename, uuid=uuid_for_document)
    return Response({'upload_url': url, 'pitch_deck_id': pitch_deck.id})


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_scores(request):
    pitch_deck_id = request.query_params.get('pitch_deck_id')
    pitch_deck = PitchDeck.objects.get(id=pitch_deck_id)
    try:
        scores = pitch_deck.company.scores.first()
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
    except Exception as e:
        print(e)
        score_object = {

        }

    try:
        name = pitch_deck.company.name
    except Exception as e:
        name = ""

    return Response({'scores': score_object, 'name': name})

def get_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("SCORE_MY_DECK_DATABASE_NAME"),
        collection_name=config("SCORE_MY_DECK_COLLECTION_NAME")
    )

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_founder_chat_message(request):
    body = json.loads(request.body)
    conversation_uuid = body["uuid"]
    message = body["message"]
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(submind.uuid, "chat")
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?
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
        },
        config={"configurable": {"session_id": submind.uuid}},

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

    deck = PitchDeck.objects.get(id=deck_id)
    return Response({'name': deck.name})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def check_decks(request):
    check_for_decks.delay()
    return Response({'status': 'Successful'})
