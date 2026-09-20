#!/usr/bin/env python
"""
start.py — one-command bootstrap and launcher for the CMIS Django project.

Runs the setup steps in order, skipping whatever is already done, then starts
the development server.

Usage:
    python start.py                 # setup (if needed) + run server on :8000
    python start.py --port 8080     # use a different port
    python start.py --host 0.0.0.0  # listen on all interfaces (LAN demo)
    python start.py --seed          # force the demo data seed to run
    python start.py --reset         # DESTRUCTIVE: wipe DB, migrate, reseed
    python start.py --no-run        # do the setup, but don't start the server
    python start.py --check         # verify the install, then exit

What it does:
    1. Checks the Python version.
    2. Installs requirements.txt if Django isn't importable.
    3. Applies migrations (making them first if any model has no migration).
    4. Seeds demo data, but only if the database looks empty.
    5. Starts the dev server.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MANAGE = BASE_DIR / "manage.py"
REQUIREMENTS = BASE_DIR / "requirements.txt"
MIN_PYTHON = (3, 10)

# ANSI colours, disabled when the output isn't a terminal or on legacy Windows.
_COLOR = sys.stdout.isatty() and os.name != "nt"


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def step(msg):
    print(_c("36;1", f"\n==> {msg}"))


def ok(msg):
    print(_c("32", f"    {msg}"))


def warn(msg):
    print(_c("33", f"    {msg}"))


def fail(msg, hint=None):
    print(_c("31;1", f"\nERROR: {msg}"))
    if hint:
        print(_c("33", f"Hint:  {hint}"))
    sys.exit(1)


def run(args, **kwargs):
    """Run a subprocess, returning the CompletedProcess. Never raises."""
    return subprocess.run(args, cwd=BASE_DIR, **kwargs)


def manage(*args, capture=False):
    """Invoke manage.py with the current interpreter."""
    cmd = [sys.executable, str(MANAGE), *args]
    if capture:
        return run(cmd, capture_output=True, text=True)
    return run(cmd)


def check_python():
    if sys.version_info < MIN_PYTHON:
        fail(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required "
            f"(found {sys.version_info.major}.{sys.version_info.minor}).",
            "Install a newer Python, or activate a virtualenv that has one.",
        )
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor} detected.")


def in_virtualenv():
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def ensure_dependencies():
    step("Checking dependencies")
    try:
        import django  # noqa: F401
        ok(f"Django {django.get_version()} is installed.")
        return
    except ImportError:
        pass

    warn("Django is not installed.")
    if not REQUIREMENTS.exists():
        fail("requirements.txt not found.", "Run this script from the project root.")

    if not in_virtualenv():
        warn("You are not in a virtual environment. Installing globally.")
        warn("Consider:  python -m venv .venv  &&  source .venv/bin/activate")

    step("Installing from requirements.txt")
    result = run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    if result.returncode != 0:
        fail(
            "Dependency installation failed.",
            f"Try manually: {sys.executable} -m pip install -r requirements.txt",
        )
    ok("Dependencies installed.")


def django_check():
    step("Running Django system checks")
    result = manage("check", capture=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail("Django system checks failed. See the output above.")
    ok("System checks passed.")


def has_pending_model_changes():
    """True if some model change hasn't been captured in a migration yet."""
    result = manage("makemigrations", "--check", "--dry-run", capture=True)
    return result.returncode != 0


def apply_migrations():
    step("Applying database migrations")
    if has_pending_model_changes():
        warn("Model changes without migrations detected; generating them.")
        if manage("makemigrations").returncode != 0:
            fail("makemigrations failed.")
    if manage("migrate").returncode != 0:
        fail("migrate failed.", "If the database is in a bad state, try: python start.py --reset")
    ok("Database is up to date.")


def database_is_empty():
    """True when no Member rows exist (our proxy for 'unseeded')."""
    code = (
        "import django, os;"
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmis_django.settings');"
        "django.setup();"
        "from members.models import Member;"
        "print(Member.objects.count())"
    )
    result = run([sys.executable, "-c", code], capture_output=True, text=True)
    if result.returncode != 0:
        return True
    try:
        return int(result.stdout.strip().splitlines()[-1]) == 0
    except (ValueError, IndexError):
        return True


def seed(force=False, reset=False):
    if reset:
        step("Reseeding demo data (--reset: existing data will be replaced)")
        if manage("seed_demo", "--reset").returncode != 0:
            fail("Seeding failed.")
        ok("Demo data reseeded.")
        return

    if not force and not database_is_empty():
        step("Checking demo data")
        ok("Database already contains records; skipping seed.")
        warn("Use --seed to seed anyway, or --reset to wipe and start over.")
        return

    step("Seeding demo data")
    if manage("seed_demo").returncode != 0:
        fail("Seeding failed.")
    ok("Demo data created.")


def reset_database():
    """Delete the SQLite file so migrations rebuild it from scratch."""
    step("Resetting the database")
    db_path = Path(os.environ.get("DATABASE_NAME", BASE_DIR / "db.sqlite3"))
    if os.environ.get("DATABASE_URL"):
        warn("DATABASE_URL is set; not deleting a remote database.")
        warn("Tables will be reset by the seeder instead.")
        return
    if db_path.exists():
        db_path.unlink()
        ok(f"Deleted {db_path.name}.")
    else:
        ok("No existing database file to delete.")


def confirm_reset():
    print(_c("31;1", "\n!!  --reset will permanently delete all data in the database."))
    answer = input("    Type 'yes' to continue: ").strip().lower()
    if answer != "yes":
        print("Aborted.")
        sys.exit(0)


def print_banner(host, port):
    url = f"http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}/"
    line = "─" * 58
    print(_c("36", f"\n┌{line}┐"))
    print(_c("36;1", "  Church Management Information System — Django"))
    print(_c("36", f"  {url}"))
    print()
    print("  Demo accounts (password for all: Demo@12345):")
    print("    superadmin · admin · pastor · finance · youthleader · member1")
    print(_c("36", f"└{line}┘\n"))


def serve(host, port):
    print_banner(host, port)
    try:
        manage("runserver", f"{host}:{port}")
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap and run the CMIS Django project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", default="8000", help="Port to bind (default: 8000)")
    parser.add_argument("--seed", action="store_true", help="Seed demo data even if records exist")
    parser.add_argument("--reset", action="store_true", help="DESTRUCTIVE: wipe the database and reseed")
    parser.add_argument("--no-seed", action="store_true", help="Skip the demo data seed entirely")
    parser.add_argument("--no-run", action="store_true", help="Set up but don't start the server")
    parser.add_argument("--check", action="store_true", help="Verify the install and exit")
    parser.add_argument("--yes", action="store_true", help="Skip the --reset confirmation prompt")
    args = parser.parse_args()

    if not MANAGE.exists():
        fail("manage.py not found.", "Run start.py from the project root directory.")

    check_python()
    ensure_dependencies()
    django_check()

    if args.check:
        ok("\nInstall looks good.")
        return

    if args.reset:
        if not args.yes:
            confirm_reset()
        reset_database()

    apply_migrations()

    if not args.no_seed:
        seed(force=args.seed, reset=args.reset and bool(os.environ.get("DATABASE_URL")))

    if args.no_run:
        ok("\nSetup complete. Start the server with:  python start.py")
        return

    serve(args.host, args.port)


if __name__ == "__main__":
    main()
