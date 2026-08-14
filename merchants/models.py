from django.db import models

class Merchant(models.Model):
    canonical_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    aliases = models.JSONField(default=list, blank=True)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_variance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.canonical_name