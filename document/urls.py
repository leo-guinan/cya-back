from django.urls import path

from document.views import generate_document, get_document

urlpatterns = [
    path('generate/', generate_document),
    path('get/', get_document),

]