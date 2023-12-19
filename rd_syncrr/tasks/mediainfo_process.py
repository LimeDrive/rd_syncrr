"""Process media information and update the database."""

from typing import Any, Dict, List  # noqa: UP035

from rd_syncrr.logging import logger
from rd_syncrr.services.media_db.dao.media_dao import MediaDAO
from rd_syncrr.settings import settings  # noqa: F401
from rd_syncrr.tasks.arrinfo_api import ArrInfo

arrinfo = ArrInfo()


async def _add_sonarr_episodes_to_db(
    dao: MediaDAO, new_episodes: List[Dict[str, Any]]
) -> None:
    """
    Add new episodes to the database.

    Args:
        dao (MediaDAO): The media DAO.
        new_episode (List[Dict[str, Any]]): The new episodes to add.
    """
    try:
        for episode in new_episodes:
            await dao.create_sonarr_episode_model(episode)
            logger.info(
                f"Episode info added to database: {episode['serieTitle']} "
                f"Episode {episode['episodeNumber']} Saison {episode['seasonNumber']}"
            )
    except Exception as e:
        logger.error(
            f"An error occurred while adding new episodes to the database: {e!s}"
        )


async def _get_sonarr_new_episodes(dao: MediaDAO) -> List[Dict[str, Any]] | None:
    """
    Get new episodes from Sonarr.

    Returns:
        List[Dict[str, Any]]: The new episodes.
    """
    try:
        sonarr_episodes = arrinfo.get_sonarr_info()
        in_db_episodes = await dao.get_sonarr_episodes_file_id()
        if not in_db_episodes:
            return sonarr_episodes
        new_episodes: List[Dict[str, Any]] = []
        for episode in sonarr_episodes:
            if episode["episodefileId"] not in in_db_episodes:
                new_episodes.append(episode)
        if not new_episodes:
            logger.debug("No new episodes found.")
            return None
    except Exception as e:
        logger.error(f"An error occurred while getting new episodes: {e!s}")
        return None
    return new_episodes


async def _add_radarr_movies_to_db(
    dao: MediaDAO, new_movies: List[Dict[str, Any]]
) -> None:
    """
    Add new movies to the database.

    Args:
        dao (MediaDAO): The media DAO.
        new_movies (List[Dict[str, Any]]): The new movies to add.
    """
    try:
        for movie in new_movies:
            await dao.create_radarr_movie_model(movie)
            logger.info(f"Movie info added to database: {movie['title']}")
    except Exception as e:
        logger.error(
            f"An error occurred while adding new movies to the database: {e!s}"
        )


async def _get_radarr_new_movies(dao: MediaDAO) -> List[Dict[str, Any]] | None:
    """
    Get new movies from Radarr.

    Returns:
        List[Dict[str, Any]]: The new movies.
    """
    try:
        radarr_movies = arrinfo.get_radarr_info()
        in_db_movies = await dao.get_radarr_movies_file_id()
        if not in_db_movies:
            return radarr_movies
        new_movies: List[Dict[str, Any]] = []
        for movie in radarr_movies:
            if movie["fileId"] not in in_db_movies:
                new_movies.append(movie)
        if not new_movies:
            logger.debug("No new movies found.")
            return None
    except Exception as e:
        logger.error(f"An error occurred while getting new movies: {e!s}")
        return None
    return new_movies


async def process_mediainfo(dao: MediaDAO) -> None:
    """Process media information and update the database."""

    try:
        logger.info("Updating media info...")
        new_episode = await _get_sonarr_new_episodes(dao)
        if new_episode:
            await _add_sonarr_episodes_to_db(dao, new_episode)
        else:
            logger.info("No new episodes found in Sonarr skiping the update")
        new_movies = await _get_radarr_new_movies(dao)
        if new_movies:
            await _add_radarr_movies_to_db(dao, new_movies)
        else:
            logger.info("No new movies found in Radarr skiping the update")
        logger.info("Media info updated.")
    except Exception as e:
        logger.error(
            f"An error occurred while processing media info update on db: {e!s}"
        )
