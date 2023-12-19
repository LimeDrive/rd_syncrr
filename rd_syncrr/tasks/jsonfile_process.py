"""Update or write the JSON file with the given data."""

import asyncio
import json
import os
from typing import Any

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.settings import settings


async def _list_torrents_to_json(
    data: list[dict[str, Any]],
    all_torrents_file: str = "all_torrents.json",
    latest_torrents_file: str = "latest_torrents.json",
) -> None:
    """List torrents to JSON file.

    Args:
        data: The list of torrents to manage.
        all_torrents_file: The file path to store all torrents.
        latest_torrents_file: The file path to store latest torrents.
    """
    try:
        data.sort(key=lambda x: x["added"], reverse=True)
        latest_data = data[:25]

        if not os.path.exists(latest_torrents_file):
            with open(latest_torrents_file, "w", encoding="utf-8") as f:
                json.dump(latest_data, f, indent=4, ensure_ascii=False, default=str)
                logger.info(f"Latest torrents file created: {latest_torrents_file}")
        else:
            with open(latest_torrents_file, "r+", encoding="utf-8") as f:
                f.seek(0)
                f.truncate()
                json.dump(latest_data, f, indent=4, ensure_ascii=False, default=str)
                logger.info(f"Latest torrents file updated: {latest_torrents_file}")

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
            files_data = [{"filename": os.path.basename(file.path)} for file in files]
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


async def process_jsonfile() -> None:
    """Process the JSON file with the given data.

    Args:
        data: The list of torrents to manage.
    """
    if settings.environment == "dev":
        all_torrents_file = "all_torrents_syncrr.json"
        latest_torrents_file = "latest_torrents_syncrr.json"
    else:
        all_torrents_file = settings.all_torrents_file
        latest_torrents_file = settings.latest_torrents_file

    async with await MediaDAO.create() as dao:
        try:
            data: list[dict[str, Any]] | None = await _get_all_torrents_from_db(dao)
            if not data:
                logger.error("No torrents found in database skip json update.")
                return
            await _list_torrents_to_json(
                data=data,
                all_torrents_file=all_torrents_file,
                latest_torrents_file=latest_torrents_file,
            )
            await asyncio.sleep(1)
            await dao.close()
        except Exception as e:
            logger.error(f"An error occurred during JSON file processing: {e!s}")
