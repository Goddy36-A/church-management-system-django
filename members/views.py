import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import RoleName
from coresys.audit import log_action
from coresys.decorators import roles_required
from engagement.services import compute_member_engagement

from .models import Department, Group, Member, MembershipStatus, Ministry

EDITOR_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.MINISTRY_LEADER)


def _next_member_no():
    last = Member.objects.order_by("-id").first()
    next_id = (last.id + 1) if last else 1
    return f"MBR-{next_id:04d}"


def _member_form_options():
    ministries = Ministry.objects.filter(is_archived=False).order_by("name")
    departments = Department.objects.filter(is_archived=False).order_by("name")
    ministry_options = [(x.id, x.name) for x in ministries]
    department_options = [(x.id, x.name) for x in departments]
    status_options = [(s, MembershipStatus.LABELS[s]) for s in MembershipStatus.ALL]
    return ministry_options, department_options, status_options


@login_required
@roles_required(*EDITOR_ROLES)
def index(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    ministry_id = request.GET.get("ministry_id", "")
    page = request.GET.get("page", 1)

    query = Member.objects.filter(is_archived=False)

    if q:
        query = query.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(member_no__icontains=q) |
            Q(phone__icontains=q) | Q(email__icontains=q)
        )
    if status:
        query = query.filter(membership_status=status)
    if ministry_id:
        query = query.filter(ministry_id=ministry_id)

    query = query.order_by("last_name", "first_name")
    paginator = Paginator(query, request.session.get("items_per_page", 15))
    pagination = paginator.get_page(page)

    ministries = Ministry.objects.filter(is_archived=False).order_by("name")

    return render(request, "members/index.html", {
        "pagination": pagination,
        "members": pagination.object_list,
        "q": q,
        "status": status,
        "ministry_id": ministry_id,
        "ministries": ministries,
        "statuses": MembershipStatus.ALL,
        "status_labels": MembershipStatus.LABELS,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def create(request):
    ministry_options, department_options, status_options = _member_form_options()

    if request.method == "POST":
        errors = []
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        if not first_name:
            errors.append("First name is required.")
        if not last_name:
            errors.append("Last name is required.")

        dob_raw = request.POST.get("date_of_birth")
        dob = None
        if dob_raw:
            from datetime import datetime
            try:
                dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Date of birth is invalid.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "members/form.html", {
                "member": None, "ministry_options": ministry_options,
                "department_options": department_options, "status_options": status_options,
                "form": request.POST,
            })

        from datetime import date as date_cls
        member = Member.objects.create(
            member_no=_next_member_no(),
            first_name=first_name,
            middle_name=request.POST.get("middle_name", "").strip() or None,
            last_name=last_name,
            gender=request.POST.get("gender") or None,
            date_of_birth=dob,
            phone=request.POST.get("phone", "").strip() or None,
            email=request.POST.get("email", "").strip() or None,
            physical_address=request.POST.get("physical_address", "").strip() or None,
            emergency_contact_name=request.POST.get("emergency_contact_name", "").strip() or None,
            emergency_contact_phone=request.POST.get("emergency_contact_phone", "").strip() or None,
            date_joined=date_cls.today(),
            membership_status=request.POST.get("membership_status", MembershipStatus.NEW),
            baptism_status=request.POST.get("baptism_status", "not_baptized"),
            marital_status=request.POST.get("marital_status") or None,
            occupation=request.POST.get("occupation", "").strip() or None,
            department_id=request.POST.get("department_id") or None,
            ministry_id=request.POST.get("ministry_id") or None,
            notes=request.POST.get("notes", "").strip() or None,
        )
        log_action(request, "member.create", entity_type="Member", entity_id=member.id,
                   description=f"Created member {member.full_name}")
        messages.success(request, f"Member {member.full_name} registered as {member.member_no}.")
        return redirect("members:view", member_id=member.id)

    return render(request, "members/form.html", {
        "member": None, "ministry_options": ministry_options,
        "department_options": department_options, "status_options": status_options, "form": {},
    })


@login_required
@roles_required(*EDITOR_ROLES)
def view(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    engagement = compute_member_engagement(member)
    group_names = [gm.group.name for gm in member.group_memberships.select_related("group").all()]
    return render(request, "members/view.html", {
        "member": member, "engagement": engagement, "group_names": group_names,
    })


@login_required
@roles_required(*EDITOR_ROLES)
def edit(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    ministry_options, department_options, status_options = _member_form_options()

    if request.method == "POST":
        member.first_name = request.POST.get("first_name", member.first_name).strip()
        member.middle_name = request.POST.get("middle_name", "").strip() or None
        member.last_name = request.POST.get("last_name", member.last_name).strip()
        member.gender = request.POST.get("gender") or None
        dob_raw = request.POST.get("date_of_birth")
        if dob_raw:
            from datetime import datetime
            try:
                member.date_of_birth = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except ValueError:
                messages.warning(request, "Date of birth is invalid; previous value kept.")
        member.phone = request.POST.get("phone", "").strip() or None
        member.email = request.POST.get("email", "").strip() or None
        member.physical_address = request.POST.get("physical_address", "").strip() or None
        member.emergency_contact_name = request.POST.get("emergency_contact_name", "").strip() or None
        member.emergency_contact_phone = request.POST.get("emergency_contact_phone", "").strip() or None
        member.membership_status = request.POST.get("membership_status", member.membership_status)
        member.baptism_status = request.POST.get("baptism_status", member.baptism_status)
        member.marital_status = request.POST.get("marital_status") or None
        member.occupation = request.POST.get("occupation", "").strip() or None
        member.department_id = request.POST.get("department_id") or None
        member.ministry_id = request.POST.get("ministry_id") or None
        member.notes = request.POST.get("notes", "").strip() or None
        member.save()

        log_action(request, "member.update", entity_type="Member", entity_id=member.id,
                   description=f"Updated member {member.full_name}")
        messages.success(request, "Member record updated.")
        return redirect("members:view", member_id=member.id)

    return render(request, "members/form.html", {
        "member": member, "ministry_options": ministry_options,
        "department_options": department_options, "status_options": status_options, "form": None,
    })


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def archive(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.is_archived = True
    member.save()
    log_action(request, "member.archive", entity_type="Member", entity_id=member.id,
               description=f"Archived member {member.full_name}")
    messages.info(request, f"{member.full_name} has been archived (soft-deleted).")
    return redirect("members:index")


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def restore(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.is_archived = False
    member.save()
    log_action(request, "member.restore", entity_type="Member", entity_id=member.id)
    messages.success(request, f"{member.full_name} restored.")
    return redirect("members:view", member_id=member.id)


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def archived(request):
    page = request.GET.get("page", 1)
    query = Member.objects.filter(is_archived=True).order_by("last_name")
    paginator = Paginator(query, 15)
    pagination = paginator.get_page(page)
    return render(request, "members/archived.html", {"pagination": pagination, "members": pagination.object_list})


@login_required
@roles_required(*EDITOR_ROLES)
def export_csv(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=members_export.csv"
    writer = csv.writer(response)
    writer.writerow(["Member No", "Full Name", "Gender", "Phone", "Email", "Status", "Ministry", "Department", "Date Joined"])
    for m in members:
        writer.writerow([
            m.member_no, m.full_name, m.gender or "", m.phone or "", m.email or "",
            MembershipStatus.LABELS.get(m.membership_status, m.membership_status),
            m.ministry.name if m.ministry else "",
            m.department.name if m.department else "",
            m.date_joined.isoformat() if m.date_joined else "",
        ])
    log_action(request, "member.export", description="Exported member list to CSV")
    return response
