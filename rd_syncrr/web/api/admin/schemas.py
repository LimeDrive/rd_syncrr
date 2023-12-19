"""Schemas for the trigger API."""
from datetime import datetime

from pydantic import BaseModel, Field


class UpdateResponse(BaseModel):
    message: str
    time: datetime = Field(default_factory=datetime.now)


class TestedHash(BaseModel):
    filename: str
    filesize: int
