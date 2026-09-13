from datetime import date
from django.conf import settings
from django.db import models


class ServiceType:
    SUNDAY_SERVICE = "sunday_service"
    MIDWEEK_SERVICE = "midweek_service"
    BIBLE_STUDY = "bible_study"
    YOUTH_MEETING = "youth_meeting"
    WOMENS_MINISTRY = "womens_ministry"
    MENS_MINISTRY = "mens_ministry"
    CHILDRENS_MINISTRY = "childrens_ministry"
    SPECIAL_EVENT = "special_event"
    OTHER = "other"

    ALL = [
        SUNDAY_SERVICE, MIDWEEK_SERVICE, BIBLE_STUDY, YOUTH_MEETING,
        WOMENS_MINISTRY, MENS_MINISTRY, CHILDRENS_MINISTRY, SPECIAL_EVENT, OTHER,
    ]
    LABELS = {
        SUNDAY_SERVICE: "Sunday Service",
        MIDWEEK_SERVICE: "Midweek Service",
        BIBLE_STUDY: "Bible Study",
        YOUTH_MEETING: "Youth Meeting",
        WOMENS_MINISTRY: "Women's Ministry",
        MENS_MINISTRY: "Men's Ministry",
        CHILDRENS_MINISTRY: "Children's Ministry",
        SPECIAL_EVENT: "Special Event",
        OTHER: "Other Activity",
    }


ServiceType.CHOICES = [(k, ServiceType.LABELS[k]) for k in ServiceType.ALL]


class AttendanceSession(models.Model):
    title = models.CharField(max_length=150)
    service_type = models.CharField(max_length=30, choices=ServiceType.CHOICES, default=ServiceType.SUNDAY_SERVICE)
    session_date = models.DateField(default=date.today, db_index=True)
    ministry = models.ForeignKey("members.Ministry", on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def present_count(self):
        return self.records.filter(present=True).count()

    @property
    def visitor_count(self):
        return self.records.filter(is_visitor=True).count()

    def __str__(self):
        return self.title


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True)  # null if pure visitor

    present = models.BooleanField(default=True)
    is_visitor = models.BooleanField(default=False)
    visitor_name = models.CharField(max_length=150, blank=True, null=True)
    visitor_phone = models.CharField(max_length=30, blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "member"], name="uq_session_member")
        ]

    def __str__(self):
        return f"Record in {self.session}"
