import logging
import pendulum

from utils.requests_wrapper import get, re

log = logging.getLogger(__name__)


class OpenF1Connector:
    def format_timestamp(self, ts: pendulum.DateTime) -> str:
        return ts.to_iso8601_string()

    def get_meetings(self, meeting_key: int | str = "latest") -> re.Response:
        endpoint = "https://api.openf1.org/v1/meetings"
        params = {"meeting_key": meeting_key}
        log.info("Listening to endpoint `/meetings` with parameters `%s`", params)
        return get(endpoint=endpoint, params=params)

    def get_drivers(self, meeting_key: int) -> re.Response:
        endpoint = "https://api.openf1.org/v1/drivers"
        params = {"meeting_key": meeting_key}
        log.info(
            "Listening to endpoint `/drivers` with parameters `%s`",
            params,
        )
        return get(endpoint=endpoint, params=params)

    def get_sessions(self, meeting_key: int, session_name: str) -> re.Response:
        endpoint = "https://api.openf1.org/v1/sessions"
        params = {"meeting_key": meeting_key, "session_name": session_name}
        log.info(
            "Listening to endpoint `/sessions` with parameters `%s`",
            params,
        )
        return get(endpoint=endpoint, params=params)

    def get_laps(self, session_key: int) -> re.Response:
        endpoint = "https://api.openf1.org/v1/laps"
        params = {"session_key": session_key}
        log.info(
            "Listening to endpoint `/laps` with parameters `%s`",
            params,
        )
        return get(endpoint=endpoint, params=params)

    def get_pits(self, session_key: int) -> re.Response:
        endpoint = "https://api.openf1.org/v1/pit"
        params = {"session_key": session_key}
        log.info(
            "Listening to endpoint `/pit` with parameters `%s`",
            params,
        )
        return get(endpoint=endpoint, params=params)
