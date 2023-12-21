import uuid
from datetime import datetime
from typing import Any, List  # noqa: UP035

import shortuuid
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, event
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Optional, String

from ..base import Base


class TorrentModel(Base):
    """Model for torrent"""

    __tablename__ = "rd_torrents"

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)  # noqa: A003
    hash: Mapped[str] = mapped_column(  # noqa: A003
        String(length=40),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(length=400), nullable=False)
    added: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    files: Mapped[Optional[list["TorrentFileModel"]]] = relationship(
        "TorrentFileModel",
        back_populates="torrent",
    )


class RadarrMovieModel(Base):
    """Model for Radarr movie container."""

    __tablename__ = "radarr_movies"

    id: Mapped[str] = mapped_column(  # noqa: A003
        String(length=22),
        primary_key=True,
        nullable=False,
        default=lambda: shortuuid.ShortUUID().random(length=18),
    )
    added: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    mediaType: Mapped[str] = mapped_column(String, nullable=False)
    movieId: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    originalTitle: Mapped[str] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    releaseGroup: Mapped[str] = mapped_column(String, nullable=True)
    imdbId: Mapped[str] = mapped_column(String, nullable=True)
    tmdbId: Mapped[int] = mapped_column(Integer, nullable=True)
    genres: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    quality: Mapped[str] = mapped_column(String, nullable=True)
    resolution: Mapped[int] = mapped_column(Integer, nullable=True)
    languages: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    originalFilePath: Mapped[str] = mapped_column(String, nullable=True)
    relativePath: Mapped[str] = mapped_column(String, nullable=True)
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    fileId: Mapped[int] = mapped_column(Integer, nullable=True)
    symlink_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("local_symlinks.id"),
    )

    # Update auto on insert in SymLinkModel
    torrent_file: Mapped[Optional["TorrentFileModel"]] = relationship(
        "TorrentFileModel",
        back_populates="radarr_info",
        uselist=False,
    )
    symlink: Mapped[Optional["SymlinkModel"]] = relationship(
        "SymlinkModel",
        back_populates="radarr_info",
        uselist=False,
        foreign_keys="RadarrMovieModel.symlink_id",
    )


class SonarrEpisodeModel(Base):
    """Model for Sonarr serie container."""

    __tablename__ = "sonarr_series"

    id: Mapped[str] = mapped_column(  # noqa: A003
        String(length=22),
        primary_key=True,
        nullable=False,
        default=lambda: shortuuid.ShortUUID().random(length=18),
    )
    added: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    mediaType: Mapped[str] = mapped_column(String, nullable=False)
    serieId: Mapped[int] = mapped_column(Integer, nullable=False)
    serieTitle: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    seasonNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    episodeTitle: Mapped[str] = mapped_column(String, nullable=True)
    episodeNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    releaseGroup: Mapped[str] = mapped_column(String, nullable=True)
    tvdbId: Mapped[int] = mapped_column(String, nullable=False)
    imdbId: Mapped[str] = mapped_column(String, nullable=True)
    tvMazeId: Mapped[int] = mapped_column(Integer, nullable=True)
    genres: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    quality: Mapped[str] = mapped_column(String, nullable=True)
    resolution: Mapped[int] = mapped_column(Integer, nullable=True)
    languages: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    relativePath: Mapped[str] = mapped_column(String, nullable=True)
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    episodefileId: Mapped[int] = mapped_column(Integer, nullable=True)
    episodeId: Mapped[int] = mapped_column(Integer, nullable=True)
    symlink_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("local_symlinks.id"),
    )

    # Update auto on insert in SymLinkModel
    torrent_file: Mapped[Optional["TorrentFileModel"]] = relationship(
        "TorrentFileModel",
        back_populates="sonarr_info",
    )
    symlink: Mapped[Optional["SymlinkModel"]] = relationship(
        "SymlinkModel",
        back_populates="sonarr_info",
        uselist=False,
        foreign_keys="SonarrEpisodeModel.symlink_id",
    )


