"""Tests for the Oilify price scheduler."""

from unittest.mock import MagicMock

from oilify_studio_backend.services import scheduler as scheduler_module
from oilify_studio_backend.services.scheduler import run_price_job, start_scheduler, stop_scheduler


class _FakeScheduler:
    def __init__(self) -> None:
        self.running = False
        self.started = False
        self.shutdown_called = False
        self.jobs: list[dict[str, object]] = []

    def add_job(self, func, trigger, id: str, replace_existing: bool) -> None:
        self.jobs.append(
            {
                "func": func,
                "trigger": trigger,
                "id": id,
                "replace_existing": replace_existing,
            }
        )

    def start(self) -> None:
        self.started = True
        self.running = True

    def shutdown(self, wait: bool = False) -> None:
        self.shutdown_called = True
        self.running = False


def test_start_scheduler_is_disabled_when_configured_off(mocker) -> None:
    scheduler_module._scheduler = None
    mocker.patch(
        "oilify_studio_backend.services.scheduler.get_settings",
        return_value=MagicMock(SCHEDULER_ENABLED=False),
    )

    start_scheduler()

    assert scheduler_module._scheduler is None


def test_start_scheduler_registers_job_and_stop_scheduler_shuts_down(mocker) -> None:
    scheduler_module._scheduler = None
    fake_scheduler = _FakeScheduler()
    mocker.patch(
        "oilify_studio_backend.services.scheduler.AsyncIOScheduler",
        return_value=fake_scheduler,
    )
    mocker.patch(
        "oilify_studio_backend.services.scheduler.get_settings",
        return_value=MagicMock(SCHEDULER_ENABLED=True),
    )

    start_scheduler()

    assert scheduler_module._scheduler is fake_scheduler
    assert fake_scheduler.started is True
    assert len(fake_scheduler.jobs) == 1
    from apscheduler.triggers.interval import IntervalTrigger
    assert isinstance(fake_scheduler.jobs[0]["trigger"], IntervalTrigger)
    assert fake_scheduler.jobs[0]["trigger"].interval.seconds == 1800  # 30 min

    stop_scheduler()

    assert scheduler_module._scheduler is None
    assert fake_scheduler.shutdown_called is True


def test_run_price_job_closes_session(mocker) -> None:
    session = MagicMock()
    manager = MagicMock()
    manager.get_session.return_value = session
    mocker.patch(
        "oilify_studio_backend.services.scheduler.get_database_manager",
        return_value=manager,
    )
    mocker.patch(
        "oilify_studio_backend.services.scheduler.ingest_prices",
        return_value=[MagicMock(), MagicMock()],
    )

    run_price_job()

    session.close.assert_called_once()