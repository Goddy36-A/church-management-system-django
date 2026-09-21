from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "description")
    search_fields = ("name", "description")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("username", "full_name", "email", "role", "is_active", "is_staff", "last_login_at")
    list_filter = ("role", "is_active", "is_staff", "must_change_password")
    search_fields = ("username", "email", "full_name", "phone")
    ordering = ("full_name",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "phone")}),
        ("Church", {"fields": ("role", "member", "ministry")}),
        ("Permissions", {"fields": (
            "is_active", "is_staff", "is_superuser", "must_change_password",
            "groups", "user_permissions",
        )}),
        ("Important dates", {"fields": ("last_login", "last_login_at", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "full_name", "role", "password1", "password2"),
        }),
    )
    readonly_fields = ("last_login_at", "date_joined")
