import json

import stripe
from decouple import config
from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def create_checkout_session(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    price_id = body['price_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        return Response({'error': 'Client account not found'})

    domain = 'http://localhost:3000/checkout'
    stripe.api_key = config('STRIPE_SECRET_KEY')
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            },
        ],
        mode='subscription',
        success_url=domain + '/success/',
        cancel_url=domain + '/cancel/',
    )
    print(checkout_session)
    return Response({"checkout_session_id": checkout_session.id, "checkout_url": checkout_session.url})