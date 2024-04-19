from django.urls import path, re_path

from prelo.views import ask, details

urlpatterns = [
    path('ask/', ask),
    path('details/', details),

]