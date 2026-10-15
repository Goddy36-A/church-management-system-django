import re

from django.db import migrations

# Wording that older seeds stamped onto records; removed from existing data.
MARKER = re.compile(r"\s*DEMO DATA\s*[\u2014-]\s*fictional, for academic evaluation purposes only\.?", re.I)
APPS = ["members", "attendance", "events", "communications", "finance", "coresys"]


def strip_labels(apps, schema_editor):
    from django.db import models

    for app_label in APPS:
        for model in apps.get_app_config(app_label).get_models():
            text_fields = [
                f.name for f in model._meta.get_fields()
                if isinstance(f, (models.CharField, models.TextField)) and not f.primary_key
            ]
            for name in text_fields:
                for obj in model.objects.filter(**{f"{name}__icontains": "DEMO DATA"}):
                    setattr(obj, name, MARKER.sub("", getattr(obj, name) or "").strip())
                    obj.save(update_fields=[name])

    # Survey responses seeded with a placeholder respondent role.
    SurveyResponse = apps.get_model("coresys", "SurveyResponse")
    SurveyResponse.objects.filter(respondent_role="demo").update(respondent_role="member")


class Migration(migrations.Migration):
    dependencies = [
        ("coresys", "0001_initial"),
        ("members", "0001_initial"),
        ("attendance", "0001_initial"),
        ("events", "0001_initial"),
        ("communications", "0001_initial"),
        ("finance", "0001_initial"),
    ]
    operations = [
        migrations.RenameField("surveyresponse", "is_demo_data", "is_seeded"),
        migrations.RunPython(strip_labels, migrations.RunPython.noop),
    ]
