from django.db import models


# Create your models here.

class WatchTweet(models.Model):
    tweet_id = models.CharField("Tweet ID", max_length=512)
    action = models.CharField("Action To Take", max_length=512)
    cadence = models.CharField("Cadence of checking", max_length=512)
    prompt = models.ForeignKey("watchtweet.PromptQuestion", related_name="prompted_tweets", on_delete=models.CASCADE,
                               null=True, blank=True)
    children = models.ManyToManyField("self", symmetrical=False, related_name='parent',
                                      blank=True)


class ReplyToTweet(models.Model):
    respondent_twitter_id = models.CharField("Twitter ID of respondent", max_length=512)
    tweet_responded_to = models.ForeignKey('watchtweet.WatchTweet', related_name="respondents",
                                           on_delete=models.SET_NULL, null=True)
    response_id = models.CharField("Tweet ID of response", max_length=512)
    responded = models.BooleanField("Have we responded to this response", default=False)
    message = models.CharField('text of response', max_length=1024)


class PromptQuestion(models.Model):
    question = models.CharField("Question to ask users", max_length=280)


class PromptResponse(models.Model):
    response = models.BooleanField("did the user respond yes to prompt", default=False)
    twitter_id = models.CharField("twitter Id of respondant", max_length=512)
    responded_to = models.ForeignKey('watchtweet.WatchTweet', related_name='responses', on_delete=models.CASCADE)


class Action(models.Model):
    name = models.CharField("name of action", max_length=255)


class TweetToWatch(models.Model):
    tweet = models.ForeignKey("twitter.Tweet", related_name='watches', on_delete=models.CASCADE)
    action_to_take = models.ForeignKey("watchtweet.Action", related_name="tweets_to_act_on", on_delete=models.CASCADE, null=True)
    requested_by = models.ForeignKey("twitter.TwitterAccount", related_name="watches_requested",
                                     on_delete=models.CASCADE, null=True)


class WatchResponse(models.Model):
    watched_tweet = models.ForeignKey("watchtweet.TweetToWatch", related_name="responses_to_tweet",
                                      on_delete=models.CASCADE)
    response = models.ForeignKey("twitter.Tweet", related_name='watch_responses', on_delete=models.CASCADE)
    action_taken = models.BooleanField("was the action taken?", default=False)
    ignored = models.BooleanField("should this response be ignored?", default=False)


class AccountThatRespondedToWatchedTweet(models.Model):
    watched_tweet = models.ForeignKey("watchtweet.TweetToWatch", related_name="accounts_that_responded",
                                      on_delete=models.CASCADE)
    account = models.ForeignKey("twitter.TwitterAccount", related_name="responded_to_watches", on_delete=models.CASCADE)


class AccountsToIgnore(models.Model):
    account = models.ForeignKey("twitter.TwitterAccount", related_name="ignored_for", on_delete=models.CASCADE)
    reason = models.CharField("the reason this account is ignored", max_length=255)
