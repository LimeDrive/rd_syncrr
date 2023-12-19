"""Symlink process task module."""
import asyncio
import os
from typing import Any

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.settings import settings


async def _scan_link_directory(path: str) -> list[dict[str, str]] | None:
    """
    Scan the given directory for symbolic links.

    Args:
        path (str): The directory to scan.

    Returns:
        list[dict[str, Any]] | None: A list of symbolic links information
        or None if no symbolic links found.
    """
    symlink_info_list = []
    for root, _, files in os.walk(path):
        for file in files:
            if os.path.islink(os.path.join(root, file)):
                symlink_info = await _get_symlink_info(os.path.join(root, file))
                if symlink_info is not None:
                    symlink_info_list.append(symlink_info)
    if not symlink_info_list:
        logger.warning("No symbolic links found in your library.")
        return None
    logger.debug(f"Symlink list: {symlink_info_list}")
    return symlink_info_list


async def _get_symlink_info(link_path: str) -> dict[str, Any] | None:
    """
    Get the information of a symbolic link.

    Args:
        link_path (str): The path of the symbolic link.

    Returns:
        dict[str, Any] | None: The information of the symbolic link
          or None if an error occurred.
    """
    try:
        target = os.readlink(link_path)
        target_path = os.path.abspath(os.path.join(os.path.dirname(link_path), target))
        return {
            "target": target_path,
            "target_filename": os.path.basename(target_path),
            "destination": link_path,
            "destination_filename": os.path.basename(link_path),
        }
    except OSError as e:
        logger.error(f"Error reading symlink: {link_path} - {e!s}")
        return None


async def _update_symlink_db(
    dao: MediaDAO, symlink_info_list: list[dict[str, str]]
) -> None:
    """
    Update the symbolic links in the database.

    Args:
        dao (MediaDAO): The data access object.
        symlink_info_list (list[dict[str, Any]]): The list of symbolic links information.
    """
    torrent_files_dict = await dao.get_torrent_files_filename_dict()
    if not torrent_files_dict:
        logger.warning(
            "No torrent files found in your database. Skipping the symlink update."
        )
        return
    for symlink_info in symlink_info_list:
        if symlink_info["target_filename"] not in torrent_files_dict:
            logger.warning(
                f"File {symlink_info['target_filename']} not found in Torrent Files"
                " Data. Skipping the symlink update."
            )
            continue
        try:
            file_id: str = torrent_files_dict[symlink_info["target_filename"]]
            await dao.create_symlink_model(symlink_info, file_id=file_id)
            logger.info(
                f"Added symlink: {symlink_info['target']} ->"
                f" {symlink_info['destination']} map with rd_file_id  : {file_id}"
            )
        except Exception as e:
            logger.error(f"An error occurred while creating symlink model: {e!s}")


async def process_symlink() -> None:
    """
    Process the symbolic links.
    """
    symlink_info_list = await _scan_link_directory(settings.symlink_path)
    if not symlink_info_list:
        return
    async with await MediaDAO.create() as dao:
        try:
            logger.info("Start symbolic links database Update.")
            old_symlinks = await dao.get_symlink_destination_filename_dict()
            if old_symlinks:
                symlink_info_list = [
                    symlink_info
                    for symlink_info in symlink_info_list
                    if symlink_info["destination_filename"] not in old_symlinks
                ]
                if not symlink_info_list:
                    logger.info("All symbolic links are already in the database.")
                    return
            await _update_symlink_db(dao, symlink_info_list)
            await asyncio.sleep(1)
            logger.info(
                f"Successfully processed {len(symlink_info_list)} new symbolic links"
                " from your library."
            )
            await dao.close()
            logger.info("End symbolic links database Update.")
        except Exception as e:
            logger.error(
                f"An error occurred while processing symbolic links refresh: {e!s}"
            )


# if __name__ == "__main__":
#     directory_to_scan = "/path/to/your/directory"
#     asyncio.run(main(directory_to_scan))
