from backend.celery import app
from twitter.models import TwitterAccount, Tweet
from twitter_api.twitter_api import TwitterAPI
from unfollow.tasks import lookup_twitter_user_as_admin
from watchtweet.models import WatchTweet, ReplyToTweet, PromptQuestion, PromptResponse, TweetToWatch, \
    AccountThatRespondedToWatchedTweet


def int_response_id_for_tweet(tweet):
    return tweet.response_id

def find_user_in_list(list_of_users, user_id):
    for i in range(len(list_of_users)):
        if list_of_users[i].id == user_id:
            return list_of_users[i]
    return None


@app.task(name="analyze_tweet")
def analyze_accounts_that_respond_to_tweet(tweet_id):
    watched_tweet = TweetToWatch.objects.filter(tweet__tweet_id=tweet_id).first()
    twitter_api = TwitterAPI()

    if not watched_tweet:
        watched_tweet = TweetToWatch()
        tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
        if not tweet:
            tweet_lookup = twitter_api.lookup_tweet_as_admin(tweet_id=tweet_id)
            author = TwitterAccount.objects.filter(twitter_id=tweet_lookup.author_id).first()
            if not author:
                author_object = twitter_api.lookup_user_as_admin(twitter_id=tweet_lookup.author_id)
                author = TwitterAccount(twitter_id=author_object.id, twitter_username=author_object.username, twitter_name=author_object.name, twitter_bio=author_object.description)
                author.save()
            tweet = Tweet(tweet_id=tweet_id, tweet_created_at=tweet_lookup.created_at, message=tweet_lookup.text, author=author )
            tweet.save()
        watched_tweet.tweet=tweet
        watched_tweet.save()

    responses = twitter_api.get_responses_to_tweet(tweet_id=tweet_id)
    if not responses:
        return
    for response in responses.data:
        response_author = TwitterAccount.objects.filter(twitter_id=response.author_id).first()
        if not response_author:
            responder = find_user_in_list(responses.includes['users'], response.author_id)
            if not responder:
                raise Exception("User not found in list. something is wrong")
            response_author = TwitterAccount(twitter_id=response.author_id, twitter_username=responder.username, twitter_name=responder.name, twitter_bio=responder.description)
            response_author.save()
        account_responded = AccountThatRespondedToWatchedTweet.objects.filter(watched_tweet=watched_tweet, account=response_author).first()
        if not account_responded:
            task = lookup_twitter_user_as_admin.s(response.author_id)
            account_responded = AccountThatRespondedToWatchedTweet(watched_tweet=watched_tweet, account=response_author)
            account_responded.save()
            task()




@app.task(name="record_prompt_responses")
def record_prompt_answers(watched_tweet_id):
    watched_tweet = WatchTweet.objects.filter(id=watched_tweet_id).first()
    twitter_api = TwitterAPI()
    tweet_id_to_lookup = watched_tweet.tweet_id
    parent = watched_tweet.parent.first()
    if parent:
        tweet_id_to_lookup = parent.tweet_id
    responses = twitter_api.get_responses_to_prompt_in_conversation(tweet_id=tweet_id_to_lookup)
    print(responses)
    if not responses:
        return
    for reply in responses:
        existing_record = PromptResponse.objects.filter(responded_to=watched_tweet, twitter_id=reply.author_id)
        if not existing_record:
            record = PromptResponse()
            record.responded_to = watched_tweet
            record.twitter_id = reply.author_id
            record.response = True if 'yes' in reply.text.lower() else False
            record.save()
            twitter_api.reply_to_tweet(message="Thanks, your response has been recorded!",
                                              tweet_id_to_reply_to=reply.id)


@app.task(name='prompt')
def prompt_twitter_user(tweet_to_respond_to_with_prompt, prompt_question_id, watched_tweet_id):
    twitter_api = TwitterAPI()
    question = PromptQuestion.objects.filter(id=prompt_question_id).first()
    response = twitter_api.reply_to_tweet(message=question.question,
                                          tweet_id_to_reply_to=tweet_to_respond_to_with_prompt)
    watch_for_response = WatchTweet()
    watch_for_response.tweet_id = response['id']
    watch_for_response.action = 'RECORD'
    watch_for_response.cadence = 'HOURLY'
    watch_for_response.save()
    watched_tweet = WatchTweet.objects.filter(id=watched_tweet_id).first()
    watched_tweet.children.add(watch_for_response)
    watched_tweet.save()


@app.task(name='process_hourly_watches')
def hourly_watches():
    analyze_accounts_that_respond_to_tweet.delay("1543941455550578688")
