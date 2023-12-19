"""Add media info to database from radarr/sonarr."""

from typing import Any, Dict, List  # noqa: UP035

from rd_syncrr.logging import logger
from rd_syncrr.settings import settings
from rd_syncrr.utils.pyarr import RadarrAPI, SonarrAPI
from rd_syncrr.utils.pyarr.types import JsonArray, JsonObject


class ArrInfo:
    def __init__(self) -> None:
        if settings.radarr_host is None or settings.radarr_api_key is None:
            raise ValueError("Radarr host or api key not set")
        if settings.sonarr_host is None or settings.sonarr_api_key is None:
            raise ValueError("Sonarr host or api key not set")
        self.radarr = RadarrAPI(settings.radarr_host, settings.radarr_api_key)
        self.sonarr = SonarrAPI(settings.sonarr_host, settings.sonarr_api_key)

    def _create_movie_data(
        self,
        movie: Dict[str, Any],
        movie_file: Dict[str, Any],
    ) -> Dict[str, Any]:
        quality = movie_file.get("quality", {}).get("quality", {})
        return {
            "mediaType": "movie",
            "movieId": movie.get("id"),
            "title": movie.get("title"),
            "originalTitle": movie.get("originalTitle"),
            "year": movie.get("year"),
            "releaseGroup": movie_file.get("releaseGroup"),
            "imdbId": movie.get("imdbId"),
            "tmdbId": movie.get("tmdbId"),
            "genres": movie.get("genres"),
            "quality": quality.get("name"),
            "resolution": quality.get("resolution"),
            "languages": [lang["name"] for lang in movie_file.get("languages", [])],
            "originalFilePath": movie_file.get("originalFilePath"),
            "relativePath": movie_file.get("relativePath"),
            "path": movie_file.get("path"),
            "fileId": movie_file.get("id"),
        }

    def _create_episode_data(
        self,
        serie: Dict[str, Any],
        episode_file: Dict[str, Any],
    ) -> Dict[str, Any]:
        quality = episode_file.get("quality", {}).get("quality", {})
        language = episode_file.get("language", [])
        if isinstance(language, dict):
            language = [language]
        return {
            "mediaType": "serie",
            "serieId": serie.get("id"),
            "serieTitle": serie.get("title"),
            "year": serie.get("year"),
            "seasonNumber": episode_file.get("seasonNumber"),
            "episodeTitle": episode_file.get("episodeTitle"),
            "episodeNumber": episode_file.get("episodeNumber"),
            "releaseGroup": episode_file.get("releaseGroup"),
            "tvdbId": serie.get("tvdbId"),
            "imdbId": serie.get("imdbId"),
            "tvMazeId": serie.get("tvMazeId"),
            "genres": serie.get("genres"),
            "quality": quality.get("name"),
            "resolution": quality.get("resolution"),
            "languages": [lang["name"] for lang in language],
            "relativePath": episode_file.get("relativePath"),
            "path": episode_file.get("path"),
            "episodeId": episode_file.get("episodeId"),
            "episodefileId": episode_file.get("id"),
        }

    def get_radarr_info(self) -> JsonArray:
        """Get all general radarr movies info.

        This function will filter out movies that have no file.

        This fonction return a list of dictionsnaries with the following format:

        [
            {
                "mediaType": string,
                "movieId": int,
                "title": string,
                "originalTitle": string,
                "year": int,
                "releaseGroup": string,
                "imbdId": string,
                "tmbdId": int,
                "genres": List[str],
                "quality": string,
                "resolution": int,
                "languages": List[str],
                "originalFilePath": string,
                "relativePath": string,
                "path": string,
                "fileId": int,
            },
        ]
        """
        data: JsonArray = []
        try:
            radarr_movies = self.radarr.get_movie()
            if isinstance(radarr_movies, dict):
                radarr_movies = [radarr_movies]
            for movie in radarr_movies:
                if movie.get("hasFile") is False:
                    logger.debug(f"Movie has no file: {movie}")
                    continue
                movie_file = movie.get("movieFile")
                if movie_file == {} or movie_file is None:
                    logger.debug(f"Movie file not found: {movie}")
                    continue
                movie_data = self._create_movie_data(movie, movie_file)
                data.append(movie_data)
        except Exception as e:
            logger.error(f"Failed to get radarr movies: {e}")
        return data

    def _get_sonarr_series_info(self) -> JsonArray:
        """Get all general sonarr series info.

        This function will filter out series that have no episode files.
        """
        data: List[Dict[str, Any]] = []
        try:
            sonarr_series = self.sonarr.get_series()
            if isinstance(sonarr_series, dict):
                sonarr_series = [sonarr_series]
            for serie in sonarr_series:
                stats = serie.get("statistics", {})
                if stats == {}:
                    logger.debug(f"Series has no statistics field: {serie}")
                    continue
                elif stats.get("episodeFileCount") == 0:
                    serie_title = serie.get("title")
                    logger.debug(f"Skiping {serie_title}, serie has no episode files")
                    continue
                data.append(serie)
        except Exception as e:
            logger.error(f"Failed to get sonarr series: {e}")
        return data

    def _get_sonarr_episodes_files_info(self, series_id: int) -> JsonArray:
        """Get all sonarr episodes files info from a given series id.

        Args:
            series_id (int): Series id.
        """
        try:
            sonarr_episodes = self.sonarr.get_episode_file(series_id, series=True)
            if isinstance(sonarr_episodes, dict):
                sonarr_episodes = [sonarr_episodes]
        except Exception as e:
            logger.error(f"Failed to get sonarr episodes: {e}")
            return [{}]  # Return an empty dict in case of error
        return sonarr_episodes

    # SHOULD BE DEPRECATED
    # def _get_sonarr_episode_info(self, _id: int) -> JsonObject[Any]:
    #     """Get single sonarr episode info from a given episode id.

    #     Args:
    #         _id (int): Episode id.

    #     !! Note: At some point this is the only way to get the related episode number.
    #     But this is a very expensive operation, so we should try to avoid it.
    #     Will try to find a better way to do this.
    #     """
    #     try:
    #         episode_info = self.sonarr.get_episode(_id, ep_id=True)
    #     except Exception as e:
    #         logger.error(f"Failed to get sonarr episodes: {e}")
    #         return {}  # Return an empty dict in case of error
    #     return episode_info

    def _get_sonarr_episodes_info(self, serie_id: int) -> List[Dict[str, Any]]:
        """Get all sonarr episodes info from a given series id.

        Args:
            serie_id (int): Series id.
        """
        sonarr_episodes: List[Dict[str, Any]] = []
        try:
            episodes = self.sonarr.get_episode(serie_id, series=True)
            if isinstance(episodes, dict):
                sonarr_episodes = [episodes]
            elif isinstance(episodes, list):
                sonarr_episodes = episodes
        except Exception as e:
            logger.error(f"Failed to get sonarr episodes: {e}")
            return [{}]  # Return a list with an empty dict in case of error
        return sonarr_episodes

    def _create_sonarr_data(self, sonarr_series: JsonArray) -> JsonArray:
        """Create sonarr data. Create a list of episodes files for each serie.
            With selected info.

        Args:
            sonarr_series (JsonArray): Sonarr series info.
        """
        data: JsonArray = []
        try:
            for serie in sonarr_series:
                episodes_files = serie.get("episodesFiles")
                if episodes_files == {} or episodes_files is None:
                    logger.debug(f"Serie has no episodes files: {serie}")
                    continue
                for episode_file in episodes_files:
                    episode = self._create_episode_data(serie, episode_file)
                    data.append(episode)
        except Exception as e:
            logger.error(f"Failed to create data: {e}")
        return data

    def _update_episode_file_dict(
        self,
        episode_file: JsonObject[Any],
        episode_info: JsonObject[Any],
    ) -> None:  # type: ignore
        """Update episode file with episode info."""
        if episode_info:
            episode_file.update(
                {
                    "episodeNumber": episode_info.get("episodeNumber"),
                    "episodeTitle": episode_info.get("title"),
                    "episodeId": episode_info.get("id"),
                },
            )

    def _update_episodes_files(
        self,
        episodes_files: JsonArray,
        episodes_info: JsonArray,
    ) -> None:
        """Update episodes files with missing episodes info."""
        for episode_file in episodes_files:
            episode_file_id = episode_file.get("id")
            if episode_file_id is None:
                logger.debug(f"Episode file id not found: {episode_file}")
                continue
            matching_episode_info = next(
                (
                    info
                    for info in episodes_info
                    if info.get("episodeFileId") == episode_file_id
                ),
                None,
            )
            if matching_episode_info is None:
                logger.debug(
                    f"No matching episode info found for id: {episode_file_id}",
                )
                continue
            self._update_episode_file_dict(episode_file, matching_episode_info)

    def _get_updated_sonarr_info(self) -> JsonArray:
        """Get all sonarr series info by episode with updated episode info."""
        sonarr_series = self._get_sonarr_series_info()
        for serie in sonarr_series:
            series_id = serie.get("id")
            if series_id is None:
                logger.debug(f"Series id not found: {serie}")
                continue
            episodes_files = self._get_sonarr_episodes_files_info(series_id)
            episodes_info = self._get_sonarr_episodes_info(series_id)
            if episodes_info == [{}] or episodes_files == [{}]:
                logger.debug(f"Episodes info not found: {serie}")
                continue
            self._update_episodes_files(episodes_files, episodes_info)
            serie.update({"episodesFiles": episodes_files})
        return sonarr_series

    def get_sonarr_info(self) -> JsonArray:
        """Get all sonarr series info by episode with updated episode info.

        This fonction return a list of dictionsnaries with the following format:

        [
            {
                "mediaType": string,
                "serieId": int,
                "serieTitle": string,
                "year": int,
                "seasonNumber": int,
                "episodeTitle": string,
                "episodeNumber": int,
                "releaseGroup": string,
                "tvdbId": int,
                "imbdId": string,
                "tvMazeId": int,
                "genres": List[str],
                "quality": string,
                "resolution": int,
                "languages": List[str],
                "relativePath": string,
                "path": string,
                "episodefileId": int,
                "episodeId": int,
            },
        ]
        """
        try:
            sonarr_series = self._get_updated_sonarr_info()
            data = self._create_sonarr_data(sonarr_series)
        except Exception as e:
            logger.error(f"Failed to get sonarr series: {e}")
            return []  # Return an empty list in case of error
        return data


if __name__ == "__main__":
    # import json

    # arr_info = ArrInfo()
    # # episodes = arr_info.sonarr.get_episode(2, series=True)

    # # print(json.dumps(episodes, indent=4))

    # series = arr_info.get_sonarr_info()
    # movies = arr_info.get_radarr_info()
    # print(json.dumps(series, indent=2))
    # print(json.dumps(movies, indent=2))
    pass
