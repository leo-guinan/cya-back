from django.urls import path, re_path

from prelo.views import ask, details, check_for_answer, create_client

urlpatterns = [
    path('ask/', ask),
    path('details/', details),
    path('check/', check_for_answer),
    path('create_client/', create_client),

]