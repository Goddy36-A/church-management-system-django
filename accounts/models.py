from django.contrib.auth.models import AbstractUser
from django.db import models


class RoleName:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    PASTOR = "pastor"
    FINANCE_OFFICER = "finance_officer"
    MINISTRY_LEADER = "ministry_leader"
    MEMBER = "member"

    ALL = [SUPER_ADMIN, ADMIN, PASTOR, FINANCE_OFFICER, MINISTRY_LEADER, MEMBER]

    LABELS = {
        SUPER_ADMIN: "Super Administrator",
        ADMIN: "Church Administrator",
        PASTOR: "Pastor / Church Leader",
        FINANCE_OFFICER: "Finance Officer",
        MINISTRY_LEADER: "Ministry / Department Leader",
        MEMBER: "Member",
    }

RoleName.CHOICES = [(k, RoleName.LABELS[k]) for k in RoleName.ALL]


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def label(self):
        return RoleName.LABELS.get(self.name, self.name)


class User(AbstractUser):
    """Custom user model. `username`, `email`, password etc. come from AbstractUser."""

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, null=True)

    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users", null=True)

    # Optional link to a member profile
    member = models.OneToOneField(
        "members.Member", on_delete=models.SET_NULL, related_name="user_account",
        null=True, blank=True,
    )

    # Ministry a "ministry_leader" role user leads/oversees (optional scoping)
    ministry = models.ForeignKey(
        "members.Ministry", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    # NOTE: account-active status uses Django's built-in `is_active` field
    # (equivalent to the original is_active_account flag).
    must_change_password = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_role(self, *role_names):
        return self.role and self.role.name in role_names

    def can_view_finances(self):
        return self.has_role(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.FINANCE_OFFICER)

    def __str__(self):
        return f"{self.username} ({self.role.name if self.role else 'no role'})"
