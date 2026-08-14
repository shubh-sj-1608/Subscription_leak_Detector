from django.contrib import admin
from .models import Subscription, UserFeedback, PriceHistory

admin.site.register(Subscription)
admin.site.register(UserFeedback)
admin.site.register(PriceHistory)