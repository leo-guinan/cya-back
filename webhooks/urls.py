from django.urls import path

from webhooks.views import twitter_webhook, list_twitter_webhook_environments, register_twitter_webhook, \
    delete_twitter_webhook, subscribe_twitter_webhook, email_received, content_received, process_twitter_user, stripe

urlpatterns = [
    path('twitter/', twitter_webhook),
    path('twitter/list', list_twitter_webhook_environments),
    path('twitter/delete', delete_twitter_webhook),
    path('twitter/register', register_twitter_webhook),
    path('twitter/subscribe', subscribe_twitter_webhook),
    path('podcast/transcript', email_received),
    path('content/save', content_received),
    path('experimentation/twitter_user', process_twitter_user),
    path('stripe', stripe),
]
