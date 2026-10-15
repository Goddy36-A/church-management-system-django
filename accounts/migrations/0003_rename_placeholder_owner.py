from django.db import migrations


def rename(apps, schema_editor):
    """Earlier seeds named the super-admin account after a person who is not
    the owner of the system. Give it a neutral name."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(full_name="Grace Ahumuza").update(full_name="System Administrator")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_super_admin_staff_flags")]
    operations = [migrations.RunPython(rename, migrations.RunPython.noop)]
