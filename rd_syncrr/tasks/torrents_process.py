"""list_torrents_to_json.py"""

from typing import Any

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.utils.rdapi import RD

rdapi = RD()


def _get_all_torrents(limit: int = 1000) -> list[dict[str, Any]]:
    """Get all torrents from RD.

    Args:
        limit: The maximum number of torrents to retrieve.

    Returns:
        A list of dictionaries representing the torrents.
    """
    page = 1
    counter = limit
    all_torrents = []

    try:
        while True:
            torrents = rdapi.torrents.get(limit=limit, page=page).json()
            all_torrents.extend(torrents)

            if len(torrents) < counter:
                break
            else:
                counter += limit
                page += 1
    except Exception as e:
        logger.error(f"An error occurred: {e!s}")

    return all_torrents


def _get_files_info(torrent_id: str) -> list[dict[str, Any]]:
    """Get files info from RD.

    Args:
        torrent_id: The torrent ID.

    Returns:
        A list of dictionaries representing the files info.
    """
    try:
        info = rdapi.torrents.info(id=torrent_id).json()
        files = info["files"]
        return files  # noqa: TRY300
    except Exception as e:
        logger.error(f"An error occurred while getting files info in RD: {e!s}")
        raise


async def _update_torrent_db(dao: MediaDAO) -> None:
    """Update torrent database.

    Args:
        dao: The database DAO for torrents.
    """
    try:
        data = _get_all_torrents()
        filtered_data = [item for item in data if item["status"] == "downloaded"]
        all_torrents = [
            {"filename": item["filename"], "id": item["id"], "hash": item["hash"]}
            for item in filtered_data
        ]

        torrents_hash = await dao.get_all_torrents_hashes()
        if torrents_hash:
            new_torrents = [
                item for item in all_torrents if item["hash"] not in torrents_hash
            ]
            if new_torrents:
                await _process_new_torrents(dao, new_torrents)
                logger.info(f"New torrents added to database: {len(new_torrents)}")
            else:
                logger.info("No new torrents found in RD.")
        else:
            await _process_new_torrents(dao, all_torrents)
            logger.info(f"New torrents added to database: {len(all_torrents)}")
    except Exception as e:
        logger.error(f"An error occurred during database update: {e!s}")


async def _process_new_torrents(dao: MediaDAO, torrents: list[dict[str, Any]]) -> None:
    """Process new torrents and add them to the database.

    Args:
        dao: The database DAO for torrents.
        torrents: List of new torrents to process.
    """
    for torrent in torrents:
        try:
            await _add_torrent_to_database(dao, torrent)
            await _add_files_to_torrent(dao, torrent)
            logger.info(f"Torrent added to database: {torrent['filename']}")
        except Exception as e:
            logger.error(f"An error occurred while processing torrent: {e!s}")


async def _add_torrent_to_database(dao: MediaDAO, torrent: dict[str, Any]) -> None:
    """Add a torrent to the database.

    Args:
        dao: The database DAO for torrents.
        torrent: The torrent data to add.
    """
    await dao.create_torrent_model(
        hash=torrent["hash"], id=torrent["id"], filename=torrent["filename"]
    )


async def _add_files_to_torrent(dao: MediaDAO, torrent: dict[str, Any]) -> None:
    """Add files to a torrent in the database.

    Args:
        dao: The database DAO for torrents.
        torrent: The torrent data containing files to add.
    """
    try:
        files = _get_files_info(torrent_id=torrent["id"])
        selected_files = [file for file in files if file["selected"] == 1]
        file_data = [
            {"path": file["path"], "bytes": file["bytes"]} for file in selected_files
        ]
        for file in file_data:
            await dao.create_file_model(torrent_id=torrent["id"], file_data=file)
            logger.debug(
                f"File from {torrent['filename']} added to database: {file['path']}"
            )
    except Exception as e:
        logger.error(f"An error occurred while getting files info in RD: {e!s}")


async def process_torrents(dao: MediaDAO) -> None:
    """Process torrents refresh.

    This function is called by the scheduler.
    """
    try:
        logger.info("Updating torrents infos.")
        await _update_torrent_db(dao)
        logger.info("Torrents infos updated.")
    except Exception as e:
        logger.error(f"An error occurred while processing torrents refresh: {e!s}")
