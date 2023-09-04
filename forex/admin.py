from django.contrib import admin
from .models import Account, Trade, ForexPair, OptionTrade

# Register your models here.
admin.site.register(Account)
admin.site.register(Trade)
admin.site.register(ForexPair)
admin.site.register(OptionTrade)