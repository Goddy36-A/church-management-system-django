import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role, RoleName, User
from coresys.audit import log_action
from coresys.decorators import roles_required
from coresys.models import AuditLog, SystemSetting


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def users(request):
    all_users = User.objects.order_by("full_name")
    return render(request, "admin/users.html", {"users": all_users})


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def create_user(request):
    roles = Role.objects.order_by("name")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        role_id = request.POST.get("role_id")

        if not all([username, email, full_name, role_id]):
            messages.error(request, "All fields are required.")
            return redirect("adminpanel:create_user")

        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "Username or email already in use.")
            return redirect("adminpanel:create_user")

        temp_password = secrets.token_urlsafe(9)
        user = User(username=username, email=email, full_name=full_name, role_id=role_id,
                    must_change_password=True)
        user.set_password(temp_password)
        user.save()
        log_action(request, "user.create", entity_type="User", entity_id=user.id, description=f"Created user {username}")
        messages.success(request, f"User '{username}' created. Temporary password: {temp_password} "
                                   f"(share securely - this will not be shown again).")
        return redirect("adminpanel:users")

    return render(request, "admin/user_form.html", {"roles": roles})


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def toggle_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.id == request.user.id:
        messages.warning(request, "You cannot deactivate your own account.")
        return redirect("adminpanel:users")
    user.is_active = not user.is_active
    user.save()
    log_action(request, "user.toggle_active", entity_type="User", entity_id=user.id,
               description=f"Set active={user.is_active}")
    messages.info(request, f"User '{user.username}' {'activated' if user.is_active else 'deactivated'}.")
    return redirect("adminpanel:users")


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    temp_password = secrets.token_urlsafe(9)
    user.set_password(temp_password)
    user.must_change_password = True
    user.save()
    log_action(request, "user.reset_password", entity_type="User", entity_id=user.id)
    messages.success(request, f"Password for '{user.username}' reset. Temporary password: {temp_password}")
    return redirect("adminpanel:users")


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def audit_logs(request):
    page = request.GET.get("page", 1)
    query = AuditLog.objects.order_by("-created_at")
    paginator = Paginator(query, 15)
    pagination = paginator.get_page(page)
    return render(request, "admin/audit_logs.html", {"pagination": pagination, "logs": pagination.object_list})


@login_required
@roles_required(RoleName.SUPER_ADMIN)
def settings_view(request):
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("setting_"):
                setting_key = key[len("setting_"):]
                setting, created = SystemSetting.objects.get_or_create(
                    key=setting_key, defaults={"value": value}
                )
                if not created:
                    setting.value = value
                    setting.save()
        log_action(request, "settings.update", description="Updated system settings")
        messages.success(request, "Settings updated.")
        return redirect("adminpanel:settings")

    settings_list = SystemSetting.objects.order_by("key")
    return render(request, "admin/settings.html", {"settings": settings_list})
