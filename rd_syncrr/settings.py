import enum
import os
from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings, SettingsConfigDict

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    # Path
    config_path: str = "/config"
    media_path: str = "/media"
    symlink_path: str = "/symlinks"
    downloads_path: str = "/downloads"

    # file
    all_torrents_file: str = os.path.join(config_path, "all_torrents.json")
    latest_torrents_file: str = os.path.join(config_path, "latest_torrents.json")

    # Real-Debrid
    rd_token: str | None = None
    rd_sleep: int = 100
    rd_long_sleep: int = 500

    # Security
    security_secret: str | None = None
    security_hide_docs: bool = True
    security_db_location: str = os.path.join(config_path, "/database/")
    security_api_key_expiration: int = 15

    # Database media
    media_db_location: str = os.path.join(config_path, "/database/")
    media_db_echo: bool = False

    # rd_syncrr_api module
    syncrr_api_key: str | None = None
    syncrr_host: str | None = None
    syncrr_sleep: int = 100
    syncrr_long_sleep: int = 500

    # radarr module
    radarr_host: str = "http://radarr:7878"
    radarr_api_key: str | None = None

    # sonarr module
    sonarr_host: str = "http://sonarr:8989"
    sonarr_api_key: str | None = None

    # logger
    log_level: LogLevel = LogLevel.INFO
    log_path: str = os.path.join(config_path, "logs")

    # scheduler
    sched_db_update_interval: int = 15
    sched_sync_interval: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RD_SYNCRR_",
        env_file_encoding="utf-8",
    )


settings = Settings()
