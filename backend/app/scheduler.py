"""
Phase 9 — Background Scheduler

A simple threading-based background task that checks for expired auctions
every INTERVAL_SECONDS and closes them automatically.

Uses only Python's stdlib `threading` module — no Celery, no Redis, no APScheduler.

Lifecycle:
  - start_scheduler()  → called once on FastAPI startup
  - stop_scheduler()   → called once on FastAPI shutdown
"""

import threading
import logging
import time

from app.config.database import SessionLocal
from app.services.auction_end_service import close_expired_auctions

logger = logging.getLogger(__name__)

# How often the scheduler wakes up (seconds)
INTERVAL_SECONDS = 60

# Internal handle to the background thread
_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _run_loop():
    """Main loop executed in the background thread."""
    logger.info("Auction scheduler started (interval: %ds)", INTERVAL_SECONDS)

    while not _stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                summary = close_expired_auctions(db)
                if summary["checked"] > 0:
                    logger.info(
                        "Scheduler run: checked=%d, sold=%d, ended_no_bids=%d, "
                        "ended_reserve_not_met=%d, errors=%d",
                        summary["checked"], summary["sold"],
                        summary["ended_no_bids"], summary["ended_reserve_not_met"],
                        summary["errors"],
                    )
            finally:
                db.close()
        except Exception as exc:
            logger.error("Scheduler error: %s", exc, exc_info=True)

        # Wait for next interval (or stop signal)
        _stop_event.wait(timeout=INTERVAL_SECONDS)

    logger.info("Auction scheduler stopped.")


def start_scheduler():
    """Start the background auction-ending scheduler thread."""
    global _scheduler_thread, _stop_event

    _stop_event.clear()
    _scheduler_thread = threading.Thread(
        target=_run_loop,
        name="AuctionScheduler",
        daemon=True,          # dies when main process dies
    )
    _scheduler_thread.start()
    logger.info("Auction scheduler thread launched.")


def stop_scheduler():
    """Gracefully stop the background scheduler thread."""
    global _scheduler_thread
    _stop_event.set()
    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=5)
    logger.info("Auction scheduler shut down.")
