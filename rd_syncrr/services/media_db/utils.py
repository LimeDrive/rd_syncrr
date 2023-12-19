import os

from rd_syncrr.settings import settings


async def create_database() -> None:
    """Create a database."""


async def drop_database() -> None:
    """Drop current database."""
    if settings.media_db_location:
        path = os.path.join(settings.media_db_location, "rd_syncrr_media.db")
        os.remove(path)
