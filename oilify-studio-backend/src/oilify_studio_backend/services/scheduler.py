import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from oilify_studio_backend.config import get_settings
from oilify_studio_backend.db import get_database_manager
from oilify_studio_backend.services.price import ingest_prices


logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def run_price_job() -> None:
    logger.info("30-min price scheduler job started")
    db = get_database_manager().get_session()
    try:
        rows = ingest_prices(db)
        logger.info("30-min price scheduler upserted %s rows", len(rows))
    except Exception:
        logger.exception("30-min price scheduler job failed")
    finally:
        db.close()
        logger.debug("30-min price scheduler database session closed")


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled by configuration")
        return
    if _scheduler is not None and _scheduler.running:
        logger.debug("Price scheduler already running")
        return

    logger.info("Starting 30-min price scheduler")
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_price_job,
        IntervalTrigger(minutes=30),
        id="price-job",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("30-min price scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        logger.debug("Price scheduler stop requested but no scheduler is active")
        return
    if _scheduler.running:
        logger.info("Stopping price scheduler")
        _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.debug("Price scheduler cleared")
