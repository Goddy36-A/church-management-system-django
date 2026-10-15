from django.test import TestCase, override_settings
from django.contrib.auth.models import Permission

from accounts.models import Role, RoleName, User


# The manifest static storage needs `collectstatic`; tests use the plain one.
PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


@PLAIN_STATIC
class AdminDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role, _ = Role.objects.get_or_create(name=RoleName.SUPER_ADMIN)
        cls.superuser = User.objects.create_superuser(username="root", password="pw-12345-x", email="r@x.org")
        cls.superuser.role = role
        cls.superuser.save()
        cls.plain = User.objects.create_user(username="plain", password="pw-12345-x", email="p@x.org")

    def test_superuser_sees_dashboard_cards(self):
        self.client.force_login(self.superuser)
        r = self.client.get("/django-admin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Church overview")
        self.assertContains(r, "Giving, last 30 days")

    def test_staff_without_permissions_sees_no_cards(self):
        self.plain.is_staff = True
        self.plain.save()
        self.client.force_login(self.plain)
        r = self.client.get("/django-admin/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Giving, last 30 days")

    def test_staff_card_respects_model_permission(self):
        self.plain.is_staff = True
        self.plain.save()
        self.plain.user_permissions.add(Permission.objects.get(codename="view_member"))
        self.client.force_login(self.plain)
        r = self.client.get("/django-admin/")
        self.assertContains(r, "Members")
        self.assertNotContains(r, "Giving, last 30 days")

    def test_non_staff_cannot_open_admin(self):
        self.client.force_login(self.plain)
        r = self.client.get("/django-admin/")
        self.assertEqual(r.status_code, 302)


@PLAIN_STATIC
class AccessibilityBasicsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="u1", password="pw-12345-x", email="u@x.org")

    def test_login_has_labelled_username_field(self):
        r = self.client.get("/login")
        self.assertContains(r, 'for="username"')
        self.assertContains(r, 'id="username"')

    def test_layout_has_skip_link_and_main_landmark(self):
        self.client.force_login(self.user)
        r = self.client.get("/")
        self.assertContains(r, 'href="#main-content"')
        self.assertContains(r, '<main id="main-content"')
        self.assertContains(r, 'aria-controls="mobilenav"')

    def test_admin_nav_link_only_for_staff(self):
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get("/"), "Admin Dashboard")
        self.user.is_staff = True
        self.user.save()
        self.assertContains(self.client.get("/"), "Admin Dashboard")


@PLAIN_STATIC
class SuperAdminStaffFlagTests(TestCase):
    def test_super_admin_role_gets_staff_flags_on_save(self):
        role, _ = Role.objects.get_or_create(name=RoleName.SUPER_ADMIN)
        u = User.objects.create_user(username="sa", password="pw-12345-x", email="sa@x.org", role=role)
        u.refresh_from_db()
        self.assertTrue(u.is_staff and u.is_superuser)
        self.client.force_login(u)
        self.assertEqual(self.client.get("/django-admin/").status_code, 200)

    def test_other_roles_are_not_made_staff(self):
        role, _ = Role.objects.get_or_create(name=RoleName.ADMIN)
        u = User.objects.create_user(username="ad", password="pw-12345-x", email="ad@x.org", role=role)
        self.assertFalse(u.is_staff)


@PLAIN_STATIC
class AdminRecentActivityTests(TestCase):
    def test_audit_log_without_user_does_not_break_dashboard(self):
        from coresys.models import AuditLog
        role, _ = Role.objects.get_or_create(name=RoleName.SUPER_ADMIN)
        su = User.objects.create_user(username="sa2", password="pw-12345-x", email="sa2@x.org", role=role)
        AuditLog.objects.create(user=None, action="auth.login_failed", description="Failed login for 'x'")
        AuditLog.objects.create(user=su, action="auth.login", description="Successful login")
        self.client.force_login(su)
        r = self.client.get("/django-admin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "auth.login_failed")
