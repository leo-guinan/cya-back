from django.urls import path, re_path

from toolkit.views import video_to_blog, idea_collider, blog_result, collider_result, sync_google_docs

urlpatterns = [
    path('blog/', video_to_blog),
    path('collider/', idea_collider),
    path('googledocs/', sync_google_docs),
    re_path('^blog/(?P<result_uuid>\w+)/$', blog_result),
    re_path('^collider/(?P<result_uuid>\w+)/$', collider_result),
]