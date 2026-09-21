from django.contrib import admin

from .models import Event, EventParticipant


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    autocomplete_fields = ("member",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title", "event_type", "start_date", "end_date", "location",
        "status", "registered_count", "attended_count", "is_archived",
    )
    list_filter = ("status", "event_type", "ministry", "is_archived")
    search_fields = ("title", "description", "location")
    date_hierarchy = "start_date"
    autocomplete_fields = ("ministry", "organizer")
    inlines = [EventParticipantInline]


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ("event", "member", "attended", "registered_at")
    list_filter = ("attended",)
    autocomplete_fields = ("event", "member")
