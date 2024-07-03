from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def chat(request):

    return Response({"message": "Hello, world!", "type": "youtube", "url": "https://www.youtube.com/watch?v=K72WHhvgiMM", "context": "Based on your message, you'll like this video because you are struggling with X."})