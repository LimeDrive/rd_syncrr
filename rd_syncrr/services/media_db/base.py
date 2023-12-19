from sqlalchemy.orm import DeclarativeBase

from rd_syncrr.services.media_db.meta import meta


class Base(DeclarativeBase):
    """Base for all models."""

    metadata = meta
