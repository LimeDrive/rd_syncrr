#!/usr/bin/env python3

import itertools
import os
import time
from typing import Any

import requests
from requests import Response

from rd_syncrr.logging import logger
from rd_syncrr.settings import settings


class RDSyncrrApi:
    def __init__(self) -> None:
        self.apikey = settings.syncrr_api_key
        self.base_url = settings.syncrr_host if settings.syncrr_host else ""
        self.header = {"api-key": str(self.apikey)}
        self.sleep = int(os.getenv("SLEEP", 100))
        self.long_sleep = int(os.getenv("LONG_SLEEP", 500))
        self.count_obj = itertools.cycle(range(0, 501))
        self.count = next(self.count_obj)

        # Check the API token
        self.check_token()

        self.torrents = self.Torrents(self)

    def get(self, path: str, **options: Any) -> Response:
        request = requests.get(  # noqa: S113
            self.base_url + path, headers=self.header, params=options
        )
        return self.handler(request, path)

    def post(self, path: str, **payload: Any) -> Response:
        request = requests.post(  # noqa: S113
            self.base_url + path, headers=self.header, data=payload
        )
        return self.handler(request, path)

    def put(self, path: str, filepath: str, **payload: Any) -> Response:
        with open(filepath, "rb") as file:
            request = requests.put(  # noqa: S113
                self.base_url + path, headers=self.header, data=file, params=payload
            )
        return self.handler(request, path)

    def delete(self, path: str) -> Response:
        request = requests.delete(  # noqa: S113
            self.base_url + path, headers=self.header
        )
        return self.handler(request, path)

    def handler(self, request: Response, path: str) -> Response:
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
        self.handle_sleep()
        return request

    def check_token(self) -> None:
        if self.apikey is None or self.apikey == "your_token_here":
            logger.warning("Add apikey to .env")

    def handle_sleep(self) -> None:
        if self.count < 500:
            logger.debug("Sleeping %sms", self.sleep)
            time.sleep(self.sleep / 1000)
        elif self.count == 500:
            logger.debug("Sleeping %sms", self.long_sleep)
            time.sleep(self.long_sleep / 1000)
            self.count = 0

    class Torrents:
        def __init__(self, rd_syncrr_instance: "RDSyncrrApi") -> None:
            self.rd = rd_syncrr_instance

        def all(self) -> Response:  # noqa: A003
            return self.rd.get("/sync/fetchAll")

        def latest(self) -> Response:
            return self.rd.get("/sync/fetchLatest")
