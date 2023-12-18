from django.urls import path, re_path

from cofounder.views import add_user, list_chats, get_chat, get_preferences, set_preferences, \
    get_profile, set_profile, start_chat, teach_cofounder

urlpatterns = [
    path('add_user/', add_user),
    path('chats/', list_chats),
    path('chat/', get_chat),
    path('start_chat/', start_chat),
    re_path('preferences/(?P<user_id>.+)/$', get_preferences),
    path('preferences/', set_preferences),
    path('set_profile/', set_profile),
    path('get_profile/', get_profile),
    path('teach/', teach_cofounder)
]
