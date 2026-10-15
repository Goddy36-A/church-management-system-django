"""Django admin site with a summary dashboard at /django-admin/."""

from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone


class CMISAdminSite(admin.AdminSite):
    site_title = "CMIS Admin"
    index_title = "Dashboard"
    index_template = "admin/cmis_index.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_header = f"{getattr(settings, 'CHURCH_NAME', 'Church')} · Admin"

    # ------------------------------------------------------------------ stats
    def _dashboard(self, request):
        """Build dashboard cards. Each card is only included if the user may
        view the underlying model, so staff with limited permissions never
        see counts (or money) they couldn't open from the model list."""
        # Imported lazily: models aren't ready when this module is first imported.
        from attendance.models import AttendanceSession
        from communications.models import FollowUp, FollowUpStatus
        from coresys.models import AuditLog
        from events.models import Event
        from finance.models import Contribution
        from members.models import Member, MembershipStatus

        user = request.user
        today = timezone.localdate()
        cards = []

        def can_view(model):
            opts = model._meta
            return user.has_perm(f"{opts.app_label}.view_{opts.model_name}") or user.has_perm(
                f"{opts.app_label}.change_{opts.model_name}"
            )

        def url(model):
            opts = model._meta
            return f"admin:{opts.app_label}_{opts.model_name}_changelist"

        if can_view(Member):
            members = Member.objects.filter(is_archived=False)
            cards.append({
                "label": "Members", "value": members.count(), "url_name": url(Member),
                "note": f"{members.filter(membership_status=MembershipStatus.ACTIVE).count()} active",
            })
        if can_view(Event):
            upcoming = Event.objects.filter(is_archived=False, start_date__gte=today)
            cards.append({
                "label": "Upcoming events", "value": upcoming.count(), "url_name": url(Event),
                "note": "from today onwards",
            })
        if can_view(FollowUp):
            open_followups = FollowUp.objects.filter(
                status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS]
            )
            cards.append({
                "label": "Open follow-ups", "value": open_followups.count(),
                "url_name": url(FollowUp), "note": "pending or in progress",
            })
        if can_view(Contribution):
            total = (
                Contribution.objects.filter(contribution_date__gte=today - timedelta(days=30))
                .aggregate(t=Sum("amount"))["t"]
                or 0
            )
            cards.append({
                "label": "Giving, last 30 days", "value": f"UGX {total:,.0f}",
                "url_name": url(Contribution), "note": "all categories",
            })
        if can_view(AttendanceSession):
            last = AttendanceSession.objects.order_by("-session_date").first()
            cards.append({
                "label": "Latest attendance",
                "value": last.present_count if last else "—",
                "url_name": url(AttendanceSession),
                "note": f"{last.title}, {last.session_date:%d %b %Y}" if last else "no sessions yet",
            })

        recent_logs = []
        if can_view(AuditLog):
            recent_logs = list(AuditLog.objects.select_related("user").order_by("-created_at")[:8])

        return {"dashboard_cards": cards, "recent_audit_logs": recent_logs}

    def index(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), **self._dashboard(request)}
        return super().index(request, extra_context)
