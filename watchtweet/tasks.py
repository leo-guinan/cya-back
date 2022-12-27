import logging

from backend.celery import app
from twitter_api.twitter_api import TwitterAPI
from watchtweet.models import WatchTweet, PromptQuestion, PromptResponse

logger = logging.getLogger(__name__)

def int_response_id_for_tweet(tweet):
    return tweet.response_id


def find_user_in_list(list_of_users, user_id):
    for i in range(len(list_of_users)):
        if list_of_users[i].id == user_id:
            return list_of_users[i]
    return None


@app.task(name="record_prompt_responses")
def record_prompt_answers(watched_tweet_id):
    watched_tweet = WatchTweet.objects.filter(id=watched_tweet_id).first()
    twitter_api = TwitterAPI()
    tweet_id_to_lookup = watched_tweet.tweet_id
    parent = watched_tweet.parent.first()
    if parent:
        tweet_id_to_lookup = parent.tweet_id
    responses = twitter_api.get_responses_to_prompt_in_conversation(tweet_id=tweet_id_to_lookup)
    logger.debug(responses)
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
