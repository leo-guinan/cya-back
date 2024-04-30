import json
import uuid

from decouple import config
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from prelo.aws.s3_utils import create_presigned_url
from prelo.models import PitchDeck
from submind.models import Goal, SubmindClient
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

    return Response({'scores': score_object})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_founder_chat_message(request):
    body = json.loads(request.body)
    conversation_uuid = body["uuid"]
    message = body["message"]
    client = SubmindClient.objects.filter(uuid=conversation_uuid).first()
    if not client:
        client = SubmindClient.objects.create(uuid=conversation_uuid, name="Score my deck client", database_name=config("SCORE_MY_DECK_DATABASE_NAME"), collection_name=config("SCORE_MY_DECK_COLLECTION_NAME"), session_suffix="_chat")
    combined_message = f"Respond to this message: {message} about the pitch deck with UUID {conversation_uuid}"
    goal = Goal.objects.create(content=combined_message, submind_id=config("PRELO_SUBMIND_ID"), fast=True, client=client,
                               uuid=str(uuid.uuid4()))

    think.delay(goal.id)

    return Response({'request_id': goal.id})