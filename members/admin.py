from django.contrib import admin

from .models import Department, Group, GroupMember, Member, Ministry


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    autocomplete_fields = ("member",)


@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "is_archived", "created_at")
    list_filter = ("is_archived",)
    search_fields = ("name", "description")
    autocomplete_fields = ("leader",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "is_archived", "created_at")
    list_filter = ("is_archived",)
    search_fields = ("name", "description")
    autocomplete_fields = ("leader",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "meeting_day", "location", "is_archived")
    list_filter = ("is_archived", "meeting_day")
    search_fields = ("name", "location")
    autocomplete_fields = ("leader",)
    inlines = [GroupMemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "member_no", "full_name", "gender", "phone", "membership_status",
        "ministry", "department", "date_joined", "is_archived",
    )
    list_filter = ("membership_status", "gender", "baptism_status", "is_archived", "ministry", "department")
    search_fields = ("member_no", "first_name", "last_name", "phone", "email")
    autocomplete_fields = ("ministry", "department")
    date_hierarchy = "date_joined"
    ordering = ("last_name", "first_name")


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ("group", "member", "joined_at")
    list_filter = ("group",)
    autocomplete_fields = ("group", "member")
