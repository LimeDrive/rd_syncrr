from datetime import datetime
from typing import List  # noqa: UP035

from pydantic import BaseModel


class SonarrEpisodeModelDTO(BaseModel):
    mediaType: str
    serieTitle: str
    year: int | None
    seasonNumber: int
    episodeTitle: str | None
    episodeNumber: int
    releaseGroup: str | None
    tvdbId: int | None
    imdbId: str | None
    tvMazeId: int | None
    genres: List[str] | None
    quality: str | None
    resolution: int | None
    languages: List[str] | None


class RadarrMovieModelDTO(BaseModel):
    mediaType: str
    title: str
    year: int
    releaseGroup: str | None
    tmdbId: int | None
    imdbId: str | None
    genres: List[str] | None
    quality: str | None
    resolution: int | None
    languages: List[str] | None


class TorrentFileModelDTO(BaseModel):
    """Torrent file model."""

    path: str
    bytes: int  # noqa: A003
    added: datetime
    info: SonarrEpisodeModelDTO | RadarrMovieModelDTO | None


class TorrentModelDTO(BaseModel):
    """Torrent model."""

    torrent: str
    id: str  # noqa: A003
    hash: str  # noqa: A003
    added: datetime
    files: List[TorrentFileModelDTO]
