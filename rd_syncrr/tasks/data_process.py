"""Update or write the JSON file with the given data."""

import json
import os
from typing import Any, Dict, List, Sequence  # noqa: UP035

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.services.media_db.models.media_model import TorrentFileModel
from rd_syncrr.settings import settings


async def _list_torrents_to_json(
    data: list[dict[str, Any]],
    all_torrents_file: str = "all_torrents.json",
) -> None:
    """List torrents to JSON file.

    Args:
        data: The list of torrents to manage.
        all_torrents_file: The file path to store all torrents.
    """
    try:
        data.sort(key=lambda x: x["added"], reverse=True)

        if not os.path.exists(all_torrents_file):
            with open(all_torrents_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False, default=str)
                logger.info(f"All torrents file created: {all_torrents_file}")
        else:
            with open(all_torrents_file, "r+", encoding="utf-8") as f:
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4, ensure_ascii=False, default=str)
                logger.info(f"All torrents file updated: {all_torrents_file}")

    except Exception as e:
        logger.error(f"An error occurred during JSON file creation: {e!s}")


async def _fetch_files_info(
    dao: MediaDAO,
    files: Sequence[TorrentFileModel],
) -> list[dict[str, Any]] | None:
    """Fetch files info from database."""

    if not files:
        return []

    data = []

    for file in files:
        info_data = None
        if file.radarr_id:
            info_radarr = await dao.get_radarr_info_by_id(id=file.radarr_id)
            if info_radarr:
                info_data = {
                    "mediaType": info_radarr.mediaType,
                    "title": info_radarr.title,
                    "year": info_radarr.year,
                    "releaseGroup": info_radarr.releaseGroup,
                    "tmdbId": info_radarr.tmdbId,
                    "imdbId": info_radarr.imdbId,
                    "genres": info_radarr.genres,
                    "quality": info_radarr.quality,
                    "resolution": info_radarr.resolution,
                    "languages": info_radarr.languages,
                }
        elif file.sonarr_id:
            info_sonarr = await dao.get_sonarr_info_by_id(id=file.sonarr_id)
            if info_sonarr:
                info_data = {
                    "mediaType": info_sonarr.mediaType,
                    "serieTitle": info_sonarr.serieTitle,
                    "year": info_sonarr.year,
                    "seasonNumber": info_sonarr.seasonNumber,
                    "episodeTitle": info_sonarr.episodeTitle,
                    "episodeNumber": info_sonarr.episodeNumber,
                    "releaseGroup": info_sonarr.releaseGroup,
                    "tvdbId": info_sonarr.tvdbId,
                    "imdbId": info_sonarr.imdbId,
                    "tvMazeId": info_sonarr.tvMazeId,
                    "genres": info_sonarr.genres,
                    "quality": info_sonarr.quality,
                    "resolution": info_sonarr.resolution,
                    "languages": info_sonarr.languages,
                }

        file_data = {
            "path": file.path,
            "bytes": file.bytes,
            "added": file.added,
            "info": info_data,
        }
        data.append(file_data)

    return data


async def _get_all_torrents_from_db(dao: MediaDAO) -> list[dict[str, Any]] | None:
    """Get all torrents from database.

    Args:
        dao: The database DAO for torrents.

    Returns:
        A list of dictionaries representing the torrents.
    """
    limit = 1000
    offset = 0
    all_torrents = []

    while True:
        torrents = await dao.get_all_torrents(limit=limit, offset=offset)
        for item in torrents:
            files = await dao.get_files_from_torrent_id(torrent_id=item.id)
            files_data = await _fetch_files_info(dao, files)
            data = {
                "torrent": item.filename,
                "id": item.id,
                "hash": item.hash,
                "added": item.added,
                "files": files_data,
            }
            all_torrents.append(data)
        if len(all_torrents) < (offset + limit):
            break
        else:
            offset += limit
    if all_torrents:
        logger.info(f"Torrents found in database: {len(all_torrents)}")
        return all_torrents
    else:
        return None


async def process_jsonfile(dao: MediaDAO) -> None:
    """Process the JSON file with the given data.

    Args:
        data: The list of torrents to manage.
    """
    if settings.environment == "dev":
        all_torrents_file = "all_torrents_syncrr.json"
    else:
        all_torrents_file = settings.all_torrents_file

    try:
        data: list[dict[str, Any]] | None = await _get_all_torrents_from_db(dao)
        if not data:
            logger.error("No torrents found in database skip json update.")
            return
        await _list_torrents_to_json(
            data=data,
            all_torrents_file=all_torrents_file,
        )
    except Exception as e:
        logger.error(f"An error occurred during JSON file processing: {e!s}")


async def process_torrents_data(
    dao: MediaDAO,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get torrents info from database.

    Args:
        dao: The database DAO for torrents.
        limit: The limit of torrents to fetch.
        offset: The offset of torrents to fetch.
    """
    torrents_data: List[Dict[str, Any]] = []
    try:
        torrents = await dao.get_all_torrents(limit=limit, offset=offset)
        for item in torrents:
            files = await dao.get_files_from_torrent_id(torrent_id=item.id)
            files_data = await _fetch_files_info(dao, files)
            data = {
                "torrent": item.filename,
                "id": item.id,
                "hash": item.hash,
                "added": item.added,
                "files": files_data,
            }
            torrents_data.append(data)
    except Exception as e:
        logger.error(f"An error occurred during torrents info fetching: {e!s}")
    return torrents_data
