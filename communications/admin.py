from django.contrib import admin

from .models import Announcement, FollowUp


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title", "target_audience", "priority", "status",
        "publish_date", "expiry_date", "author", "is_expired",
    )
    list_filter = ("target_audience", "priority", "status")
    search_fields = ("title", "message")
    date_hierarchy = "publish_date"
    autocomplete_fields = ("author", "target_ministry", "target_department", "target_group")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = (
        "member", "reason", "status", "assigned_to",
        "date_created", "next_followup_date", "completed_at",
    )
    list_filter = ("status", "reason")
    search_fields = ("notes", "outcome")
    date_hierarchy = "date_created"
    autocomplete_fields = ("member", "assigned_to", "created_by")
