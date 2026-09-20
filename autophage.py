#!/usr/bin/env python
"""
autophage.py — a self-destruct timer for this project.

Once installed, it deletes the entire project directory 30 days after
installation — UNLESS you disable it first, by either:

    1. Running:  python autophage.py --disable
       (flips "enabled": false in .autophage.json), or
    2. Deleting this file (and the scheduled job that runs it — see below).

Nothing else stops it. There is no interactive confirmation at delete time,
because it's designed to run unattended from cron / Task Scheduler.

------------------------------------------------------------------------
Commands
------------------------------------------------------------------------
    python autophage.py --install     Start the countdown + register a daily
                                       scheduled check (cron / Task Scheduler).
    python autophage.py --status      Show days remaining, enabled/disabled.
    python autophage.py --disable     Turn it off (keeps the countdown state).
    python autophage.py --enable      Turn it back on.
    python autophage.py --uninstall   Remove the scheduled job and config.
                                       (The project is NOT deleted by this.)
    python autophage.py               Run one check now (what the scheduled
                                       job calls). Deletes the project if the
                                       TTL has elapsed and it's enabled.

------------------------------------------------------------------------
Safety rails
------------------------------------------------------------------------
- Refuses to run at all unless the project directory looks like THIS
  project (manage.py + a cmis_django/settings.py must both exist right
  where this script lives). This exists so a misplaced copy of this file
  can never delete an unrelated directory.
- Writes a countdown warning to autophage.log every time it runs in the
  final 7 days, so a `tail autophage.log` or the start.py banner surfaces
  it before it happens.
- On the day it fires: writes a tombstone log explaining what happened
  and when, removes the scheduled job (so it doesn't error against a
  directory that no longer exists), then deletes everything else.
- Deletion is scoped strictly to this project's own directory tree. It
  never touches anything outside it, and never touches your GitHub
  remote — only the local working copy.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / ".autophage.json"
LOG_PATH = BASE_DIR / "autophage.log"
TOMBSTONE_PATH = BASE_DIR.parent / f"{BASE_DIR.name}-DELETED-{{ts}}.log"

TTL_DAYS = 30
WARNING_WINDOW_DAYS = 7
CRON_MARKER = "# autophage-cmis"
TASK_NAME = "CMISAutophage"


# ---------------------------------------------------------------- sanity ---

def sanity_check():
    """Refuse to run anywhere but the real project root."""
    if not (BASE_DIR / "manage.py").exists():
        fail("manage.py not found next to this script — refusing to run.")
    if not (BASE_DIR / "cmis_django" / "settings.py").exists():
        fail("cmis_django/settings.py not found — this doesn't look like the "
             "CMIS project root. Refusing to run.")


def fail(msg):
    print(f"autophage: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------- config ---

def load_config():
    if not CONFIG_PATH.exists():
        return None
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")


def init_config():
    cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "ttl_days": TTL_DAYS,
    }
    save_config(cfg)
    return cfg


def days_remaining(cfg):
    created = datetime.fromisoformat(cfg["created_at"])
    deadline = created + timedelta(days=cfg.get("ttl_days", TTL_DAYS))
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds() / 86400
    return remaining


# ------------------------------------------------------------- scheduling ---

def _crontab_lines():
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def install_cron():
    python = sys.executable
    script = str(BASE_DIR / "autophage.py")
    entry = f'0 9 * * * {python} {script} >> {BASE_DIR / "autophage.cron.log"} 2>&1 {CRON_MARKER}'

    lines = _crontab_lines()
    if lines is None:
        log("`crontab` is not available on this system. Install a cron daemon, "
            "or add this line yourself with `crontab -e`:")
        log(f"  {entry}")
        return False

    lines = [l for l in lines if CRON_MARKER not in l]
    lines.append(entry)
    try:
        proc = subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
    except FileNotFoundError:
        proc = None
    if proc is None or proc.returncode != 0:
        log("Could not install cron job automatically. Add this line yourself "
            "with `crontab -e`:")
        log(f"  {entry}")
        return False
    log("Installed a daily cron job (09:00) to check the countdown.")
    return True


def uninstall_cron():
    lines = _crontab_lines()
    if not lines:
        return
    kept = [l for l in lines if CRON_MARKER not in l]
    if len(kept) == len(lines):
        return
    try:
        subprocess.run(["crontab", "-"], input="\n".join(kept) + ("\n" if kept else ""), text=True)
    except FileNotFoundError:
        return
    log("Removed the cron job.")


def install_windows_task():
    python = sys.executable
    script = str(BASE_DIR / "autophage.py")
    cmd = [
        "schtasks", "/Create", "/SC", "DAILY", "/TN", TASK_NAME,
        "/TR", f'"{python}" "{script}"', "/ST", "09:00", "/F",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        proc = None
    if proc is None or proc.returncode != 0:
        log("Could not register the Task Scheduler job automatically. "
            "Run this yourself in an elevated Command Prompt:")
        log("  " + " ".join(cmd))
        return False
    log(f"Registered a daily Task Scheduler job ('{TASK_NAME}') to check the countdown.")
    return True


def uninstall_windows_task():
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                        capture_output=True, text=True)
    except FileNotFoundError:
        return
    log("Removed the Task Scheduler job (if it existed).")


def install_schedule():
    if platform.system() == "Windows":
        install_windows_task()
    else:
        install_cron()


def uninstall_schedule():
    if platform.system() == "Windows":
        uninstall_windows_task()
    else:
        uninstall_cron()


# --------------------------------------------------------------- delete ---

def self_destruct(cfg):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tombstone = Path(str(TOMBSTONE_PATH).format(ts=ts))

    message = (
        f"This project directory ({BASE_DIR}) self-destructed via autophage.py.\n"
        f"Installed:  {cfg['created_at']}\n"
        f"TTL:        {cfg.get('ttl_days', TTL_DAYS)} days\n"
        f"Deleted at: {datetime.now(timezone.utc).isoformat()}\n"
        f"Host:       {platform.node()}\n"
        "\n"
        "To recover the project, re-clone it from its git remote (this only\n"
        "deleted the local working copy, not any git history you'd pushed).\n"
    )

    try:
        tombstone.write_text(message)
        print(f"autophage: wrote tombstone to {tombstone}")
    except OSError as e:
        print(f"autophage: could not write tombstone ({e}); deleting anyway.")

    uninstall_schedule()

    print(f"autophage: deleting {BASE_DIR} ...")
    shutil.rmtree(BASE_DIR, ignore_errors=True)
    print("autophage: done.")


# ---------------------------------------------------------------- checks ---

def run_check():
    cfg = load_config()
    if cfg is None:
        fail("Not installed yet. Run: python autophage.py --install")

    if not cfg.get("enabled", True):
        log("Disabled — no action taken.")
        return

    remaining = days_remaining(cfg)

    if remaining <= 0:
        log(f"TTL of {cfg.get('ttl_days', TTL_DAYS)} days elapsed. Self-destructing.")
        self_destruct(cfg)
        return

    if remaining <= WARNING_WINDOW_DAYS:
        log(f"WARNING: {remaining:.1f} day(s) left before this project self-destructs. "
            f"Run `python autophage.py --disable` to stop it.")
    else:
        log(f"{remaining:.1f} day(s) remaining. Enabled.")


def print_status():
    cfg = load_config()
    if cfg is None:
        print("autophage: not installed. Run: python autophage.py --install")
        return
    remaining = days_remaining(cfg)
    state = "ENABLED" if cfg.get("enabled", True) else "disabled"
    if not cfg.get("enabled", True):
        print(f"autophage: {state}. (Would have {max(remaining, 0):.1f} day(s) left if re-enabled.)")
    elif remaining <= 0:
        print(f"autophage: {state}. TTL elapsed — will self-destruct on next scheduled check.")
    else:
        flag = " *** " if remaining <= WARNING_WINDOW_DAYS else " "
        print(f"autophage: {state}.{flag}{remaining:.1f} day(s) remaining "
              f"(installed {cfg['created_at']}).")


def set_enabled(value):
    cfg = load_config()
    if cfg is None:
        fail("Not installed yet. Run: python autophage.py --install")
    cfg["enabled"] = value
    save_config(cfg)
    log(f"{'Enabled' if value else 'Disabled'} by user.")


def do_install():
    if CONFIG_PATH.exists():
        print("autophage: already installed. Use --status to check, or "
              "--uninstall first if you want to reset the countdown.")
        return
    cfg = init_config()
    log(f"Installed. Project will self-destruct in {cfg['ttl_days']} days "
        f"unless disabled (python autophage.py --disable) or this file is removed.")
    install_schedule()
    print_status()


def do_uninstall():
    uninstall_schedule()
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    print("autophage: uninstalled. Countdown state cleared and scheduled job removed. "
          "The project itself was NOT deleted.")


# ------------------------------------------------------------------ main ---

def main():
    sanity_check()

    args = sys.argv[1:]
    if "--install" in args:
        do_install()
    elif "--uninstall" in args:
        do_uninstall()
    elif "--status" in args:
        print_status()
    elif "--disable" in args:
        set_enabled(False)
        print_status()
    elif "--enable" in args:
        set_enabled(True)
        print_status()
    elif args:
        fail(f"Unknown argument(s): {' '.join(args)}")
    else:
        run_check()


if __name__ == "__main__":
    main()
