import os
from asyncio import current_task
from collections.abc import Sequence
from typing import Any, List, Optional  # noqa: UP035

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dependencies import get_db_session
from rd_syncrr.services.media_db.models.media_model import (
    RadarrMovieModel,
    SonarrEpisodeModel,
    SymlinkModel,
    TorrentFileModel,
    TorrentModel,
)
from rd_syncrr.settings import settings


class MediaDAO:
    """Class for accessing torrent table."""

    def __init__(self, session: AsyncSession = Depends(get_db_session)):  # noqa: B008
        self.session = session

    @classmethod
    async def create(cls) -> "MediaDAO":
        """Create a new instance of MediaDAO with an async session."""
        if settings.environment == "dev":
            db_path = "rd_syncrr_media_dev.db"
        else:
            db_path = os.path.join(settings.media_db_location, "rd_syncrr_media.db")

        db_path = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(db_path)
        async_session = async_scoped_session(
            async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
            ),
            scopefunc=current_task,
        )
        session = async_session()
        return cls(session=session)

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()

    async def __aenter__(self) -> "MediaDAO":
        """Enter the asynchronous context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Exit the asynchronous context manager."""
        await self.close()

    async def create_torrent_model(
        self,
        hash: str,  # noqa: A002
        id: str,  # noqa: A002
        filename: str,
    ) -> None:
        """
        Add single torrent to session.
        :param hash: hash of torrent. nullable=False
        :param id: ID of torrent. nullable=False
        :param filename: filename of torrent. nullable=False
        """
        try:
            torrent_model = TorrentModel(hash=hash, id=id, filename=filename)
            self.session.add(torrent_model)
            await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while adding torrent to database: {e!s}")
            await self.session.rollback()

    async def create_symlink_model(
        self,
        symlink_data: dict[str, Any],
        file_id: Optional[str] = None,
    ) -> None:
        """
        Add single dummy to session.
        :param data of a symlink.
        dict:
            target: target path of symlink. nullable=False
            target_filename: target filename of symlink. nullable=False
            destination: destination path of symlink. nullable=False
            destination_filename: destination filename of symlink. nullable=False
            relationship: rd_file: Mapped[Optional["TorrentFileModel"]]
            relationship: plex: Mapped[Optional["PlexInfoModel"]]
        """
        try:
            if file_id is not None:
                torrent_file = await self.session.get(TorrentFileModel, file_id)
                if torrent_file:
                    symlink_data["rd_file"] = torrent_file
            symlink_model = SymlinkModel(**symlink_data)
            self.session.add(symlink_model)
            await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while adding symlink to database: {e!s}")
            await self.session.rollback()

    async def create_radarr_movie_model(self, movie_data: dict[str, Any]) -> None:
        """
        Add single movie to session.
        :param movie_data: Data of the movie.
        """
        try:
            movie_model = RadarrMovieModel(**movie_data)
            self.session.add(movie_model)
            await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while adding movie to database: {e!s}")
            await self.session.rollback()

    async def create_sonarr_episode_model(self, episode_data: dict[str, Any]) -> None:
        """
        Add single episode to session.
        :param episode_data: Data of the episode.
        """
        try:
            episode_model = SonarrEpisodeModel(**episode_data)
            self.session.add(episode_model)
            await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while adding episode to database: {e!s}")
            await self.session.rollback()

    async def create_file_model(
        self,
        torrent_id: str,
        file_data: dict[str, Any],
    ) -> None:
        """
        Add single file to torrent.
        :param torrent_id: ID of the torrent model.
        :param file_data: Data of the torrent file.
        """
        try:
            torrent_model = await self.session.get(TorrentModel, torrent_id)
            if torrent_model:
                torrent_file = TorrentFileModel(**file_data, torrent=torrent_model)
                self.session.add(torrent_file)
                await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while adding file to torrent: {e!s}")
            await self.session.rollback()

    async def get_all_torrents(
        self,
        limit: Optional[int] = 50,
        offset: Optional[int] = 0,
    ) -> Sequence[TorrentModel]:
        """
        Get all torrents from the database.
        :param limit: The limit of results to return.
        :param offset: The offset of results to return.
        :return: List of torrent models.
        """
        query = select(TorrentModel).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_torrents_hashes(self) -> Optional[list[str]]:
        """
        Get a list of all torrent hashes.
        :return: List of torrent hashes or None if the database is empty.
        """
        query = select(TorrentModel.hash)
        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return None
        return [row[0] for row in rows]

    async def get_torrent(
        self,
        hash: Optional[str] = None,  # noqa: A002
        torrent_id: Optional[int] = None,
    ) -> Optional[TorrentModel]:
        """
        Get specific torrent model.
        :param hash: hash of torrent instance.
        :param torrent_id: ID of torrent instance.
        :return: torrent model or None if not found.
        """
        query = select(TorrentModel)
        if hash:
            query = query.where(TorrentModel.hash == hash)
        if torrent_id:
            query = query.where(TorrentModel.id == torrent_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_file_by_id(self, file_id: str) -> Optional[TorrentFileModel]:
        """
        Get a specific torrent file by ID.
        :param file_id: ID of the torrent file.
        :return: Torrent file model or None if not found.
        """
        query = select(TorrentFileModel).where(TorrentFileModel.id == file_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_files_unlinked_media(self) -> Optional[Sequence[TorrentFileModel]]:
        """
        Get all torrent files that are not linked to any torrents.
        :return: List of torrent file models.
        """
        query = select(TorrentFileModel).where(
            TorrentFileModel.radarr_id == None,  # noqa: E711
            TorrentFileModel.sonarr_id == None,  # noqa: E711
            TorrentFileModel.symlink_id != None,  # noqa: E711
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_files_unlinked_symlink(self) -> Optional[Sequence[TorrentFileModel]]:
        """
        Get all torrent files that are not linked to any torrents.
        :return: List of torrent file models.
        """
        query = select(TorrentFileModel).where(
            TorrentFileModel.symlink_id == None,  # noqa: E711
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_files_from_torrent_id(
        self,
        torrent_id: str,
    ) -> Sequence[TorrentFileModel]:
        """
        Get all torrent files for a torrent.
        :param torrent_id: ID of the torrent model.
        :return: List of torrent file models.
        """
        query = select(TorrentFileModel).where(
            TorrentFileModel.torrent_id == torrent_id,
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_torrent_files_filename_dict(self) -> Optional[dict[str, str]]:
        """
        Get a dictionary of all torrent files with filename.
        :return: Dictionary of torrent files.
        """
        result = await self.session.execute(
            select(TorrentFileModel.id, TorrentFileModel.path),
        )
        rows = result.all()
        if not rows:
            return None
        return {os.path.basename(filename): file_id for file_id, filename in rows}

    async def get_all_torrents_files(self) -> Sequence[TorrentFileModel]:
        """
        Get all torrent files.
        :return: List of torrent file models.
        """
        query = select(TorrentFileModel)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_symlink_by_id(self, symlink_id: str) -> Optional[SymlinkModel]:
        """
        Get a specific symlink by ID.
        :param symlink_id: ID of the symlink.
        :return: Symlink model or None if not found.
        """
        query = select(SymlinkModel).where(SymlinkModel.id == symlink_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_symlink_by_target(self, target: str) -> Optional[SymlinkModel]:
        """
        Get a specific symlink by target.
        :param target: target of the symlink.
        :return: Symlink model or None if not found.
        """
        query = select(SymlinkModel).where(SymlinkModel.target == target)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_symlinks(self) -> Optional[Sequence[SymlinkModel]]:
        """
        Get all symlink models.
        :return: List of symlink models.
        """
        query = select(SymlinkModel)
        result = await self.session.execute(query)
        if not result.scalars().all():
            return None
        return result.scalars().all()

    async def get_symlink_destination_filename_dict(self) -> Optional[dict[str, str]]:
        """
        Get a dictionary of all symlinks with destination filename.
        :return: Dictionary of symlinks.
        """
        result = await self.session.execute(
            select(SymlinkModel.id, SymlinkModel.destination_filename),
        )
        rows = result.all()
        if not rows:
            return None
        return {
            destination_filename: symlink_id
            for symlink_id, destination_filename in rows
        }

    async def get_symlink_target_filename_dict(self) -> Optional[dict[str, str]]:
        """
        Get a dictionary of all symlinks with target filename.
        :return: Dictionary of symlinks.
        """
        result = await self.session.execute(
            select(SymlinkModel.id, SymlinkModel.target_filename),
        )
        rows = result.all()
        if not rows:
            return None
        return {target_filename: symlink_id for symlink_id, target_filename in rows}

    async def get_sonarr_episodes_file_id(self) -> Optional[List[str]]:
        """
        Get a list of all Sonarr episodes file ID.
        :return: List of Sonarr episodes file ID.
        """
        query = select(SonarrEpisodeModel.episodefileId)
        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return None
        return [row[0] for row in rows]

    async def get_radarr_movies_file_id(self) -> Optional[List[str]]:
        """
        Get a list of all Radarr movies file ID.
        :return: List of Radarr movies file ID.
        """
        query = select(RadarrMovieModel.fileId)
        result = await self.session.execute(query)
        rows = result.all()
        if not rows:
            return None
        return [row[0] for row in rows]

    async def get_radarr_info_by_id(
        self,
        id: str,  # noqa: A002
    ) -> Optional[RadarrMovieModel]:
        """
        Get a specific Radarr movie by ID.
        :param id: ID of the Radarr movie.
        :return: Radarr movie model or None if not found.
        """
        query = select(RadarrMovieModel).where(RadarrMovieModel.id == id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_sonarr_info_by_id(
        self,
        id: str,  # noqa: A002
    ) -> Optional[SonarrEpisodeModel]:
        """
        Get a specific Sonarr episode by ID.
        :param id: ID of the Sonarr episode.
        :return: Sonarr episode model or None if not found.
        """
        query = select(SonarrEpisodeModel).where(SonarrEpisodeModel.id == id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def check_radarr_path_exists(self, path: str) -> Optional[RadarrMovieModel]:
        """
        Check if a Radarr path exists in the database.
        :param path: Path to check.
        :return: Radarr movie model or None if not found.
        """
        query = select(RadarrMovieModel).where(RadarrMovieModel.path == path)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def check_sonarr_path_exists(self, path: str) -> Optional[SonarrEpisodeModel]:
        """
        Check if a Sonarr path exists in the database.
        :param path: Path to check.
        :return: Sonarr episode model or None if not found.
        """
        query = select(SonarrEpisodeModel).where(SonarrEpisodeModel.path == path)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def link_file_to_radarr(self, radarr_id: str, file_id: str) -> None:
        """
        Link a torrent to a Radarr movie.
        :param radarr_id: ID of the Radarr movie.
        :param torrent_id: ID of the torrent.
        """
        try:
            radarr_movie = await self.session.get(RadarrMovieModel, radarr_id)
            torrent_file = await self.session.get(TorrentFileModel, file_id)
            if radarr_movie and torrent_file:
                torrent_file.radarr_info = radarr_movie
                await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while linking torrent to Radarr: {e!s}")
            await self.session.rollback()

    async def link_file_to_sonarr(self, sonarr_id: str, file_id: str) -> None:
        """
        Link a torrent to a Sonarr episode.
        :param sonarr_id: ID of the Sonarr episode.
        :param torrent_id: ID of the torrent.
        """
        try:
            sonarr_episode = await self.session.get(SonarrEpisodeModel, sonarr_id)
            torrent_file = await self.session.get(TorrentFileModel, file_id)
            if sonarr_episode and torrent_file:
                torrent_file.sonarr_info = sonarr_episode
                await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while linking torrent to Sonarr: {e!s}")
            await self.session.rollback()

    async def link_radarr_to_symlink(self, symlink_id: str, radarr_id: str) -> None:
        """
        Link a Radarr movie to a symlink.
        :param symlink_id: ID of the symlink.
        :param file_id: ID of the torrent file.
        """
        try:
            symlink = await self.session.get(SymlinkModel, symlink_id)
            radarr = await self.session.get(RadarrMovieModel, radarr_id)
            if symlink and radarr:
                symlink.radarr_info = radarr
                await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while linking Radarr to symlink: {e!s}")
            await self.session.rollback()

    async def link_sonarr_to_symlink(self, symlink_id: str, sonarr_id: str) -> None:
        """
        Link a Sonarr episode to a symlink.
        :param symlink_id: ID of the symlink.
        :param file_id: ID of the torrent file.
        """
        try:
            symlink = await self.session.get(SymlinkModel, symlink_id)
            sonarr = await self.session.get(SonarrEpisodeModel, sonarr_id)
            if symlink and sonarr:
                symlink.sonarr_info = sonarr
                await self.session.commit()
        except Exception as e:
            logger.error(f"An error occurred while linking Sonarr to symlink: {e!s}")
            await self.session.rollback()
