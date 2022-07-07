from django.contrib import admin

# Register your models here.
from twitter.models import Tweet, TwitterAccount, Like, Retweet, TweetCollection, Group


class TweetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Tweet, TweetAdmin)


class TwitterAccountAdmin(admin.ModelAdmin):
    pass


admin.site.register(TwitterAccount, TwitterAccountAdmin)


class LikeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Like, LikeAdmin)


class RetweetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Retweet, RetweetAdmin)


class TweetCollectionAdmin(admin.ModelAdmin):
    pass


admin.site.register(TweetCollection, TweetCollectionAdmin)


class GroupAdmin(admin.ModelAdmin):
    pass


admin.site.register(Group, GroupAdmin)
