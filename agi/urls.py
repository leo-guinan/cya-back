from django.urls import path, re_path

from agi.views import salesforce_list_meetings, person, respond, webhook

urlpatterns = [
    path('salesforce/', salesforce_list_meetings),
    path('person/1', person),
    path('person/2', respond),
    path('webhook/<uuid:uuid>', webhook)

]