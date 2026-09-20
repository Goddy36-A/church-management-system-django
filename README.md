# Church Management Information System — Django

A Django port of the original Flask-based Church Management Information System
(academic prototype, Mbarara City). Feature parity with the Flask version: same
data model, same URL paths, same role-based permissions, same screens.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo      # optional: fictional demo data
python manage.py runserver
```

Then open http://127.0.0.1:8000/

### Demo accounts

`seed_demo` creates six accounts, all with the password `Demo@12345`:

| Username | Role |
|---|---|
| `superadmin` | Super Administrator |
| `admin` | Church Administrator |
| `pastor` | Pastor / Church Leader |
| `finance` | Finance Officer |
| `youthleader` | Ministry / Department Leader |
| `member1` | Member |

All seeded records are fictional and tagged `DEMO DATA — fictional, for academic
evaluation purposes only.` Re-run with `--reset` to wipe and reseed.

## Configuration

Settings read from the environment (a `.env` file at the project root is loaded
automatically if `python-dotenv` is installed):

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev placeholder | **Set this in production.** |
| `DJANGO_DEBUG` | `true` | Set to `false` in production. |
| `ALLOWED_HOSTS` | `*` | Comma-separated host list. |
| `DATABASE_URL` | — | Postgres URL; falls back to SQLite when unset. |
| `DATABASE_NAME` | `db.sqlite3` | SQLite file path. |
| `CHURCH_NAME` | Grace Family Church - Mbarara | Shown in the header. |
| `DEMO_MODE` | `true` | Shows the demo-data banner. |

With `DJANGO_DEBUG=false`, secure session and CSRF cookies are enabled
automatically. Static files are served via WhiteNoise — run
`python manage.py collectstatic` before deploying.

## Project layout

Each Django app corresponds to a Flask blueprint / model module:

| App | Covers | Mounted at |
|---|---|---|
| `accounts` | `User`, `Role`; login, register, profile | `/login`, `/register`, `/profile` |
| `members` | `Member`, `Ministry`, `Department`, `Group` | `/members/`, `/ministries`, `/departments`, `/groups` |
| `attendance` | `AttendanceSession`, `AttendanceRecord` | `/attendance/` |
| `events` | `Event`, `EventParticipant` | `/events/` |
| `communications` | `Announcement`, `FollowUp` | `/announcements/`, `/followups/` |
| `finance` | `Contribution`, `ContributionCategory` | `/contributions/` |
| `dashboard` | Role-specific dashboards | `/` |
| `reportsapp` | Membership / attendance / admin reports | `/reports/` |
| `engagement` | Engagement scoring and dashboard | `/engagement/` |
| `coresys` | Audit log, settings, efficiency metrics, research survey | `/efficiency/`, `/research/` |
| `adminpanel` | User management, audit logs, system settings | `/admin/` |

Shared pieces live in `coresys`: `decorators.py` (`roles_required`,
`finance_access_required`), `audit.py` (`log_action`), and
`templatetags/cmis_extras.py`.

URL paths match the Flask app exactly. Django's built-in admin site is therefore
mounted at `/django-admin/`, leaving `/admin/` to the CMIS admin panel as in the
original.

## Notes on the conversion

- **Auth** — Flask-Login was replaced by Django's auth framework with a custom
  `AUTH_USER_MODEL` (`accounts.User`). The original `is_active_account` flag maps
  onto Django's built-in `is_active`. Login accepts either username or email.
- **Templates** — Jinja2 macros in `partials/macros.html` became the
  `cmis_extras` template-tag library (`kpi`, `field`, `select`, `textarea`,
  `password_field`, `badge`, `pagination`, plus `to_json`, `get_item`,
  `role_in`, `first_name`, `parse_pairs` filters). Flask's `csrf_token()` hidden
  inputs became `{% csrf_token %}`; `url_for(...)` became `{% url %}`.
- **Chart data** — Jinja allowed `dict.keys()|list|tojson` inline. Django
  templates do not, so views now pass explicit label/value lists and templates
  serialize them with the `to_json` filter.
- **Engagement scores** are an administrative participation indicator derived
  from attendance, event participation, and ministry/group involvement over a
  rolling 90-day window. They are not a psychological, spiritual, or medical
  assessment, and the UI states this wherever scores appear.
- **Efficiency metrics** are researcher-entered baseline-vs-system measurements,
  not generated figures. The dashboard shows only what a researcher records.

### Bugs fixed during the port

- Class-scope `LABELS`/`CHOICES` comprehensions raised `NameError` under Python 3
  and were moved to module level.
- Several report and efficiency queries compared `DateTimeField`s against bare
  `date` objects, producing naive-datetime warnings under `USE_TZ`; these now use
  timezone-aware cutoffs.

## Status

All routes, role permissions, and create/update flows have been exercised against
seeded data. Not yet ported: the Flask `tests/` suite.
