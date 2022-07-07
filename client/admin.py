from django.contrib import admin

# Register your models here.
from client.models import Client, ClientAccount


class ClientAdmin(admin.ModelAdmin):
    pass


admin.site.register(Client, ClientAdmin)


class ClientAccountAdmin(admin.ModelAdmin):
    pass


admin.site.register(ClientAccount, ClientAccountAdmin)
