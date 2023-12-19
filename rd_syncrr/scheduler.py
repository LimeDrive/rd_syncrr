"""Scheduler for the syncrr program."""

from typing import List  # noqa: UP035

from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.settings import settings
from rd_syncrr.tasks import (
    process_mediainfo,
    process_torrents,
)


def init_scheduler() -> AsyncIOScheduler:
    """Initialize the scheduler with SQLite jobstore.

    Returns:
        The initialized scheduler object.
    """
    jobstore = {
        "default": SQLAlchemyJobStore(
            url="sqlite:///rd_syncrr_jobs.db",
            tablename="default_jobs",
        ),
    }
    job_defaults = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 20,
    }

    scheduler = AsyncIOScheduler(jobstores=jobstore, job_defaults=job_defaults)
    return scheduler


async def database_update_job() -> None:
    """Initialize database update job."""
    async with await MediaDAO.create() as dao:
        logger.info("Updating database...")
        await process_torrents(dao)
        await process_mediainfo(dao)
        await dao.close()
        logger.info("Database updated.")


async def _trigger_database_update_job(
    scheduler: AsyncIOScheduler,
    jobs: List[Job],
) -> None:
    """Trigger the database update job.

    Args:
        scheduler: The scheduler object to add the jobs to.
    """
    for job in jobs:
        if job.name == "database_update_job":
            return
    scheduler.add_job(
        database_update_job,
        "interval",
        minutes=settings.sched_db_update_interval,
        name="database_update_job",
    )


async def init_jobs(scheduler: AsyncIOScheduler) -> None:
    """Initialize the jobs and add them to the scheduler.

    Args:
        scheduler: The scheduler object to add the jobs to.
    """
    try:
        jobs = scheduler.get_jobs(jobstore="default")

        await _trigger_database_update_job(scheduler, jobs)
    except Exception as e:
        logger.error(f"An error occurred while initializing the jobs: {e!s}")
        return
