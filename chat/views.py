import json
import uuid

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey

from chat.enums import SpeakerTypes
from chat.models import ClientApp, Use
from chat.service import respond_to_message
from client.models import Client
from decisions.models import MetaSearchEngine
from search.models import SearchEngine
from crawler.tasks import crawl_website

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
    print(request.headers)
    source = app.sources.filter(url=request.headers['Referer']).first()
    if source is None:
        engine = MetaSearchEngine.objects.get(slug=app.default_slug)
        source = app.sources.create(url=request.headers['Referer'], title=request.headers['Origin'],
                                    metasearch_engine=engine)
    if use_id == -1:

        use = source.uses.create()
        input_message = use.messages.create(content=app.initial_message, speaker=SpeakerTypes.BOT)
        use.messages.add(input_message)

        use.save()
        print(app.initial_message)
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
        response = respond_to_message([], message, source.metasearch_engine.slug)
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
def add_client_app(request):
    body = json.loads(request.body)
    url = body.get('url', None)
    key = request.META["HTTP_AUTHORIZATION"].split()[1]
    api_key = APIKey.objects.get_from_key(key)
    client = Client.objects.filter(api_key=api_key).first()
    if client is None:
        return Response({'message': 'Invalid API Key'}, status=403)
    metasearch_engine = MetaSearchEngine.objects.create(slug=str(uuid.uuid4()), name=body['name'])
    app = ClientApp.objects.create(name=body['name'], api_key=str(uuid.uuid4()), client=client, default_slug=metasearch_engine.slug, metasearch_engine=metasearch_engine)
    if url:
        crawl_website.delay(url, app.id)
    return Response({'api_key': app.api_key})

