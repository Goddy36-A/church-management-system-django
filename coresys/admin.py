from django.contrib import admin

from .models import AuditLog, EfficiencyMetric, SurveyQuestion, SurveyResponse, SystemSetting


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "entity_type", "entity_id", "ip_address")
    list_filter = ("action", "entity_type")
    search_fields = ("description", "ip_address")
    date_hierarchy = "created_at"
    autocomplete_fields = ("user",)

    # Audit logs are a record of what happened, not something to hand-edit.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description", "updated_at")
    search_fields = ("key", "description")


@admin.register(EfficiencyMetric)
class EfficiencyMetricAdmin(admin.ModelAdmin):
    list_display = (
        "metric_name", "previous_process_value", "cmis_process_value",
        "unit", "improvement_label", "recorded_by", "created_at",
    )
    search_fields = ("metric_name", "notes")
    autocomplete_fields = ("recorded_by",)


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "dimension", "is_active", "display_order")
    list_filter = ("dimension", "is_active")
    search_fields = ("text",)


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("question", "score", "respondent", "respondent_role", "is_demo_data", "submitted_at")
    list_filter = ("score", "is_demo_data", "respondent_role")
    date_hierarchy = "submitted_at"
    autocomplete_fields = ("question", "respondent")