class SymlinkModel(Base):
    """Model for symlink"""

    __tablename__ = "local_symlinks"

    id: Mapped[str] = mapped_column(  # noqa: A003
        String(length=12),
        primary_key=True,
        nullable=False,
        default=lambda: shortuuid.ShortUUID().random(length=12),
    )
    added: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    target: Mapped[str] = mapped_column(String, nullable=False, index=True)
    target_filename: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    destination_filename: Mapped[str] = mapped_column(String, nullable=False)

    rd_file: Mapped["TorrentFileModel"] = relationship(
        "TorrentFileModel",
        back_populates="symlink",
    )
    sonarr_info: Mapped[Optional["SonarrEpisodeModel"]] = relationship(
        "SonarrEpisodeModel",
        back_populates="symlink",
    )
    radarr_info: Mapped[Optional["RadarrMovieModel"]] = relationship(
        "RadarrMovieModel",
        back_populates="symlink",
    )


class TorrentFileModel(Base):
    """Model files in torrent."""

    __tablename__ = "rd_torrents_files"

    id: Mapped[str] = mapped_column(  # noqa: A003
        String(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    path: Mapped[str] = mapped_column(String(length=600), nullable=False)
    bytes: Mapped[int] = mapped_column(Integer, nullable=False)  # noqa: A003
    added: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    torrent_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("rd_torrents.id"),
    )
    symlink_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("local_symlinks.id"),
    )
    radarr_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("radarr_movies.id"),
    )
    sonarr_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("sonarr_series.id"),
    )

    torrent: Mapped[Optional["TorrentModel"]] = relationship(
        "TorrentModel",
        back_populates="files",
        foreign_keys="TorrentFileModel.torrent_id",
    )
    symlink: Mapped[Optional["SymlinkModel"]] = relationship(
        "SymlinkModel",
        back_populates="rd_file",
        uselist=False,
        foreign_keys="TorrentFileModel.symlink_id",
    )
    radarr_info: Mapped[Optional["RadarrMovieModel"]] = relationship(
        "RadarrMovieModel",
        back_populates="torrent_file",
        uselist=False,
        foreign_keys="TorrentFileModel.radarr_id",
    )
    sonarr_info: Mapped[Optional["SonarrEpisodeModel"]] = relationship(
        "SonarrEpisodeModel",
        back_populates="torrent_file",
        uselist=False,
        foreign_keys="TorrentFileModel.sonarr_id",
    )


def update_torrent_file(mapper: Any, connection: Any, target: SymlinkModel) -> None:
    session = Session(bind=connection)
    if target.radarr_info:
        radarr_movie = (
            session.query(RadarrMovieModel).filter_by(id=target.radarr_info.id).first()
        )
        if radarr_movie:
            radarr_movie.torrent_file = target.rd_file
            session.commit()
    elif target.sonarr_info:
        sonarr_episode = (
            session.query(SonarrEpisodeModel)
            .filter_by(id=target.sonarr_info.id)
            .first()
        )
        if sonarr_episode:
            sonarr_episode.torrent_file = target.rd_file
            session.commit()


event.listen(SymlinkModel, "after_insert", update_torrent_file)
event.listen(SymlinkModel, "after_update", update_torrent_file)

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import sessionmaker

# # Create a sessionmaker for async sessions
# AsyncSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# async def update_torrent_file(mapper, connection, target: SymlinkModel):
#     async with AsyncSession(engine) as session:
#         if target.radarr_info:
#             radarr_movie = (
#                 await session.query(RadarrMovieModel).filter_by(id=target.radarr_info.id).first()
#             )
#             if radarr_movie:
#                 radarr_movie.torrent_file = target.rd_file
#                 await session.commit()
#         elif target.sonarr_info:
#             sonarr_episode = (
#                 await session.query(SonarrEpisodeModel)
#                 .filter_by(id=target.sonarr_info.id)
#                 .first()
#             )
#             if sonarr_episode:
#                 sonarr_episode.torrent_file = target.rd_file
#                 await session.commit()

# event.listen(SymlinkModel, "after_insert", update_torrent_file, propagate=True)
# event.listen(SymlinkModel, "after_update", update_torrent_file, propagate=True)
