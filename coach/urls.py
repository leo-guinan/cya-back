from django.urls import path

from coach.views import add_user, list_chats, get_chat, start_daily_checkin

urlpatterns = [
    path('add_user/', add_user),
    path('chats/', list_chats),
    path('chat/', get_chat),
    path('start_daily/', start_daily_checkin),
]