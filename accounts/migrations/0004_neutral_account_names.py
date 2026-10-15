from django.db import migrations

# Seeded accounts used personal names. Replace them with role titles, but only
# where the name is still exactly what the seed wrote (never touch edited ones).
SEEDED = {
    "admin": ("Peter Rwabwogo", "Church Administrator"),
    "pastor": ("Pastor Daniel Mugume", "Pastor"),
    "finance": ("Sarah Nabatanzi", "Finance Officer"),
    "youthleader": ("James Katsigazi", "Youth Ministry Leader"),
}


def rename(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for username, (old, new) in SEEDED.items():
        User.objects.filter(username=username, full_name=old).update(full_name=new)
    for u in User.objects.filter(username="member1").select_related("member"):
        m = u.member
        if m and u.full_name == f"{m.first_name} {m.last_name}".strip():
            User.objects.filter(pk=u.pk).update(full_name="Member")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_rename_placeholder_owner"),
        ("members", "0001_initial"),
    ]
    operations = [migrations.RunPython(rename, migrations.RunPython.noop)]
