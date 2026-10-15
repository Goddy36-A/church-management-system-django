from django.db import migrations


def grant_staff(apps, schema_editor):
    """Existing databases seeded before the Django admin dashboard existed have
    super_admin users without is_staff/is_superuser, so /django-admin/ refuses
    them. Fix them once here."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(role__name="super_admin").update(is_staff=True, is_superuser=True)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(grant_staff, migrations.RunPython.noop)]
