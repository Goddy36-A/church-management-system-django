from datetime import date
from django.conf import settings
from django.db import models


class ContributionCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)  # Tithe, Offering, Donation, Special...
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "contribution categories"

    def __str__(self):
        return self.name


class Contribution(models.Model):
    member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True)  # null = anonymous
    category = models.ForeignKey(ContributionCategory, on_delete=models.PROTECT, related_name="contributions")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="UGX")
    contribution_date = models.DateField(default=date.today, db_index=True)
    payment_method = models.CharField(max_length=30, default="cash")  # cash / mobile_money / bank / cheque
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} {self.currency} ({self.category})"
