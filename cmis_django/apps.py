from django.contrib.admin.apps import AdminConfig


class CMISAdminConfig(AdminConfig):
    """Swap Django's default admin site for the CMIS one (branded, with a
    dashboard on the index page). Every ``@admin.register`` in the project
    keeps working because the default site is replaced, not duplicated."""

    default_site = "cmis_django.admin_site.CMISAdminSite"
