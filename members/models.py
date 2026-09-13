from datetime import date
from django.db import models


class MembershipStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    NEW = "new_member"
    TRANSFERRED = "transferred"
    DECEASED = "deceased"

    ALL = [ACTIVE, INACTIVE, NEW, TRANSFERRED, DECEASED]
    LABELS = {
        ACTIVE: "Active",
        INACTIVE: "Inactive",
        NEW: "New Member",
        TRANSFERRED: "Transferred",
        DECEASED: "Deceased",
    }


MembershipStatus.CHOICES = [(k, MembershipStatus.LABELS[k]) for k in MembershipStatus.ALL]


class Ministry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    leader = models.ForeignKey(
        "Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "ministries"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    leader = models.ForeignKey(
        "Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Group(models.Model):
    """Church cell / small group."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    leader = models.ForeignKey(
        "Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    meeting_day = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    member_no = models.CharField(max_length=20, unique=True, db_index=True)  # e.g. MBR-0001

    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True, null=True)
    last_name = models.CharField(max_length=80)
    gender = models.CharField(max_length=10, blank=True, null=True)  # male / female
    date_of_birth = models.DateField(blank=True, null=True)

    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=120, blank=True, null=True)
    physical_address = models.CharField(max_length=255, blank=True, null=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)

    date_joined = models.DateField(default=date.today)
    membership_status = models.CharField(
        max_length=20, choices=MembershipStatus.CHOICES, default=MembershipStatus.NEW, db_index=True
    )
    baptism_status = models.CharField(max_length=30, default="not_baptized")  # not_baptized / baptized
    marital_status = models.CharField(max_length=30, blank=True, null=True)
    occupation = models.CharField(max_length=120, blank=True, null=True)

    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )
    ministry = models.ForeignKey(
        Ministry, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )

    profile_photo = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    is_archived = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __str__(self):
        return f"{self.member_no} {self.full_name}"


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="group_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "member"], name="uq_group_member")
        ]

    def __str__(self):
        return f"{self.member} in {self.group}"
