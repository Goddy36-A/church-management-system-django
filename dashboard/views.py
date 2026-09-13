from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import RoleName
from attendance.models import AttendanceRecord, AttendanceSession
from communications.models import Announcement, FollowUp, FollowUpStatus
from engagement.services import bulk_engagement_summary
from events.models import Event
from finance.models import Contribution
from members.models import Member, MembershipStatus


@login_required
def index(request):
    role = request.user.role.name if request.user.role else None

    if role == RoleName.MEMBER:
        return member_dashboard(request)
    if role == RoleName.PASTOR:
        return pastor_dashboard(request)
    return admin_dashboard(request)


def admin_dashboard(request):
    total_members = Member.objects.filter(is_archived=False).count()
    active_members = Member.objects.filter(is_archived=False, membership_status=MembershipStatus.ACTIVE).count()
    new_members = Member.objects.filter(is_archived=False, membership_status=MembershipStatus.NEW).count()

    today = date.today()
    upcoming_events = Event.objects.filter(start_date__gte=today, is_archived=False).order_by("start_date")[:5]
    recent_announcements = Announcement.objects.filter(status="published").order_by("-publish_date")[:5]
    pending_followups = FollowUp.objects.filter(
        status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS]
    ).count()

    recent_contributions = Contribution.objects.filter(contribution_date__gte=today - timedelta(days=30))
    contribution_sum = sum(float(a) for a in recent_contributions.values_list("amount", flat=True))

    last_session = AttendanceSession.objects.order_by("-session_date").first()

    return render(request, "dashboard/admin.html", {
        "total_members": total_members,
        "active_members": active_members,
        "new_members": new_members,
        "upcoming_events": upcoming_events,
        "recent_announcements": recent_announcements,
        "pending_followups": pending_followups,
        "contribution_sum": contribution_sum,
        "last_session": last_session,
    })


def pastor_dashboard(request):
    today = date.today()
    total_members = Member.objects.filter(is_archived=False).count()
    active_members = Member.objects.filter(is_archived=False, membership_status=MembershipStatus.ACTIVE).count()

    members = list(Member.objects.filter(is_archived=False)[:200])  # capped for dashboard performance
    engagement = bulk_engagement_summary(members)

    pending_followups = FollowUp.objects.filter(
        status__in=[FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS]
    ).order_by("next_followup_date")[:8]

    upcoming_events = Event.objects.filter(start_date__gte=today, is_archived=False).order_by("start_date")[:5]
    recent_announcements = Announcement.objects.filter(status="published").order_by("-publish_date")[:5]

    return render(request, "dashboard/pastor.html", {
        "total_members": total_members,
        "active_members": active_members,
        "engagement": engagement,
        "pending_followups": pending_followups,
        "upcoming_events": upcoming_events,
        "recent_announcements": recent_announcements,
    })


def member_dashboard(request):
    member = request.user.member
    today = date.today()

    upcoming_events = Event.objects.filter(start_date__gte=today, is_archived=False).order_by("start_date")[:5]
    announcements = Announcement.objects.filter(status="published").order_by("-publish_date")[:5]

    attendance_history = []
    if member:
        attendance_history = (
            AttendanceRecord.objects.filter(member_id=member.id, present=True)
            .select_related("session").order_by("-session__session_date")[:10]
        )

    return render(request, "dashboard/member.html", {
        "member": member,
        "upcoming_events": upcoming_events,
        "announcements": announcements,
        "attendance_history": attendance_history,
    })
