from django.contrib import admin

# Register your models here.
from watchtweet.models import WatchTweet, ReplyToTweet, PromptQuestion, PromptResponse, Action, TweetToWatch, \
    WatchResponse, AccountThatRespondedToWatchedTweet, AccountsToIgnore


class WatchTweetAdmin(admin.ModelAdmin):
    pass


admin.site.register(WatchTweet, WatchTweetAdmin)


class ReplyToTweetAdmin(admin.ModelAdmin):
    pass


admin.site.register(ReplyToTweet, ReplyToTweetAdmin)


class PromptQuestionAdmin(admin.ModelAdmin):
    pass


admin.site.register(PromptQuestion, PromptQuestionAdmin)


class PromptResponseAdmin(admin.ModelAdmin):
    pass


admin.site.register(PromptResponse, PromptResponseAdmin)


class ActionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Action, ActionAdmin)


class TweetToWatchAdmin(admin.ModelAdmin):
    pass


admin.site.register(TweetToWatch, TweetToWatchAdmin)


class WatchResponseAdmin(admin.ModelAdmin):
    pass


admin.site.register(WatchResponse, WatchResponseAdmin)


class AccountThatRespondedToWatchedTweetAdmin(admin.ModelAdmin):
    pass


admin.site.register(AccountThatRespondedToWatchedTweet, AccountThatRespondedToWatchedTweetAdmin)


class AccountsToIgnoreAdmin(admin.ModelAdmin):
    pass


admin.site.register(AccountsToIgnore, AccountsToIgnoreAdmin)
