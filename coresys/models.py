from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)  # e.g. "member.create", "auth.login"
    entity_type = models.CharField(max_length=80, blank=True, null=True)  # e.g. "Member"
    entity_id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    ip_address = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.action


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class EfficiencyMetric(models.Model):
    """
    Researcher-entered baseline (manual process) vs system-supported time measurements.
    Used by the Administrative Efficiency dashboard to calculate % improvement.
    These are configurable research inputs, never fabricated system data.
    """

    metric_name = models.CharField(max_length=150)  # e.g. "Member registration time (minutes)"
    previous_process_value = models.FloatField()
    cmis_process_value = models.FloatField()
    unit = models.CharField(max_length=30, default="minutes")
    notes = models.CharField(max_length=255, blank=True, null=True)

    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def improvement_percent(self):
        if not self.previous_process_value:
            return None
        return round(
            ((self.previous_process_value - self.cmis_process_value) / self.previous_process_value) * 100, 1
        )

    def __str__(self):
        return self.metric_name


class SurveyQuestion(models.Model):
    """Configurable Likert-scale evaluation questions for the research module."""

    dimension = models.CharField(max_length=30)  # "administrative_efficiency" or "member_engagement"
    text = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class SurveyResponse(models.Model):
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="responses")
    respondent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    respondent_role = models.CharField(max_length=50, blank=True, null=True)  # captured at time of response
    score = models.IntegerField()  # 1-5 Likert
    is_demo_data = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(score__gte=1) & models.Q(score__lte=5), name="ck_score_range")
        ]

    def __str__(self):
        return f"Response to {self.question_id}"
