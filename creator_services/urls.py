from django.urls import path

from creator_services.views import send_demo_message

urlpatterns = [
    path('demo_message/', send_demo_message)
]
