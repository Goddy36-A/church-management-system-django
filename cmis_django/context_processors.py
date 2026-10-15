from django.conf import settings


def church_globals(request):
    return {
        "church_name": getattr(settings, "CHURCH_NAME", ""),
    }
