import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from oilify_studio_backend.config import get_settings
from oilify_studio_backend.db import get_database_manager
from oilify_studio_backend.services.price import ingest_daily_prices


logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _parse_hours(raw_hours: str) -> str:
    parts = [hour.strip() for hour in raw_hours.split(",") if hour.strip()]
    logger.debug("Parsed scheduler hours raw=%s parsed=%s", raw_hours, parts)
    return ",".join(parts) if parts else "0,8,16"


def run_price_job() -> None:
    logger.info("Price scheduler job started")
    db = get_database_manager().get_session()
    try:
        rows = ingest_daily_prices(db)
        logger.info("Price scheduler upserted %s rows", len(rows))
    except Exception:
        logger.exception("Price scheduler job failed")
    finally:
        db.close()
        logger.debug("Price scheduler database session closed")


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled by configuration")
        return
    if _scheduler is not None and _scheduler.running:
        logger.debug("Price scheduler already running")
        return

    hours = _parse_hours(settings.PRICE_SCHEDULE_HOURS)
    logger.info("Starting price scheduler for UTC hours=%s", hours)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_price_job,
        CronTrigger(hour=hours, minute=0),
        id="price-job",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Price scheduler started for UTC hours: %s", hours)


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
