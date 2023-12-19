"""Module for syncing RD account from one to another."""
import asyncio
import json
import os
from typing import Any

from rd_syncrr.logging import logger
from rd_syncrr.utils.rdapi import RD
from rd_syncrr.utils.syncrrapi import RDSyncrrApi

rd_client = RD()
syncrr_api = RDSyncrrApi()


def _get_all_synced_torrents() -> list[dict[str, Any]]:
    """Get all synced torrents from other instance."""
    try:
        synced_torrents = syncrr_api.torrents.all().json()
    except Exception as e:
        logger.error(f"An error occurred while getting synced torrents: {e!s}")
        raise
    return synced_torrents


def _get_latest_synced_torrents() -> list[dict[str, Any]]:
    """Get latest synced torrents from other instance."""
    try:
        synced_torrents = syncrr_api.torrents.latest().json()
    except Exception as e:
        logger.error(f"An error occurred while getting latest synced torrents: {e!s}")
        raise
    return synced_torrents


def _get_all_local_torrents(
    all_torrents_file: str = "all_torrents.json",
) -> list[dict[str, Any]] | None:
    """Get all torrents from local instance."""
    try:
        if not os.path.exists(all_torrents_file):
            with open(all_torrents_file, encoding="utf-8") as f:
                return json.load(f)
        else:
            return None
    except Exception as e:
        logger.error(f"An error occurred while getting local torrents: {e!s}")
        raise


def _list_wanted_torrents(
    synced_torrents: list[dict[str, Any]],
    local_torrents: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    """List wanted torrents."""
    if local_torrents is None:
        wanted_torrents = synced_torrents
        return wanted_torrents
    elif len(synced_torrents) == 0:
        return None
    else:
        synced_torrents_ids = {item["id"] for item in synced_torrents}
        wanted_torrents = [
            item for item in local_torrents if item["id"] not in synced_torrents_ids
        ]
        return wanted_torrents


async def sync_all_torrents() -> None:
    """
    Download all torrents and sync them with the local torrents.

    This function retrieves all torrents from the remote server and compares them with
    the local torrents.
    It selects the wanted torrents that are not already synced and adds them to the RD account.
    After syncing the torrents, it updates the list of torrents in a JSON file.

    Raises:
        Exception: If an error occurs while syncing the torrents.

    Returns:
        None
    """
    local_torrents = _get_all_local_torrents()
    synced_torrents = _get_all_synced_torrents()
    wanted_torrents = _list_wanted_torrents(synced_torrents, local_torrents)
    if wanted_torrents is None:
        logger.info("No torrents to sync")
    else:
        for torrent in wanted_torrents:
            try:
                magnet = rd_client.torrents.add_magnet(magnet=torrent["hash"]).json()
                rd_client.torrents.select_files(id=magnet["id"], files="all")
                logger.info(f"Torrent {torrent['name']} added")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"An error occurred while syncing torrents: {e!s}")
                raise

        await asyncio.sleep(2)
        # await process_torrents()
        logger.info("All torrents successfully synced")


async def sync_latest_torrents() -> None:
    """
    Download the latest torrents and sync them with the local torrents.

    This function retrieves the latest torrents from the remote server and compares
      them with the local torrents.
    It selects the wanted torrents that are not already synced and adds them to the RD account.
    After syncing the torrents, it updates the list of torrents in a JSON file.

    Raises:
        Exception: If an error occurs while syncing the torrents.

    Returns:
        None
    """
    local_torrents = _get_all_local_torrents()
    synced_torrents = _get_latest_synced_torrents()
    wanted_torrents = _list_wanted_torrents(synced_torrents, local_torrents)
    if wanted_torrents is None:
        logger.info("No torrents to sync")
    else:
        for torrent in wanted_torrents:
            try:
                magnet = rd_client.torrents.add_magnet(magnet=torrent["hash"]).json()
                rd_client.torrents.select_files(id=magnet["id"], files="all")
                logger.info(f"Torrent {torrent['name']} added")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"An error occurred while syncing torrents: {e!s}")
                raise

        await asyncio.sleep(2)
        # await process_torrents()
        logger.info("Latest torrents successfully synced")
