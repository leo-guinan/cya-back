from django.urls import path, re_path

from submind.views import send_message

urlpatterns = [
    re_path('^chat/(?P<submind_id>\d+)/send/$', send_message),

]
