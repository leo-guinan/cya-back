from django.urls import path, re_path

from coach.views import add_user, list_chats, get_chat, start_daily_checkin, get_preferences, set_preferences

urlpatterns = [
    path('add_user/', add_user),
    path('chats/', list_chats),
    path('chat/', get_chat),
    path('start_daily/', start_daily_checkin),
    re_path('preferences/(?P<user_id>.+)/$', get_preferences),
    path('preferences/', set_preferences)
]
