from contextlib import contextmanager
import logging
from typing import Any, Generator

from duckdb import connect, DuckDBPyConnection, ConnectionException
from pandas import DataFrame
from pydantic_settings import BaseSettings

log = logging.getLogger(__name__)


class MotherDuckSettings(BaseSettings):
    motherduck_token: str
    motherduck_database: str


class MotherDuckConnection:
    def __init__(self):
        self._settings = None
        self._connection: DuckDBPyConnection | None = None

    @property
    def settings(self) -> MotherDuckSettings:
        if self._settings is None:
            self._settings = MotherDuckSettings()
        return self._settings

    @contextmanager
    def connect(self) -> Generator[DuckDBPyConnection, None, None]:
        try:
            conn_str = f"md:{self.settings.motherduck_database}?motherduck_token={self.settings.motherduck_token}"
            self._connection = connect(database=conn_str)
            yield self._connection
        except ConnectionException as e:
            log.error("Could not connect to MotherDuck: %s", e)
            raise
        finally:
            if self._connection:
                self._connection.close()
                self._connection = None

    def execute_query(self, query: str, params: list[Any] = None) -> DataFrame:
        with self.connect() as connection:
            return connection.execute(query, params).df()
