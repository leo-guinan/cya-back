from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework_api_key.permissions import HasAPIKey


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add_subscription(request):
    pass