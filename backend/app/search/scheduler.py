import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app import db
from app.schemas import Schedule
from app.search import runner

log = logging.getLogger(__name__)

JOB_ID = "busqueda-programada"
scheduler = AsyncIOScheduler()


async def run_scheduled() -> None:
    if runner.is_running():
        log.info("Búsqueda programada omitida: ya hay una en curso")
        return
    async with db.SessionLocal() as session:
        run = await runner.create_run(session, "programada")
    await runner.execute_run(run.id)


def apply_schedule(schedule: Schedule) -> None:
    if scheduler.get_job(JOB_ID):
        scheduler.remove_job(JOB_ID)
    if not schedule.enabled:
        return
    trigger = CronTrigger(
        day_of_week=schedule.weekday if schedule.frequency == "weekly" else "*",  # 0 = lunes
        hour=schedule.hour,
        minute=0,
        timezone=schedule.timezone,
    )
    scheduler.add_job(run_scheduled, trigger, id=JOB_ID, misfire_grace_time=3600, coalesce=True)


def next_run_at() -> datetime | None:
    job = scheduler.get_job(JOB_ID)
    return getattr(job, "next_run_time", None) if job else None
