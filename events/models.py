from django.conf import settings
from django.db import models


class EventStatus:
    PLANNED = "planned"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL = [PLANNED, ONGOING, COMPLETED, CANCELLED]
    CHOICES = [(k, k.title()) for k in ALL]


class Event(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ministry = models.ForeignKey("members.Ministry", on_delete=models.SET_NULL, null=True, blank=True)
    max_participants = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=EventStatus.CHOICES, default=EventStatus.PLANNED)
    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def registered_count(self):
        return self.participants.count()

    @property
    def attended_count(self):
        return self.participants.filter(attended=True).count()

    def __str__(self):
        return self.title


class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "member"], name="uq_event_member")
        ]

    def __str__(self):
        return f"{self.member} @ {self.event}"
