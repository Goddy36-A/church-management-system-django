from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import RoleName, User
from coresys.audit import log_action
from coresys.decorators import roles_required
from members.models import Department, Group, Member, Ministry

from .models import Announcement, AnnouncementAudience, FollowUp, FollowUpReason, FollowUpStatus

EDITOR_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.MINISTRY_LEADER)


# ---------------- Announcements ----------------

@login_required
def announcements_index(request):
    today = date.today()
    query = Announcement.objects.filter(status="published", publish_date__lte=today)
    query = query.filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
    announcements = query.order_by("-priority", "-publish_date")
    can_manage = request.user.has_role(*EDITOR_ROLES, RoleName.SUPER_ADMIN)
    return render(request, "announcements/index.html", {"announcements": announcements, "can_manage": can_manage})


@login_required
@roles_required(*EDITOR_ROLES)
def announcements_create(request):
    ministries = Ministry.objects.filter(is_archived=False).order_by("name")
    departments = Department.objects.filter(is_archived=False).order_by("name")
    groups = Group.objects.filter(is_archived=False).order_by("name")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        if not title or not message:
            messages.error(request, "Title and message are required.")
            return redirect("announcements:create")

        expiry_raw = request.POST.get("expiry_date")
        expiry_date = None
        if expiry_raw:
            try:
                expiry_date = datetime.strptime(expiry_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        a = Announcement.objects.create(
            title=title,
            message=message,
            author=request.user,
            target_audience=request.POST.get("target_audience", AnnouncementAudience.ALL),
            target_ministry_id=request.POST.get("target_ministry_id") or None,
            target_department_id=request.POST.get("target_department_id") or None,
            target_group_id=request.POST.get("target_group_id") or None,
            expiry_date=expiry_date,
            priority=request.POST.get("priority", "normal"),
            status=request.POST.get("status", "published"),
        )
        log_action(request, "announcement.create", entity_type="Announcement", entity_id=a.id, description=a.title)
        messages.success(request, "Announcement published.")
        return redirect("announcements:index")

    return render(request, "announcements/form.html", {
        "ministries": ministries, "departments": departments, "groups": groups,
        "audiences": AnnouncementAudience.CHOICES_LIST,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def announcements_archive(request, announcement_id):
    a = get_object_or_404(Announcement, id=announcement_id)
    a.status = "archived"
    a.save()
    log_action(request, "announcement.archive", entity_type="Announcement", entity_id=a.id)
    messages.info(request, "Announcement archived.")
    return redirect("announcements:index")


# ---------------- Follow-ups ----------------

@login_required
@roles_required(*EDITOR_ROLES)
def followups_index(request):
    status = request.GET.get("status", "")
    query = FollowUp.objects.all()
    if status:
        query = query.filter(status=status)
    followups = query.order_by("-date_created")

    stats = {s: FollowUp.objects.filter(status=s).count() for s in FollowUpStatus.ALL}

    return render(request, "followups/index.html", {
        "followups": followups, "status": status, "stats": stats, "reason_labels": FollowUpReason.LABELS,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def followups_create(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    staff = User.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        member_id = request.POST.get("member_id")
        if not member_id:
            messages.error(request, "Please select a member.")
            return redirect("followups:create")

        next_date_raw = request.POST.get("next_followup_date")
        next_date = None
        if next_date_raw:
            try:
                next_date = datetime.strptime(next_date_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        f = FollowUp.objects.create(
            member_id=member_id,
            reason=request.POST.get("reason", FollowUpReason.OTHER),
            assigned_to_id=request.POST.get("assigned_to_id") or request.user.id,
            notes=request.POST.get("notes", "").strip() or None,
            next_followup_date=next_date,
            created_by=request.user,
        )
        log_action(request, "followup.create", entity_type="FollowUp", entity_id=f.id)
        messages.success(request, "Follow-up record created.")
        return redirect("followups:index")

    return render(request, "followups/form.html", {
        "members": members, "reasons": FollowUpReason.ALL, "reason_labels": FollowUpReason.LABELS, "staff": staff,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def followups_update_status(request, followup_id):
    from django.utils import timezone
    f = get_object_or_404(FollowUp, id=followup_id)
    new_status = request.POST.get("status")
    outcome = request.POST.get("outcome", "").strip()

    if new_status in FollowUpStatus.ALL:
        f.status = new_status
        if new_status == FollowUpStatus.COMPLETED:
            f.completed_at = timezone.now()
    if outcome:
        f.outcome = outcome
    f.save()

    log_action(request, "followup.update", entity_type="FollowUp", entity_id=f.id, description=f"Status -> {new_status}")
    messages.success(request, "Follow-up updated.")
    return redirect("followups:index")
