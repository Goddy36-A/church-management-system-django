"""
URL configuration for cmis_django project.

Mapping mirrors the original Flask blueprint registration:
  auth_bp          -> ""                 (accounts.urls)
  dashboard_bp      -> "/"                (dashboard.urls)
  members_bp        -> "/members/"        (members.urls)
  attendance_bp      -> "/attendance/"     (attendance.urls)
  structure_bp       -> ""                (members.structure_urls)
  events_bp          -> "/events/"         (events.urls)
  announcements_bp   -> "/announcements/"  (communications.urls)
  followups_bp        -> "/followups/"      (communications.followup_urls)
  contributions_bp    -> "/contributions/"  (finance.urls)
  reports_bp          -> "/reports/"        (reportsapp.urls)
  engagement_bp        -> "/engagement/"     (engagement.urls)
  efficiency_bp         -> "/efficiency/"     (coresys.efficiency_urls)
  research_bp           -> "/research/"       (coresys.research_urls)
  admin_bp               -> "/admin/"          (adminpanel.urls)

Django's own admin site is moved to "/django-admin/" to avoid clashing with
the CMIS admin panel, which occupies "/admin/" just like the original app.
"""

from django.contrib import admin
from django.urls import include, path

# Custom error handlers (templates live in templates/errors/)
handler403 = "cmis_django.views.handler403"
handler404 = "cmis_django.views.handler404"
handler500 = "cmis_django.views.handler500"

urlpatterns = [
    path("django-admin/", admin.site.urls),

    path("", include("accounts.urls")),
    path("", include("dashboard.urls")),
    path("members/", include("members.urls")),
    path("attendance/", include("attendance.urls")),
    path("", include("members.structure_urls")),
    path("events/", include("events.urls")),
    path("announcements/", include("communications.urls")),
    path("followups/", include("communications.followup_urls")),
    path("contributions/", include("finance.urls")),
    path("reports/", include("reportsapp.urls")),
    path("engagement/", include("engagement.urls")),
    path("efficiency/", include("coresys.efficiency_urls")),
    path("research/", include("coresys.research_urls")),
    path("admin/", include("adminpanel.urls")),
]
