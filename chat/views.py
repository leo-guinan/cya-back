import json
import uuid

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from chat.enums import SpeakerTypes
from chat.models import ClientApp, Use
from chat.service import respond_to_message
from search.models import SearchEngine


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def chat(request, client):
    body = json.loads(request.body)
    print(body)
    app = ClientApp.objects.get(api_key=client)
    message = body.get('message', "")
    use_id = body.get('use_id', None)
    source = app.sources.filter(url=request.headers['Referer']).first()
    if source is None:
        engine = SearchEngine.objects.get(slug=app.default_slug)
        source = app.sources.create(url=request.headers['Referer'], title=request.headers['Origin'],
                                    search_engine=engine)
    if use_id == -1:

        use = source.uses.create()
        input_message = use.messages.create(content=app.initial_message, speaker=SpeakerTypes.BOT)
        use.messages.add(input_message)

        use.save()
        return Response({'message': {
            'id': 1,
            'message': app.initial_message,
            'speaker': "bot",

        },
            'use_id': use.id
        })
    else:
        use = Use.objects.get(id=use_id)
        input_message = use.messages.create(content=message, speaker=SpeakerTypes.HUMAN)
        use.messages.add(input_message)
        response = respond_to_message([], message, source.search_engine.slug)
        response_message = use.messages.create(content=response, speaker=SpeakerTypes.BOT)
        use.messages.add(response_message)
        use.save()
        return Response({
            'message': {
                'id': response_message.id,
                'message': response_message.content,
                'speaker': "bot",

            },
            'use_id': use.id
        })


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def add_client(request):
    body = json.loads(request.body)
    app = ClientApp.objects.create(name=body['name'], api_key=str(uuid.uuid4()))
    return Response({'api_key': app.api_key})
