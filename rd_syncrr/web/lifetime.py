import os
from collections.abc import Awaitable
from typing import Callable

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rd_syncrr.scheduler import init_jobs, init_scheduler
from rd_syncrr.services.media_db.meta import meta
from rd_syncrr.services.media_db.models import load_all_models
from rd_syncrr.settings import settings

scheduler = init_scheduler()


def _set_media_db_path() -> str:
    """Set the path to the database."""
    if settings.environment == "dev":
        db_path = "rd_syncrr_media_dev.db"
    else:
        db_path = os.path.join(settings.media_db_location, "rd_syncrr_media.db")

    db_path = f"sqlite+aiosqlite:///{db_path}"
    return db_path


db_path: str = _set_media_db_path()


def _setup_db(app: FastAPI) -> None:  # pragma: no cover
    """
    Creates connection to the database.

    This function creates SQLAlchemy engine instance,
    session_factory for creating sessions
    and stores them in the application's state property.

    :param app: fastAPI application.
    """
    engine = create_async_engine(db_path, echo=settings.media_db_echo)
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory


async def _create_tables() -> None:  # pragma: no cover
    """Populates tables in the database."""
    load_all_models()
    engine = create_async_engine(db_path)
    async with engine.begin() as connection:
        await connection.run_sync(meta.create_all)
    await engine.dispose()


def register_startup_event(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:  # pragma: no cover
    """
    Actions to run on application startup.

    This function uses fastAPI app to store data
    in the state, such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    @app.on_event("startup")
    async def _startup() -> None:
        app.middleware_stack = None
        _setup_db(app)
        await _create_tables()
        scheduler.start()
        await init_jobs(scheduler)
        app.middleware_stack = app.build_middleware_stack()
        pass

    return _startup


def register_shutdown_event(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:  # pragma: no cover
    """
    Actions to run on application's shutdown.

    :param app: fastAPI application.
    :return: function that actually performs actions.
    """

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        scheduler.shutdown()
        await app.state.db_engine.dispose()
        pass

    return _shutdown
