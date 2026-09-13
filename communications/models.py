from datetime import date
from django.conf import settings
from django.db import models


class AnnouncementAudience:
    ALL = "all"
    YOUTH = "youth"
    MEN = "men"
    WOMEN = "women"
    CHILDREN = "children"
    MINISTRY = "ministry"
    DEPARTMENT = "department"
    GROUP = "group"

    CHOICES_LIST = [ALL, YOUTH, MEN, WOMEN, CHILDREN, MINISTRY, DEPARTMENT, GROUP]
    CHOICES = [(c, c.title()) for c in CHOICES_LIST]


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    target_audience = models.CharField(max_length=30, choices=AnnouncementAudience.CHOICES, default=AnnouncementAudience.ALL)
    target_ministry = models.ForeignKey("members.Ministry", on_delete=models.SET_NULL, null=True, blank=True)
    target_department = models.ForeignKey("members.Department", on_delete=models.SET_NULL, null=True, blank=True)
    target_group = models.ForeignKey("members.Group", on_delete=models.SET_NULL, null=True, blank=True)

    publish_date = models.DateField(default=date.today)
    expiry_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, default="normal")  # low / normal / high
    status = models.CharField(max_length=20, default="published")  # draft / scheduled / published / archived

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())

    def __str__(self):
        return self.title


class FollowUpStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL = [PENDING, IN_PROGRESS, COMPLETED, CANCELLED]
    CHOICES = [(k, k.replace("_", " ").title()) for k in ALL]


class FollowUpReason:
    REPEATED_ABSENCE = "repeated_absence"
    NEW_MEMBER = "new_member_followup"
    PASTORAL_VISIT = "pastoral_visit"
    PRAYER_REQUEST = "prayer_request"
    MEMBERSHIP_INQUIRY = "membership_inquiry"
    EVENT_FOLLOWUP = "event_followup"
    GENERAL_WELFARE = "general_welfare"
    OTHER = "other"

    ALL = [
        REPEATED_ABSENCE, NEW_MEMBER, PASTORAL_VISIT, PRAYER_REQUEST,
        MEMBERSHIP_INQUIRY, EVENT_FOLLOWUP, GENERAL_WELFARE, OTHER,
    ]
    LABELS = {
        REPEATED_ABSENCE: "Repeated Absence",
        NEW_MEMBER: "New Member Follow-up",
        PASTORAL_VISIT: "Pastoral Visit",
        PRAYER_REQUEST: "Prayer Request",
        MEMBERSHIP_INQUIRY: "Membership Inquiry",
        EVENT_FOLLOWUP: "Event Follow-up",
        GENERAL_WELFARE: "General Welfare",
        OTHER: "Other",
    }


FollowUpReason.CHOICES = [(k, FollowUpReason.LABELS[k]) for k in FollowUpReason.ALL]


class FollowUp(models.Model):
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE)
    reason = models.CharField(max_length=30, choices=FollowUpReason.CHOICES, default=FollowUpReason.OTHER)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    date_created = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=FollowUpStatus.CHOICES, default=FollowUpStatus.PENDING, db_index=True)
    notes = models.TextField(blank=True, null=True)
    next_followup_date = models.DateField(blank=True, null=True)
    outcome = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Follow-up for {self.member}"
