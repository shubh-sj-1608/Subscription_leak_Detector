from django.db import models
from django.contrib.auth.models import User
from merchants.models import Merchant

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    raw_merchant_text = models.CharField(max_length=255)
    cleaned_merchant_name = models.CharField(max_length=255, blank=True, null=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=100, blank=True, null=True)
    is_recurring_candidate = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.raw_merchant_text} - {self.amount} on {self.date}"
