"""
FLIPPY Worker — DB-controlled scanning process.

Starts up and polls ScannerSettings from the database every 5 seconds.
The website controls everything — the worker just executes.

How the website controls the worker:
  - Toggle auto mode on/off  → worker starts/stops scanning
  - Change interval           → worker uses new interval on next scan
  - "Scan Now" button         → sets next_scan_at = now() in DB;
                                worker picks it up within 5 seconds

Worker states written to DB (WorkerStatus.current_task):
  "standby"  — online, idle, auto mode off
  "waiting"  — online, idle, auto mode on, between scans
  "scanning" — actively scanning
  (offline)  — no heartbeat in last 30s

Usage:
    python main.py            # normal — DB-controlled, runs forever
    python main.py --once     # debug only: run one scan immediately then exit
"""
import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path

# ─── Bootstrap ────────────────────────────────────────────────────────────────
WORKER_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORKER_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"

# backend/ → Django models, settings, apps.shared.services
sys.path.insert(0, str(BACKEND_DIR))
# worker/ → services.flippy_scanner_service, services.agents, etc.
sys.path.insert(0, str(WORKER_DIR))

from dotenv import load_dotenv
_env_file = WORKER_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
    print(f"[worker] Loaded .env from {_env_file}")
else:
    print(f"[worker] WARNING: no .env found at {_env_file} — using environment variables")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django
django.setup()

# ─── Django imports (safe after setup) ────────────────────────────────────────
from django.utils import timezone

