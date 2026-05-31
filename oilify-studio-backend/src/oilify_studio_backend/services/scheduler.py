import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from oilify_studio_backend.config import get_settings
from oilify_studio_backend.db import get_database_manager
from oilify_studio_backend.services.oil_price import ingest_daily_oil_prices


logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _parse_hours(raw_hours: str) -> str:
    parts = [hour.strip() for hour in raw_hours.split(",") if hour.strip()]
    return ",".join(parts) if parts else "0,8,16"


def run_oil_price_job() -> None:
    db = get_database_manager().get_session()
    try:
        rows = ingest_daily_oil_prices(db)
        logger.info("Oil price scheduler upserted %s rows", len(rows))
    except Exception:
        logger.exception("Oil price scheduler job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled by configuration")
        return
    if _scheduler is not None and _scheduler.running:
        return

    hours = _parse_hours(settings.OIL_PRICE_SCHEDULE_HOURS)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_oil_price_job,
        CronTrigger(hour=hours, minute=0),
        id="oilify-oil-price-job",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Oil price scheduler started for UTC hours: %s", hours)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
