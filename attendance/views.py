from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import RoleName
from coresys.audit import log_action
from coresys.decorators import roles_required
from members.models import Member, Ministry

from .models import AttendanceRecord, AttendanceSession, ServiceType

EDITOR_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.MINISTRY_LEADER)


@login_required
@roles_required(*EDITOR_ROLES)
def index(request):
    page = request.GET.get("page", 1)
    query = AttendanceSession.objects.order_by("-session_date")
    paginator = Paginator(query, 15)
    pagination = paginator.get_page(page)
    return render(request, "attendance/index.html", {
        "pagination": pagination, "sessions": pagination.object_list, "service_labels": ServiceType.LABELS,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def create_session(request):
    ministries = Ministry.objects.filter(is_archived=False).order_by("name")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        session_date_raw = request.POST.get("session_date")
        if not title:
            messages.error(request, "Session title is required.")
            return redirect("attendance:create_session")
        try:
            session_date = datetime.strptime(session_date_raw, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            session_date = date.today()

        session = AttendanceSession.objects.create(
            title=title,
            service_type=request.POST.get("service_type", ServiceType.SUNDAY_SERVICE),
            session_date=session_date,
            ministry_id=request.POST.get("ministry_id") or None,
            notes=request.POST.get("notes", "").strip() or None,
            created_by=request.user,
        )
        log_action(request, "attendance.session_create", entity_type="AttendanceSession", entity_id=session.id,
                   description=f"Created attendance session '{session.title}'")
        messages.success(request, "Attendance session created. Now record who attended.")
        return redirect("attendance:record", session_id=session.id)

    return render(request, "attendance/session_form.html", {
        "ministries": ministries, "service_types": ServiceType.ALL, "service_labels": ServiceType.LABELS,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def record(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)

    if request.method == "POST":
        present_ids = {int(x) for x in request.POST.getlist("present_member_ids") if x.isdigit()}
        all_active_ids = set(Member.objects.filter(is_archived=False).values_list("id", flat=True))

        for member_id in all_active_ids:
            existing = AttendanceRecord.objects.filter(session_id=session.id, member_id=member_id).first()
            is_present = member_id in present_ids
            if existing:
                existing.present = is_present
                existing.save()
            elif is_present:
                AttendanceRecord.objects.create(session_id=session.id, member_id=member_id, present=True)

        visitor_names = request.POST.getlist("visitor_name")
        visitor_phones = request.POST.getlist("visitor_phone")
        for name, phone in zip(visitor_names, visitor_phones):
            if name.strip():
                AttendanceRecord.objects.create(
                    session_id=session.id, member=None, present=True,
                    is_visitor=True, visitor_name=name.strip(), visitor_phone=phone.strip() or None,
                )

        log_action(request, "attendance.record", entity_type="AttendanceSession", entity_id=session.id,
                   description=f"Recorded attendance for '{session.title}' ({len(present_ids)} present)")
        messages.success(request, "Attendance recorded.")
        return redirect("attendance:view_session", session_id=session.id)

    q = request.GET.get("q", "").strip()
    query = Member.objects.filter(is_archived=False)
    if q:
        query = query.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(member_no__icontains=q))
    members = query.order_by("last_name")

    existing_present = {
        r.member_id for r in AttendanceRecord.objects.filter(session_id=session.id, present=True) if r.member_id
    }

    return render(request, "attendance/record.html", {
        "session": session, "members": members, "existing_present": existing_present, "q": q,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def view_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    return render(request, "attendance/view.html", {"session": session, "service_labels": ServiceType.LABELS})


@login_required
@roles_required(*EDITOR_ROLES, RoleName.FINANCE_OFFICER)
def analytics(request):
    since = date.today() - timedelta(days=180)
    sessions = AttendanceSession.objects.filter(session_date__gte=since).order_by("session_date")

    labels = [s.session_date.strftime("%d %b") for s in sessions]
    present_counts = [s.present_count for s in sessions]
    visitor_counts = [s.visitor_count for s in sessions]

    return render(request, "attendance/analytics.html", {
        "labels": labels, "present_counts": present_counts, "visitor_counts": visitor_counts, "sessions": sessions,
    })
