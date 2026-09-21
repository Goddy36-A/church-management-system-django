from django.contrib import admin

from .models import Contribution, ContributionCategory


@admin.register(ContributionCategory)
class ContributionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "description")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = (
        "contribution_date", "member", "category", "amount",
        "currency", "payment_method", "recorded_by",
    )
    list_filter = ("category", "payment_method", "currency")
    search_fields = ("reference", "notes")
    date_hierarchy = "contribution_date"
    autocomplete_fields = ("member", "category", "recorded_by")
