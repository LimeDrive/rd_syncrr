from datetime import datetime

from pydantic import BaseModel, validator


class Torrent(BaseModel):
    """Torrent model."""

    filename: str
    id: str  # noqa: A003
    hash: str  # noqa: A003
    added: datetime

    @validator("hash")
    def validate_hash(cls, v: str) -> str:
        if len(v) != 40:
            raise ValueError("Invalid hash length")
        return v


class Torrents(BaseModel):
    """Torrents model."""

    torrents: list[Torrent]
