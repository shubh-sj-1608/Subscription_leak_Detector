from django.db import models
from django.contrib.auth.models import User
from merchants.models import Merchant

class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('flagged', 'Flagged'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    first_seen = models.DateField()
    last_seen = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    avg_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    risk_score = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.merchant.canonical_name} - {self.user.username}"


class UserFeedback(models.Model):
    FEEDBACK_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('wrong', 'Wrong'),
        ('cancelled', 'Cancelled'),
    ]
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


class PriceHistory(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField() 