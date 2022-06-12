from django.contrib import admin

# Register your models here.
from unfollow.models import TwitterAccount, FollowingRelationship, Group


class TwitterAccountAdmin(admin.ModelAdmin):
    pass
admin.site.register(TwitterAccount, TwitterAccountAdmin)

class FollowingRelationshipAdmin(admin.ModelAdmin):
    pass
admin.site.register(FollowingRelationship, FollowingRelationshipAdmin)

class GroupAdmin(admin.ModelAdmin):
    pass
admin.site.register(Group, GroupAdmin)