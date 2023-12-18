from django.shortcuts import render
from rest_framework.response import Response


# Create your views here.


def command(request):
    return Response({'message': 'Hello, world!'})