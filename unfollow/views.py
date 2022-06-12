from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_api_key.permissions import HasAPIKey

import json
from datetime import datetime, timedelta
from twitter_api.twitter_api import TwitterAPI
# Create your views here.
from .models import TwitterAccount, FollowingRelationship, Group
from .serializers import TwitterAccountSerializer
from .tasks import lookup_twitter_user
import pytz

utc=pytz.UTC

# Create your views here.
class TwitterAccountList(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = TwitterAccount.objects.all()
    serializer_class = TwitterAccountSerializer


class TwitterAccountDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = TwitterAccount.objects.all()
    serializer_class = TwitterAccountSerializer
def sortKeyFunctionLastTweetDate(e):
  return e['last_tweet_date']

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def lookup_user(request):
    body = json.loads(request.body)
    token = body['token']
    twitter_id_to_lookup = body['twitter_id']
    lookup_twitter_user.delay(token, twitter_id_to_lookup)
    return Response({"status": "success"})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_followers_whose_last_tweet_was_more_than_3_months_ago(request):
    body = json.loads(request.body)
    twitter_id_to_check = body['twitter_id']
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    results = []
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    relationships = FollowingRelationship.objects.filter(twitter_user=current_user).all()
    for relationship in relationships:
        user_to_check = TwitterAccount.objects.filter(twitter_id=relationship.follows.twitter_id).first()
        if user_to_check and user_to_check.last_tweet_date:
            if user_to_check.last_tweet_date < date_to_compare_against:
                serializer = TwitterAccountSerializer(user_to_check)
                results.append(serializer.data)
    results.sort(key=sortKeyFunctionLastTweetDate)
    return Response(results)

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_number_of_followers_processed(request):
    body = json.loads(request.body)
    twitter_id_to_check = body['twitter_id']
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    relationship_count = FollowingRelationship.objects.filter(twitter_user=current_user).count()
    return Response({"count": relationship_count})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_number_of_followers(request):
    body = json.loads(request.body)
    twitter_id_to_check = body['twitter_id']
    twitter_api = TwitterAPI()
    count = twitter_api.get_number_of_accounts_followed_by_account(twitter_id_to_check)
    return Response({"count": count})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_number_of_followers_whose_last_tweet_was_more_than_3_months_ago(request):
    body = json.loads(request.body)
    twitter_id_to_check = body['twitter_id']
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    results = []
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    relationships = FollowingRelationship.objects.filter(twitter_user=current_user).all()
    for relationship in relationships:
        user_to_check = TwitterAccount.objects.filter(twitter_id=relationship.follows.twitter_id).first()
        if user_to_check and user_to_check.last_tweet_date:
            if user_to_check.last_tweet_date < date_to_compare_against:
                serializer = TwitterAccountSerializer(user_to_check)
                results.append(serializer.data)

    return Response({"count": len(results)})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def unfollow_user(request):
    body = json.loads(request.body)
    token = body['token']
    logged_in_user_twitter_id = body['logged_in_user_id']
    twitter_id_to_unfollow = body['twitter_id']
    twitter_api = TwitterAPI()
    print(f"Unfollowing {twitter_id_to_unfollow}")
    twitter_api.unfollow_user(twitter_id_to_unfollow, token)
    currentUser = TwitterAccount.objects.filter(twitter_id=logged_in_user_twitter_id).first()
    userToUnfollow = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    FollowingRelationship.objects.filter(twitter_user=currentUser, follows=userToUnfollow).delete()
    return Response({"success": True})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def protect_user(request):
    body = json.loads(request.body)
    logged_in_user_twitter_id = body['logged_in_user_id']
    twitter_id_to_unfollow = body['twitter_id']
    print(f"Protecting {twitter_id_to_unfollow}")
    currentUser = TwitterAccount.objects.filter(twitter_id=logged_in_user_twitter_id).first()
    userToProtect = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    # if group doesn't exist for protected, create one
    protected_group = Group.objects.filter(owned_by=currentUser, name="Protected").first()
    if not protected_group:
        protected_group = Group(name="Protected")
        protected_group.save()
        protected_group.members.add(userToProtect)
        currentUser.groups.add(protected_group)
    else:
        protected_group.members.add(userToProtect)
    protected_group.save()
    currentUser.save()
    print(protected_group)
    serializer = TwitterAccountSerializer(userToProtect)

    return Response(serializer.data)

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def unprotect_user(request):
    body = json.loads(request.body)
    logged_in_user_twitter_id = body['logged_in_user_id']
    twitter_id_to_unfollow = body['twitter_id']
    print(f"Protecting {twitter_id_to_unfollow}")
    currentUser = TwitterAccount.objects.filter(twitter_id=logged_in_user_twitter_id).first()
    userToUnprotect = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    if userToUnprotect in currentUser.groups.all():
        currentUser.groups.remove(userToUnprotect)
        currentUser.save()
    serializer = TwitterAccountSerializer(userToUnprotect)
    return Response(serializer.data)

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_protected_users(request):
    body = json.loads(request.body)
    logged_in_user_twitter_id = body['logged_in_user_id']
    currentUser = TwitterAccount.objects.filter(twitter_id=logged_in_user_twitter_id).first()
    protected_users = []
    for group in currentUser.groups.all():
        for member in group.members.all():
            serializer = TwitterAccountSerializer(member)
            protected_users.append(serializer.data)
    return Response(protected_users)