from apps.scanners.models import WorkerStatus, ScannerSettings
from services.flippy_scanner_service import FlippyScannerOrchestrator
from services.scan_history_service import ScanHistoryService

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(WORKER_DIR / "worker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("flippy_worker")

# ─── Graceful shutdown ────────────────────────────────────────────────────────
_stop = False

def _handle_signal(sig, frame):
    global _stop
    logger.info(f"Received signal {sig} — finishing current scan then stopping...")
    _stop = True

signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ─── Heartbeat ────────────────────────────────────────────────────────────────

_current_task = "standby"

def _heartbeat_thread_fn():
    """
    Background thread — writes current state to DB every 10s.
    The frontend checks for a write within the last 30s to determine online/offline.
    If the process is killed hard, this thread dies too and the DB goes stale → offline.
    """
    while not _stop:
        try:
            WorkerStatus.ping(task=_current_task)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
        time.sleep(10)


def go_offline():
    try:
        WorkerStatus.go_offline()
        logger.info("Marked worker offline in DB.")
    except Exception as e:
        logger.warning(f"Could not mark worker offline: {e}")


# ─── Schedule window ──────────────────────────────────────────────────────────

def _is_within_schedule(db_settings) -> bool:
    """Return True if the current local time is inside the configured scan window."""
    if not db_settings.schedule_enabled:
        return True
    try:
        import pytz
        from datetime import datetime as dt
        tz = pytz.timezone(db_settings.schedule_timezone)
        now_local = dt.now(tz).time()
        start = db_settings.schedule_start
        end = db_settings.schedule_end
        # Overnight window (e.g. 23:00 → 06:30 crosses midnight)
        if start > end:
            return now_local >= start or now_local <= end
        return start <= now_local <= end
    except Exception as e:
        logger.warning(f"Schedule check failed: {e} — running scan anyway")
        return True


def _next_window_open(db_settings):
    """Return the next UTC-aware datetime when the schedule window opens."""
    import pytz
    from datetime import datetime as dt, timedelta
    tz = pytz.timezone(db_settings.schedule_timezone)
    now_local = dt.now(tz)
    start = db_settings.schedule_start

    today_start = tz.localize(dt.combine(now_local.date(), start))
    if now_local < today_start:
        return today_start.astimezone(pytz.utc)
    # Window already passed today — opens tomorrow
    tomorrow_start = tz.localize(dt.combine(now_local.date() + timedelta(days=1), start))
    return tomorrow_start.astimezone(pytz.utc)


# ─── Scan execution ───────────────────────────────────────────────────────────

def run_scan() -> dict:
    """
    Run one full scan cycle (scrape → triage → deep analysis → notify).

    Always runs with single_run=False so Pass 2 (deep analysis) executes
    automatically. Randomize order is read from ScannerSettings in the DB.
    """
    global _current_task
    db_settings = ScannerSettings.get_settings()
    randomize = db_settings.randomize_order

    started_at = timezone.now()
    scan_record = ScanHistoryService.create_scan_record(
        scan_type="single",
        started_at=started_at,
        randomized=randomize,
    )

    _current_task = "scanning"
    logger.info("Starting scan cycle...")

    try:
        orchestrator = FlippyScannerOrchestrator()
        # single_run=False → Pass 2 (deep analysis) runs automatically
        result = orchestrator.run_all_scanners(randomize=randomize, single_run=False)
        completed_at = timezone.now()

        if result["success"]:
            logger.info(f"Scan complete — {result['message']}")
            logger.info(f"Stats: {result['stats']}")
            ScanHistoryService.update_scan_success(scan_record, completed_at, result["stats"])
        else:
            logger.error(f"Scan returned failure — {result['message']}")
            ScanHistoryService.update_scan_error(scan_record, completed_at, result["message"])

        return result

    except Exception as e:
        completed_at = timezone.now()
        error_msg = f"Scan exception: {e}"
        logger.error(error_msg, exc_info=True)
        ScanHistoryService.update_scan_error(scan_record, completed_at, error_msg)
        return {"success": False, "message": error_msg}

    finally:
        # Poll loop will set the correct state (waiting or standby) on next iteration
        _current_task = "standby"


# ─── Main polling loop ────────────────────────────────────────────────────────

def main_loop():
    """
    Poll ScannerSettings from DB every 5 seconds.
    Run a scan whenever auto_enabled=True and next_scan_at <= now.

    States:
      standby  — online, auto mode OFF
      waiting  — online, auto mode ON, between scans
      scanning — actively running a scan (set by run_scan)
    """
    global _current_task
    logger.info("Worker online. Polling database for scan schedule...")
    logger.info("Website controls: auto mode, interval, and Scan Now button.")

    consecutive_errors = 0

    while not _stop:
        try:
            db_settings = ScannerSettings.get_settings()

            if db_settings.auto_enabled:
                next_scan = db_settings.next_scan_at or timezone.now()

                if timezone.now() >= next_scan:
                    # Apply schedule window only for auto mode (not manual "Scan Now" triggers)
                    if db_settings.mode == 'auto' and not _is_within_schedule(db_settings):
                        next_window = _next_window_open(db_settings)
                        db_settings.next_scan_at = next_window
                        db_settings.save(update_fields=['next_scan_at'])
                        _current_task = "waiting"
                        import pytz
                        tz = pytz.timezone(db_settings.schedule_timezone)
                        window_local = next_window.astimezone(tz).strftime('%I:%M %p')
                        logger.info(
                            f"Outside schedule window — next scan at {window_local} MST"
                        )
                        if not _stop:
                            time.sleep(5)
                        continue
                    logger.info(
                        f"Scan triggered — auto_enabled=True, "
                        f"interval={db_settings.interval_minutes}m"
                    )
                    result = run_scan()

                    if result.get("success"):
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                        logger.warning(f"Scan failed ({consecutive_errors} consecutive errors)")
                else:
                    remaining = int((next_scan - timezone.now()).total_seconds())
                    _current_task = "waiting"
                    logger.info(f"Waiting — next scan in {remaining}s "
                                f"(auto_enabled=True, interval={db_settings.interval_minutes}m)")
            else:
                _current_task = "standby"
                logger.info("Standby — auto mode is OFF (enable via website Control page)")

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in poll loop: {e}", exc_info=True)

        if _stop:
            break

        # Poll every 5 seconds for fast response to website triggers
        if not _stop:
            time.sleep(5)

    logger.info("Poll loop exited cleanly.")
    go_offline()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FLIPPY Worker — DB-controlled scanner")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Debug: run one scan immediately then exit (ignores DB settings)"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("FLIPPY Worker starting")
    logger.info(f"  Backend dir : {BACKEND_DIR}")
    logger.info(f"  Worker dir  : {WORKER_DIR}")
    logger.info(f"  Mode        : {'single scan (debug)' if args.once else 'DB-controlled loop'}")
    logger.info("=" * 60)

    # Clear any stale state from a previous killed session
    go_offline()

    # Start background heartbeat thread (daemon so it dies with the process)
    hb_thread = threading.Thread(target=_heartbeat_thread_fn, daemon=True, name="heartbeat")
    hb_thread.start()
    logger.info("Heartbeat thread started (10s interval, 30s staleness threshold)")

    if args.once:
        logger.info("--once flag: running one scan immediately (Pass 2 included)")
        result = run_scan()
        go_offline()
        sys.exit(0 if result.get("success") else 1)
    else:
        main_loop()


if __name__ == "__main__":
    main()
