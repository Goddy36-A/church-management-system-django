from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import RoleName
from coresys.audit import log_action
from coresys.decorators import roles_required

from .models import Department, Group, GroupMember, Member, Ministry

EDITOR_ROLES = (RoleName.ADMIN, RoleName.PASTOR)


# ---------- Ministries ----------

@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def ministries_index(request):
    ministries = Ministry.objects.filter(is_archived=False).order_by("name")
    return render(request, "structure/ministries.html", {"ministries": ministries})


@login_required
@roles_required(*EDITOR_ROLES)
def ministry_create(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Ministry name is required.")
            return redirect("structure:ministry_create")
        m = Ministry.objects.create(
            name=name, description=request.POST.get("description", "").strip() or None,
            leader_id=request.POST.get("leader_id") or None,
        )
        log_action(request, "ministry.create", entity_type="Ministry", entity_id=m.id, description=f"Created ministry {m.name}")
        messages.success(request, f"Ministry '{m.name}' created.")
        return redirect("structure:ministries_index")
    return render(request, "structure/ministry_form.html", {"members": members, "ministry": None})


@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def ministry_view(request, ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    members = Member.objects.filter(ministry_id=ministry.id, is_archived=False).order_by("last_name")
    return render(request, "structure/ministry_view.html", {"ministry": ministry, "members": members})


@login_required
@roles_required(*EDITOR_ROLES)
def ministry_archive(request, ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    ministry.is_archived = True
    ministry.save()
    log_action(request, "ministry.archive", entity_type="Ministry", entity_id=ministry.id)
    messages.info(request, f"Ministry '{ministry.name}' archived.")
    return redirect("structure:ministries_index")


# ---------- Departments ----------

@login_required
@roles_required(*EDITOR_ROLES)
def departments_index(request):
    departments = Department.objects.filter(is_archived=False).order_by("name")
    return render(request, "structure/departments.html", {"departments": departments})


@login_required
@roles_required(*EDITOR_ROLES)
def department_create(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Department name is required.")
            return redirect("structure:department_create")
        d = Department.objects.create(
            name=name, description=request.POST.get("description", "").strip() or None,
            leader_id=request.POST.get("leader_id") or None,
        )
        log_action(request, "department.create", entity_type="Department", entity_id=d.id)
        messages.success(request, f"Department '{d.name}' created.")
        return redirect("structure:departments_index")
    return render(request, "structure/department_form.html", {"members": members})


@login_required
@roles_required(*EDITOR_ROLES)
def department_view(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    members = Member.objects.filter(department_id=department.id, is_archived=False).order_by("last_name")
    return render(request, "structure/department_view.html", {"department": department, "members": members})


# ---------- Groups / Cells ----------

@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def groups_index(request):
    groups = Group.objects.filter(is_archived=False).order_by("name")
    return render(request, "structure/groups.html", {"groups": groups})


@login_required
@roles_required(*EDITOR_ROLES)
def group_create(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Group name is required.")
            return redirect("structure:group_create")
        g = Group.objects.create(
            name=name,
            description=request.POST.get("description", "").strip() or None,
            leader_id=request.POST.get("leader_id") or None,
            meeting_day=request.POST.get("meeting_day") or None,
            location=request.POST.get("location", "").strip() or None,
        )
        log_action(request, "group.create", entity_type="Group", entity_id=g.id)
        messages.success(request, f"Group '{g.name}' created.")
        return redirect("structure:groups_index")
    return render(request, "structure/group_form.html", {"members": members})


@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def group_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    all_members = Member.objects.filter(is_archived=False).order_by("last_name")
    member_ids_in_group = {gm.member_id for gm in group.memberships.all()}
    return render(request, "structure/group_view.html", {
        "group": group, "all_members": all_members, "member_ids_in_group": member_ids_in_group,
    })


@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def group_add_member(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    member_id = request.POST.get("member_id")
    if member_id and not GroupMember.objects.filter(group_id=group.id, member_id=member_id).exists():
        GroupMember.objects.create(group_id=group.id, member_id=member_id)
        log_action(request, "group.add_member", entity_type="Group", entity_id=group.id)
        messages.success(request, "Member added to group.")
    return redirect("structure:group_view", group_id=group.id)


@login_required
@roles_required(*EDITOR_ROLES, RoleName.MINISTRY_LEADER)
def group_remove_member(request, group_id, member_id):
    gm = get_object_or_404(GroupMember, group_id=group_id, member_id=member_id)
    gm.delete()
    log_action(request, "group.remove_member", entity_type="Group", entity_id=group_id)
    messages.info(request, "Member removed from group.")
    return redirect("structure:group_view", group_id=group_id)
