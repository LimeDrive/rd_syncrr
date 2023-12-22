"""Check if all torrents are linked to their respective media files."""

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao import MediaDAO


async def process_unlinked_media_info(dao: MediaDAO) -> None:
    """Check if all torrents are linked to their respective media files.

    Args:
        dao: The database DAO for torrents.
    """
    unlinked_torrents = await dao.get_files_unlinked_media()
    if not unlinked_torrents:
        return
    for torrent in unlinked_torrents:
        if not torrent.symlink_id:
            logger.warning(f"Symlink not found for torrent: {torrent.path}")
            continue
        symlink = await dao.get_symlink_by_id(torrent.symlink_id)
        if not symlink:
            logger.warning(f"Symlink not found in db for torrent: {torrent.path}")
            continue
        radarr = await dao.check_radarr_path_exists(symlink.destination)
        if radarr:
            logger.info(f"Found Radarr path for torrent: {torrent.path}")
            await dao.link_file_to_radarr(file_id=torrent.id, radarr_id=radarr.id)
            continue
        sonarr = await dao.check_sonarr_path_exists(symlink.destination)
        if sonarr:
            logger.info(f"Found Sonarr path for torrent: {torrent.path}")
            await dao.link_file_to_sonarr(file_id=torrent.id, sonarr_id=sonarr.id)
            continue
        logger.info(f"Could not find media path for torrent: {torrent.path}")
