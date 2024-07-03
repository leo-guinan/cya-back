from django.urls import path, re_path

from prelo.views import ask, details, check_for_answer, create_client, get_upload_url, get_scores, \
    send_founder_chat_message, get_deck_name, check_decks, get_deck_report, send_investor_chat_message, \
    get_investor_deck_report, download_deck_report, send_interview_chat_message

urlpatterns = [
    path('ask/', ask),
    path('details/', details),
    path('check/', check_for_answer),
    path('create_client/', create_client),
    path('get_upload_url/', get_upload_url),
    path('get_scores/', get_scores),
    path('get_name/', get_deck_name),
    path('check_decks/', check_decks),
    path('founder/send/', send_founder_chat_message),
    path('investor/send/', send_investor_chat_message),
    path('interview/send/', send_interview_chat_message),
    path('deck/report/', get_deck_report),
    path('deck/report/download/', download_deck_report),
    path('deck/investor/report/', get_investor_deck_report)

]