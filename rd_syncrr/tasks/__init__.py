"""Tasks for the services app."""
from rd_syncrr.tasks.data_process import process_jsonfile, process_torrents_data
from rd_syncrr.tasks.infolink_process import process_unlinked_media_info
from rd_syncrr.tasks.mediainfo_process import process_mediainfo
from rd_syncrr.tasks.symlink_process import process_symlink
from rd_syncrr.tasks.sync_instance import sync_all_torrents, sync_latest_torrents
from rd_syncrr.tasks.torrents_action import (
    add_cached_torrent_to_rd,
    check_hash_availability,
)
from rd_syncrr.tasks.torrents_process import process_torrents

__all__ = [
    "process_torrents",
    "process_unlinked_media_info",
    "process_mediainfo",
    "process_symlink",
    "process_jsonfile",
    "process_torrents_data",
    "sync_all_torrents",
    "sync_latest_torrents",
    "check_hash_availability",
    "add_cached_torrent_to_rd",
]
