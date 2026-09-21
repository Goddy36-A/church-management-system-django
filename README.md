# Church Management Information System — Django

A Django port of the original Flask-based Church Management Information System
(academic prototype, Mbarara City). Feature parity with the Flask version: same
data model, same URL paths, same role-based permissions, same screens.

## Quick start

### Easiest — one command

**Windows:** double-click `setup.bat` (first time), then `run.bat`.

**Linux / macOS:**

```bash
./setup.sh      # first time only
./run.sh
```

These create a virtualenv, install dependencies, migrate, seed demo data, and
start the server at http://127.0.0.1:8000/.

### Or use start.py directly

If you already have the dependencies installed, `start.py` handles everything
itself and is safe to re-run:

```bash
python start.py                 # setup (as needed) + run server
python start.py --port 8080     # different port
python start.py --host 0.0.0.0  # listen on the LAN (for a demo machine)
python start.py --seed          # force the demo seed to run
python start.py --reset         # DESTRUCTIVE: wipe DB, migrate, reseed
python start.py --no-run        # set up, but don't start the server
python start.py --check         # verify the install and exit
```

It checks the Python version, installs `requirements.txt` if Django is missing,
generates any missing migrations, applies them, and seeds only when the database
is empty.

### Or do it manually

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo      # optional: fictional demo data
python manage.py runserver
```

### Helper scripts

Matching `.bat` (Windows) and `.sh` (Linux/macOS) versions live in `scripts/`:

| Script | Does |
|---|---|
| `setup` | Create venv, install deps, migrate, seed. Run once. |
| `start` | Activate the venv and launch the server. Passes args to `start.py`. |
| `seed` | Load the fictional demo data. |
| `reset` | **Destructive.** Wipe the database and reseed, after confirmation. |
| `test` | Run Django system checks and the test suite. |

`setup.bat` / `run.bat` and `setup.sh` / `run.sh` at the project root are
shortcuts to the two you'll use most.

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

Postgres support (`psycopg2-binary`) is **not** in `requirements.txt` — local
development uses SQLite and needs no C compiler or build tools. If you set
`DATABASE_URL`, install the extra first:

```bash
pip install -r requirements-postgres.txt
```

Skipping this gives a clear error telling you to run that command, rather
than a confusing build failure.
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

Automation lives in `start.py` (the cross-platform bootstrapper) and `scripts/`
(thin `.bat` / `.sh` wrappers around it).

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

## Self-destruct timer (autophage.py) — optional

`autophage.py` is a 30-day countdown timer for this project. It is **not
installed or running by default** — nothing happens until you explicitly run:

```bash
python autophage.py --install
```

That records the current time, registers a daily scheduled check (cron on
Linux/macOS, Task Scheduler on Windows — or prints the command to add it
yourself if neither is available), and from then on: **30 days later, the
entire project directory is deleted**, unless you've disabled it first.

```bash
python autophage.py --status      # days remaining / enabled?
python autophage.py --disable     # stop the countdown (state is kept)
python autophage.py --enable      # turn it back on
python autophage.py --uninstall   # remove the scheduled job + countdown state
                                   # (does NOT delete the project)
```

Two things stop it, and only two:
1. Setting `enabled` to `false` — via `--disable`, or by hand-editing
   `.autophage.json`.
2. Deleting `autophage.py` itself, which also removes its own scheduled job.

In the final 7 days it logs a countdown warning to `autophage.log` on every
scheduled check. When it fires, it writes a tombstone file one directory level
up (`<project>-DELETED-<timestamp>.log`) explaining what happened and when,
removes its own scheduled job, then deletes the project directory. It only
ever touches its own directory tree — never anything outside it — and it
never touches your GitHub remote, only the local working copy; re-clone to
recover.

It refuses to run at all unless it finds `manage.py` and
`cmis_django/settings.py` right next to it, so a stray copy elsewhere can
never delete the wrong directory.
