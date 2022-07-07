from django.db import models


# Create your models here.
class Tweet(models.Model):
    tweet_id = models.CharField("Tweet ID", max_length=512, unique=True)
    tweet_created_at = models.DateTimeField("Datetime that tweet was created")
    message = models.CharField("Content of the Tweet", max_length=512)
    author = models.ForeignKey("twitter.TwitterAccount", on_delete=models.CASCADE)
    in_response_to = models.ManyToManyField("self", symmetrical=False, related_name="responses")


class TwitterAccount(models.Model):
    twitter_id = models.CharField("the twitter id of the user", max_length=512, unique=True)
    twitter_username = models.CharField("the username of the user", max_length=512, null=True, blank=True)
    twitter_name = models.CharField("the name of the user", max_length=512, null=True, blank=True)
    twitter_bio = models.CharField("the bio of the user", max_length=1024, null=True, blank=True)
    twitter_profile_picture_url = models.CharField("the url of the user's profile picture", max_length=1024, null=True,
                                                   blank=True)
    most_recent_tweet = models.ForeignKey("twitter.Tweet", on_delete=models.SET_NULL, null=True, blank=True)
    follows = models.ManyToManyField("self", symmetrical=False, related_name="followed_by")
    last_tweet_date = models.DateTimeField("date of last tweet", null=True)


class Group(models.Model):
    name = models.CharField("Group Name", max_length=255, null=False)
    members = models.ManyToManyField("twitter.TwitterAccount", related_name="member_of")
    owner = models.ForeignKey("twitter.TwitterAccount", related_name="groups", on_delete=models.CASCADE)


class Like(models.Model):
    tweet = models.ForeignKey("twitter.Tweet", on_delete=models.CASCADE, null=True, blank=True, related_name="likes")
    liking_account = models.ForeignKey("twitter.TwitterAccount", on_delete=models.CASCADE, null=True, blank=True,
                                       related_name="liked_tweets")


class Retweet(models.Model):
    tweet = models.ForeignKey("twitter.Tweet", on_delete=models.CASCADE, null=True, blank=True, related_name="retweets")
    retweeting_account = models.ForeignKey("twitter.TwitterAccount", on_delete=models.CASCADE, null=True, blank=True,
                                           related_name="retweeted_tweets")


class TweetCollection(models.Model):
    tweets = models.ManyToManyField("twitter.Tweet", related_name="collections")
    name = models.CharField("the name of the collection", max_length=512)
