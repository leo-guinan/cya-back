import json
from datetime import datetime, timedelta

import pytz
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from twitter.models import TwitterAccount
from twitter.serializers import TwitterAccountSerializer
from twitter_api.twitter_api import TwitterAPI
# Create your views here.
from .models import Analysis
from .tasks import lookup_twitter_user, report_to_account

utc = pytz.UTC


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
    twitter_api = TwitterAPI()
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id_to_lookup).first()
    if not twitter_account:
        twitter_account_looked_up = twitter_api.lookup_user_as_admin(twitter_id_to_lookup)
        twitter_account.twitter_id = twitter_account_looked_up.id
        twitter_account.twitter_bio = twitter_account_looked_up.description
        twitter_account.twitter_name = twitter_account_looked_up.name
        twitter_account.twitter_username = twitter_account_looked_up.username
        twitter_account.twitter_profile_picture_url = twitter_account_looked_up.profile_image_url
        twitter_account.save()
    analysis = Analysis.objects.filter(account=twitter_account).first()
    if not analysis:
        analysis = Analysis()
        analysis.account = twitter_account
        analysis.save()
    lookup_twitter_user.delay(token, twitter_id_to_lookup)
    return Response({"status": "success"})


@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def analyze_self(request):
    report_to_account.delay("1325102346792218629")
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
    for relationship in current_user.follows.all():
        if relationship and relationship.last_tweet_date:
            if relationship.last_tweet_date < date_to_compare_against:
                serializer = TwitterAccountSerializer(relationship)
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
    return Response({"count": current_user.follows.count()})


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
    for relationship in current_user.follows.all():
        if relationship and relationship.last_tweet_date:
            if relationship.last_tweet_date < date_to_compare_against:
                serializer = TwitterAccountSerializer(relationship)
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
