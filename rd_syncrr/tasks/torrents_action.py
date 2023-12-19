import asyncio
from typing import Any, Union

from rd_syncrr.logging import logger
from rd_syncrr.utils.rdapi import RD

rdapi = RD()


async def check_hash_availability(
    hash: str,  # noqa: A002
) -> Union[dict[str, Any], bool]:
    """Check if the torrent files are cached in RD server.

    Args:
        hash: The hash of the torrent to check.
    """

    response = rdapi.torrents.instant_availability(hash).json()

    if response[hash] == []:
        logger.info(f"Torrent {hash} is not available")
        return False
    elif "rd" not in response[hash]:
        logger.info(
            f"Torrent {hash} is not available in Real-Debrid but on other hosters",
        )
        return False
    else:
        torrent_info = response[hash]["rd"][0]
        logger.info(f"Torrent {torrent_info}) is available on Real-Debrid")
        return torrent_info


async def add_cached_torrent_to_rd(hash: str) -> None:  # noqa: A002
    """Add a cached torrent to Real-Debrid.

    Args:
        hash: The hash of the torrent to add.
    """
    try:
        magnet = rdapi.torrents.add_magnet(magnet=hash).json()
        rdapi.torrents.select_files(id=magnet["id"], files="all")
        logger.info(
            f"Torrent file : id = {magnet['id']} ; hash = {hash} was added to RD",
        )
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"An error occurred while syncing torrents: {e!s}")
        raise


# rrrt = _check_aviability("d234681e30cfb8ab9cdcd67326dc9080fa9c0418")
# logger.debug(rrrt)
# _check_aviability("d234681e30cfb8ab9cdcd67326dc9080fa9c0410")
