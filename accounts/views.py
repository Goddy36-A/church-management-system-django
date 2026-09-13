from django.contrib import messages
from django.contrib.auth import authenticate as dj_authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone

from coresys.audit import log_action
from .models import User, Role, RoleName


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = User.objects.filter(Q(username=identifier) | Q(email=identifier)).first()

        if user is None or not user.check_password(password):
            messages.error(request, "Invalid username or password.")
            log_action(request, "auth.login_failed", description=f"Failed login attempt for '{identifier}'")
            return render(request, "auth/login.html", status=401)

        if not user.is_active:
            messages.error(request, "This account has been deactivated. Contact an administrator.")
            return render(request, "auth/login.html", status=403)

        dj_login(request, user)
        if not request.POST.get("remember"):
            request.session.set_expiry(0)
        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])
        log_action(request, "auth.login", entity_type="User", entity_id=user.id, description="Successful login")

        next_page = request.GET.get("next")
        return redirect(next_page or "dashboard:index")

    return render(request, "auth/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if username and User.objects.filter(username=username).exists():
            errors.append("That username is already taken.")
        if email and User.objects.filter(email=email).exists():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "auth/register.html", {"form": request.POST})

        member_role = Role.objects.filter(name=RoleName.MEMBER).first()
        if not member_role:
            messages.error(request, "The system is not fully set up yet (no Member role found). "
                                     "Contact an administrator.")
            return render(request, "auth/register.html", {"form": request.POST})

        user = User(username=username, email=email, full_name=full_name, phone=phone or None,
                    role=member_role)
        user.set_password(password)
        user.save()
        log_action(request, "auth.register", entity_type="User", entity_id=user.id,
                   description=f"Self-registered account '{username}'")

        dj_login(request, user)
        messages.success(request, "Account created. Welcome! Ask a church administrator to link your account "
                                   "to your member profile if you don't see your details yet.")
        return redirect("dashboard:index")

    return render(request, "auth/register.html", {"form": {}})


@login_required
def logout_view(request):
    log_action(request, "auth.logout", entity_type="User", entity_id=request.user.id)
    dj_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    if request.method == "POST":
        request.user.full_name = request.POST.get("full_name", request.user.full_name).strip()
        request.user.phone = request.POST.get("phone", request.user.phone)
        request.user.save()
        messages.success(request, "Profile updated.")
        log_action(request, "auth.profile_update", entity_type="User", entity_id=request.user.id)
        return redirect("accounts:profile")

    return render(request, "auth/profile.html")


@login_required
def change_password_view(request):
    current_password = request.POST.get("current_password", "")
    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    if not request.user.check_password(current_password):
        messages.error(request, "Current password is incorrect.")
        return redirect("accounts:profile")

    if len(new_password) < 8:
        messages.error(request, "New password must be at least 8 characters.")
        return redirect("accounts:profile")

    if new_password != confirm_password:
        messages.error(request, "New passwords do not match.")
        return redirect("accounts:profile")

    request.user.set_password(new_password)
    request.user.must_change_password = False
    request.user.save()
    log_action(request, "auth.password_change", entity_type="User", entity_id=request.user.id)
    messages.success(request, "Password changed successfully.")
    # Django logs the user out on password change by default via session hash;
    # re-authenticate to keep the session (mirrors original Flask "silent" behavior).
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    return redirect("accounts:profile")
