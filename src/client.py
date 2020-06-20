import json
import os
import time
from json.decoder import JSONDecodeError
from pathlib import Path

import requests
from furl import furl

from cache import Cache
from loggers.logger import Logger

BASE_REPORT_URL = 'https://classic.warcraftlogs.com:443/' \
                  'v1/reports/guild/{guild}/{server}/{region}'

BASE_LOG_URL = 'https://classic.warcraftlogs.com:443' \
               '/v1/report/tables/{view}/{log_id}' \
               '?end={end}&encounter={encounter}'

API_KEY = os.getenv("API_KEY")


class WCLClient():

    def __init__(
        self,
        base_report_url: str = BASE_REPORT_URL,
        base_log_url: str = BASE_LOG_URL,
        api_key: str = API_KEY
    ) -> None:
        self.report_url = base_report_url
        self.log_url = base_log_url
        self.logger = Logger().getLogger(__file__)
        self.logger.info("Initialize WCLClient.")
        self.__cache = Cache()

    def __get_cache_key(self, func_name: str) -> str:
        return f"{Path(__file__).stem}.{func_name}"

    def __add_api_key(self, url: str):
        return furl(url).add({'api_key': API_KEY})

    def __parse_reports_response(self, response):
        try:
            reports = response.json()
            try:
                options = [
                    {
                        'label': report['title'],
                        'value': json.dumps(report),
                        'zone': report['zone']
                    } for report in reports
                ]
                return options
            except (NameError, TypeError) as e:
                self.logger.error(
                    f"Got status code: {reports.get('status', None)}. Response: {reports}"
                )
                raise e
        except JSONDecodeError as e:
            self.logger.error(
                f"Couldn't parse response as json: '{response.text}'"
            )
            raise e

    def __parse_log_response(self, response, view, encounter):
        try:
            json_response = response.json()
            if 'error' not in json_response:
                return json_response
            else:
                self.logger.warning(
                    f"Got status code {json_response.get('status', None)}.Response: {json_response}"
                )
        except JSONDecodeError as e:
            self.logger.error(f"Couldn't parse response as json: '{response.text}'")
            raise e

    def get_reports(
        self,
        guild: str,
        server: str,
        region: str
    ):
        if self.__cache.key_exists(
            self.__get_cache_key(func_name = "_get_reports"),
            guild,
            server,
            region
        ):
            self.logger.info(
                f"Reports for {guild}-{server}-{region} already exists, fetching from cache."
            )

        @self.__cache()
        def _get_reports(
            guild: str,
            server: str,
            region: str
        ):

            url = self.report_url.format(
                guild = guild,
                server = server,
                region = region
            )

            url = self.__add_api_key(url)

            self.logger.debug(f"Requesting reports from url: {url}")
            t0 = time.time()
            response = requests.get(url=url, verify=True)
            t1 = time.time()
            self.logger.debug('Done. API call for fetching reports took {} s.'.format(t1 - t0))

            return self.__parse_reports_response(response)

        return _get_reports(guild, server, region)

    def get_log(
        self,
        view: str,
        log_id: str,
        end: str,
        encounter: str
    ):
        if self.__cache.key_exists(
            self.__get_cache_key(func_name = "_get_log"),
            view,
            log_id,
            end,
            encounter
        ):
            self.logger.info(f"Log {log_id} already exists, fetching from cache.")

        @self.__cache()
        def _get_log(
            view: str,
            log_id: str,
            end: str,
            encounter: str
        ):

            url = self.log_url.format(
                view = view,
                log_id = log_id,
                end = end,
                encounter = encounter
            )

            url = self.__add_api_key(url)

            self.logger.debug(f"Fetching logs from url: {url}")
            t0 = time.time()
            response = requests.get(url=url, verify=True)
            t1 = time.time()
            self.logger.debug('Done API call for fetching logs. Took {} s.'.format(t1 - t0))

            return self.__parse_log_response(response, view, encounter)

        return _get_log(view, log_id, end, encounter)
