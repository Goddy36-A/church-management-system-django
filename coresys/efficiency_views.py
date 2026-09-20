from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import RoleName
from attendance.models import AttendanceSession
from communications.models import Announcement, FollowUp
from events.models import Event
from members.models import Member

from .audit import log_action
from .decorators import roles_required
from .models import EfficiencyMetric


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def index(request):
    since = date.today() - timedelta(days=30)

    usage_indicators = {
        "member_records_processed": Member.objects.filter(created_at__gte=since).count(),
        "attendance_records_processed": AttendanceSession.objects.filter(session_date__gte=since).count(),
        "followups_completed": FollowUp.objects.filter(completed_at__isnull=False, completed_at__gte=since).count(),
        "events_managed": Event.objects.filter(created_at__gte=since).count(),
        "announcements_published": Announcement.objects.filter(created_at__gte=since).count(),
    }

    metrics = EfficiencyMetric.objects.order_by("-created_at")

    return render(request, "efficiency/index.html", {"usage_indicators": usage_indicators, "metrics": metrics})


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def add_metric(request):
    if request.method == "POST":
        name = request.POST.get("metric_name", "").strip()
        try:
            previous_value = float(request.POST.get("previous_process_value", 0))
            cmis_value = float(request.POST.get("cmis_process_value", 0))
        except ValueError:
            messages.error(request, "Please enter valid numeric values.")
            return redirect("efficiency:add_metric")

        if not name:
            messages.error(request, "Metric name is required.")
            return redirect("efficiency:add_metric")

        m = EfficiencyMetric.objects.create(
            metric_name=name,
            previous_process_value=previous_value,
            cmis_process_value=cmis_value,
            unit=request.POST.get("unit", "minutes"),
            notes=request.POST.get("notes", "").strip() or None,
            recorded_by=request.user,
        )
        log_action(request, "efficiency_metric.create", entity_type="EfficiencyMetric", entity_id=m.id, description=name)
        messages.success(request, "Baseline/measured metric recorded.")
        return redirect("efficiency:index")

    return render(request, "efficiency/metric_form.html")
