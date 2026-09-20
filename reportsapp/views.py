from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render

from accounts.models import RoleName
from attendance.models import AttendanceRecord, AttendanceSession
from communications.models import Announcement, FollowUp
from coresys.decorators import roles_required
from coresys.models import AuditLog
from events.models import Event
from finance.models import Contribution
from members.models import Department, Member, MembershipStatus, Ministry

REPORT_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.FINANCE_OFFICER, RoleName.MINISTRY_LEADER)


@login_required
@roles_required(*REPORT_ROLES)
def index(request):
    return render(request, "reports/index.html")


@login_required
@roles_required(*REPORT_ROLES)
def membership(request):
    members = Member.objects.filter(is_archived=False)
    total = members.count()
    by_status = {s: 0 for s in MembershipStatus.ALL}
    by_gender = {"male": 0, "female": 0, "unspecified": 0}
    by_ministry = {}
    age_bands = {"Under 18": 0, "18-30": 0, "31-45": 0, "46-60": 0, "Over 60": 0, "Unknown": 0}

    for m in members:
        by_status[m.membership_status] = by_status.get(m.membership_status, 0) + 1
        gender_key = (m.gender or "unspecified").lower()
        by_gender[gender_key] = by_gender.get(gender_key, 0) + 1
        ministry_name = m.ministry.name if m.ministry else "Unassigned"
        by_ministry[ministry_name] = by_ministry.get(ministry_name, 0) + 1

        age = m.age
        if age is None:
            age_bands["Unknown"] += 1
        elif age < 18:
            age_bands["Under 18"] += 1
        elif age <= 30:
            age_bands["18-30"] += 1
        elif age <= 45:
            age_bands["31-45"] += 1
        elif age <= 60:
            age_bands["46-60"] += 1
        else:
            age_bands["Over 60"] += 1

    status_labels_list = [MembershipStatus.LABELS.get(k, k) for k in by_status.keys()]

    return render(request, "reports/membership.html", {
        "total": total,
        "by_status": by_status,
        "status_labels": MembershipStatus.LABELS,
        "status_chart_labels": status_labels_list,
        "status_chart_values": list(by_status.values()),
        "gender_labels": list(by_gender.keys()),
        "gender_values": list(by_gender.values()),
        "age_labels": list(age_bands.keys()),
        "age_values": list(age_bands.values()),
        "ministry_labels": list(by_ministry.keys()),
        "ministry_values": list(by_ministry.values()),
        "by_gender": by_gender, "by_ministry": by_ministry, "age_bands": age_bands,
    })


@login_required
@roles_required(*REPORT_ROLES)
def attendance(request):
    since = date.today() - timedelta(days=180)
    sessions = AttendanceSession.objects.filter(session_date__gte=since).order_by("session_date")

    labels = [s.session_date.strftime("%d %b") for s in sessions]
    present_counts = [s.present_count for s in sessions]

    by_service_type = {}
    for s in sessions:
        by_service_type[s.service_type] = by_service_type.get(s.service_type, 0) + s.present_count

    from attendance.models import ServiceType
    service_type_labels = [ServiceType.LABELS.get(k, k) for k in by_service_type.keys()]

    return render(request, "reports/attendance.html", {
        "sessions": sessions, "labels": labels, "present_counts": present_counts,
        "by_service_type": by_service_type,
        "service_type_labels": service_type_labels,
        "service_type_values": list(by_service_type.values()),
    })


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def administrative(request):
    # DateTimeFields are compared against an aware datetime, not a bare date.
    since = timezone.now() - timedelta(days=30)
    new_registrations = Member.objects.filter(created_at__gte=since).count()
    followups_completed = FollowUp.objects.filter(completed_at__isnull=False, completed_at__gte=since).count()
    events_managed = Event.objects.filter(created_at__gte=since).count()
    announcements_published = Announcement.objects.filter(created_at__gte=since, status="published").count()
    activity_log_count = AuditLog.objects.filter(created_at__gte=since).count()

    return render(request, "reports/administrative.html", {
        "new_registrations": new_registrations, "followups_completed": followups_completed,
        "events_managed": events_managed, "announcements_published": announcements_published,
        "activity_log_count": activity_log_count,
    })
