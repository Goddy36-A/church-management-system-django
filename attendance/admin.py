from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    autocomplete_fields = ("member",)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "service_type", "session_date", "ministry", "present_count", "visitor_count")
    list_filter = ("service_type", "ministry")
    search_fields = ("title", "notes")
    date_hierarchy = "session_date"
    autocomplete_fields = ("ministry",)
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("session", "member", "present", "is_visitor", "visitor_name", "recorded_at")
    list_filter = ("present", "is_visitor")
    search_fields = ("visitor_name", "visitor_phone")
    autocomplete_fields = ("session", "member")
