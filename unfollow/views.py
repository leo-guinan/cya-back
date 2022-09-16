import json
from datetime import datetime, timedelta

import pytz
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClientAccount
from client.models import ClientAccount
from twitter.models import TwitterAccount, Group, Relationship
from twitter.serializers import TwitterAccountSerializer
from twitter.service import unfollow_account
from twitter.tasks import unfollow_user_for_client_account
from twitter_api.twitter_api import TwitterAPI
# Create your views here.
from .models import UnfollowRequest, AccountCheck
from .tasks import lookup_twitter_user, unfollow_accounts_needing

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
def get_account_analysis(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    current_user = client_account.twitter_account
    following = Relationship.objects.filter(this_account=current_user).all()
    follower_count = len(following)
    dormant_count = 0
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    for relationship in following:
        if relationship and relationship.follows_this_account.last_tweet_date:
            if relationship.follows_this_account.last_tweet_date < date_to_compare_against:
                dormant_count += 1
    followers_to_analyze = client_account.accounts_to_analyze.filter(status__in=[AccountCheck.CheckStatus.REQUESTED, AccountCheck.CheckStatus.IN_PROGRESS]).count()
    result = {
        "following_count": follower_count,
        "dormant_count": dormant_count,
        "followers_to_analyze": followers_to_analyze
    }
    return Response(result)

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_number_of_accounts_left_to_analyze(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    followers_to_analyze = client_account.accounts_to_analyze.filter(last_analyzed__isnull=True).count()
    result = {
        "followers_to_analyze": followers_to_analyze
    }
    return Response(result)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_followers_whose_last_tweet_was_more_than_3_months_ago(request):
    body = json.loads(request.body)
    twitter_id_to_check = body['twitter_id']
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    results = []
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    for relationship in Relationship.objects.filter(this_account=current_user).all():
        if relationship and relationship.follows_this_account.last_tweet_date:
            if relationship.follows_this_account.last_tweet_date < date_to_compare_against:
                serializer = TwitterAccountSerializer(relationship.follows_this_account)
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
    return Response({"count": current_user.following.count()})


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
def unfollow_user(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    twitter_id_to_unfollow = body['twitter_id']
    print(f"Unfollowing {twitter_id_to_unfollow}")
    unfollow_account(client_account_id, twitter_id_to_unfollow)
    current_user = TwitterAccount.objects.filter(twitter_id=client_account.twitter_account.twitter_id).first()
    user_to_unfollow = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    relationship = Relationship.objects.filter(this_account=current_user, follows_this_account=user_to_unfollow).first()
    if relationship:
        relationship.delete()
    return Response({"success": True})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def bulk_unfollow_users(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    twitter_ids_to_unfollow = body['twitter_ids']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    for twitter_id in twitter_ids_to_unfollow:
        acct_to_unfollow = TwitterAccount.objects.get(twitter_id=twitter_id)
        existing_request = UnfollowRequest.objects.filter(requesting_account=client_account,account_to_unfollow=acct_to_unfollow).first()
        if not existing_request:
            request = UnfollowRequest()
            request.requesting_account = client_account
            request.account_to_unfollow = acct_to_unfollow
            request.save()
    unfollow_accounts_needing.delay()
    return Response({"success": True})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def protect_user(request):
    body = json.loads(request.body)
    logged_in_user_twitter_id = body['logged_in_user_id']
    twitter_id_to_unfollow = body['twitter_id']
    print(f"Protecting {twitter_id_to_unfollow}")
    current_user = TwitterAccount.objects.filter(twitter_id=logged_in_user_twitter_id).first()
    user_to_protect = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    # if group doesn't exist for protected, create one
    protected_group = Group.objects.filter(owner=current_user, name="Protected").first()
    if not protected_group:
        protected_group = Group(name="Protected", owner=current_user)
        protected_group.save()
        protected_group.members.add(user_to_protect)
    else:
        protected_group.members.add(user_to_protect)
    protected_group.save()
    serializer = TwitterAccountSerializer(user_to_protect)

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

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def bulk_request_status(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    unfollow_request_count = UnfollowRequest.objects.filter(requesting_account_id=client_account_id ,unfollowed__isnull=True).count()
    return Response({"left_to_unfollow": unfollow_request_count})

