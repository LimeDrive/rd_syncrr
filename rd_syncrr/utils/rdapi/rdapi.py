""" Real-Debrid API wrapper """
import itertools
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import requests
from requests import Response

from rd_syncrr.logging import logger
from rd_syncrr.settings import settings


class RD:
    def __init__(self) -> None:
        self.rd_apitoken = settings.rd_token
        self.base_url = "https://api.real-debrid.com/rest/1.0"
        self.header = {"Authorization": "Bearer " + str(self.rd_apitoken)}
        self.error_codes = json.load(
            open(  # noqa: SIM115
                os.path.join(Path(__file__).parent.absolute(), "error_codes.json"),
            ),
        )
        self.sleep = settings.rd_sleep
        self.long_sleep = settings.rd_long_sleep
        self.count_obj = itertools.cycle(range(0, 501))
        self.count = next(self.count_obj)

        # Check the API token
        self.check_token()

        self.system = self.System(self)
        self.user = self.User(self)
        self.unrestrict = self.Unrestrict(self)
        self.traffic = self.Traffic(self)
        self.streaming = self.Streaming(self)
        self.downloads = self.Downloads(self)
        self.torrents = self.Torrents(self)
        self.hosts = self.Hosts(self)
        self.settings = self.Settings(self)

    def get(self, path: str, **options: Any) -> Response:
        request = requests.get(  # noqa: S113
            self.base_url + path,
            headers=self.header,
            params=options,
        )
        return self.handler(request, self.error_codes, path)

    def post(self, path: str, **payload: Any) -> Response:
        request = requests.post(  # noqa: S113
            self.base_url + path,
            headers=self.header,
            data=payload,
        )
        return self.handler(request, self.error_codes, path)

    def put(self, path: str, filepath: str, **payload: Any) -> Response:
        with open(filepath, "rb") as file:
            request = requests.put(  # noqa: S113
                self.base_url + path,
                headers=self.header,
                data=file,
                params=payload,
            )
        return self.handler(request, self.error_codes, path)

    def delete(self, path: str) -> Response:
        request = requests.delete(  # noqa: S113
            self.base_url + path,
            headers=self.header,
        )
        return self.handler(request, self.error_codes, path)

    def handler(
        self,
        request: Response,
        error_codes: dict[str, str],
        path: str,
    ) -> Response:
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logger.error("%s at %s", errh, path)
        except requests.exceptions.ConnectionError as errc:
            logger.error("%s at %s", errc, path)
        except requests.exceptions.Timeout as errt:
            logger.error("%s at %s", errt, path)
        except requests.exceptions.RequestException as err:
            logger.error("%s at %s", err, path)
        try:
            if "error_code" in request.json():
                code = request.json()["error_code"]
                message = error_codes.get(str(code), "Unknown error")
                logger.warning("%s: %s at %s", code, message, path)
        except:  # noqa: E722, S110
            pass
        self.handle_sleep()
        return request

    def check_token(self) -> None:
        if self.rd_apitoken is None or self.rd_apitoken == "your_token_here":
            logger.warning("RD_SYNCRR_RD_TOKEN is not set. Please set it in the .env.")

    def handle_sleep(self) -> None:
        if self.count < 500:
            logger.debug("Sleeping %sms", self.sleep)
            time.sleep(self.sleep / 1000)
        elif self.count == 500:
            logger.debug("Sleeping %sms", self.long_sleep)
            time.sleep(self.long_sleep / 1000)
            self.count = 0

    class System:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def disable_token(self) -> Response:
            return self.rd.get("/disable_access_token")

        def time(self) -> Response:
            return self.rd.get("/time")

        def iso_time(self) -> Response:
            return self.rd.get("/time/iso")

    class User:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(self) -> Response:
            return self.rd.get("/user")

    class Unrestrict:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def check(self, link: str, password: Optional[str] = None) -> Response:
            return self.rd.post("/unrestrict/check", link=link, password=password)

        def link(
            self,
            link: str,
            password: Optional[str] = None,
            remote: Optional[str] = None,
        ) -> Response:
            return self.rd.post(
                "/unrestrict/link",
                link=link,
                password=password,
                remote=remote,
            )

        def folder(self, link: str) -> Response:
            return self.rd.post("/unrestrict/folder", link=link)

        def container_file(self, filepath: str) -> Response:
            return self.rd.put("/unrestrict/containerFile", filepath=filepath)

        def container_link(self, link: str) -> Response:
            return self.rd.post("/unrestrict/containerLink", link=link)

    class Traffic:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(self) -> Response:
            return self.rd.get("/traffic")

        def details(
            self,
            start: Optional[str] = None,
            end: Optional[str] = None,
        ) -> Response:
            return self.rd.get("/traffic/details", start=start, end=end)

    class Streaming:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def transcode(self, id: str) -> Response:  # noqa: A002
            return self.rd.get("/streaming/transcode/" + str(id))

        def media_info(self, id: str) -> Response:  # noqa: A002
            return self.rd.get("/streaming/mediaInfos/" + str(id))

    class Downloads:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(
            self,
            offset: Optional[int] = None,
            page: Optional[int] = None,
            limit: Optional[int] = None,
        ) -> Response:
            return self.rd.get("/downloads", offset=offset, page=page, limit=limit)

        def delete(self, id: str) -> Response:  # noqa: A002
            return self.rd.delete("/downloads/delete/" + str(id))

    class Torrents:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(
            self,
            offset: Optional[int] = None,
            page: Optional[int] = None,
            limit: Optional[int] = None,
            filter: Optional[str] = None,  # noqa: A002
        ) -> Response:
            return self.rd.get(
                "/torrents",
                offset=offset,
                page=page,
                limit=limit,
                filter=filter,
            )

        def info(self, id: str) -> Response:  # noqa: A002
            return self.rd.get("/torrents/info/" + str(id))

        def instant_availability(self, hash: str) -> Response:  # noqa: A002
            return self.rd.get("/torrents/instantAvailability/" + str(hash))

        def active_count(self) -> Response:
            return self.rd.get("/torrents/activeCount")

        def available_hosts(self) -> Response:
            return self.rd.get("/torrents/availableHosts")

        def add_file(self, filepath: str, host: Optional[str] = None) -> Response:
            return self.rd.put("/torrents/addTorrent", filepath=filepath, host=host)

        def add_magnet(self, magnet: str, host: Optional[str] = None) -> Response:
            magnet_link = "magnet:?xt=urn:btih:" + str(magnet)
            return self.rd.post("/torrents/addMagnet", magnet=magnet_link, host=host)

        def select_files(self, id: str, files: str) -> Response:  # noqa: A002
            return self.rd.post("/torrents/selectFiles/" + str(id), files=str(files))

        def delete(self, id: str) -> Response:  # noqa: A002
            return self.rd.delete("/torrents/delete/" + str(id))

    class Hosts:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(self) -> Response:
            return self.rd.get("/hosts")

        def status(self) -> Response:
            return self.rd.get("/hosts/status")

        def regex(self) -> Response:
            return self.rd.get("/hosts/regex")

        def regex_folder(self) -> Response:
            return self.rd.get("/hosts/regexFolder")

        def domains(self) -> Response:
            return self.rd.get("/hosts/domains")

    class Settings:
        def __init__(self, rd_instance: "RD") -> None:
            self.rd = rd_instance

        def get(self) -> Response:
            return self.rd.get("/settings")

        def update(self, setting_name: str, setting_value: str) -> Response:
            return self.rd.post(
                "/settings/update",
                setting_name=setting_name,
                setting_value=setting_value,
            )

        def convert_points(self) -> Response:
            return self.rd.post("/settings/convertPoints")

        def change_password(self) -> Response:
            return self.rd.post("/settings/changePassword")

        def avatar_file(self, filepath: str) -> Response:
            return self.rd.put("/settings/avatarFile", filepath=filepath)

        def avatar_delete(self) -> Response:
            return self.rd.delete("/settings/avatarDelete")
