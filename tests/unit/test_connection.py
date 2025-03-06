from unittest.mock import patch, MagicMock, PropertyMock
import pytest
import pandas as pd
from duckdb import ConnectionException
from reporting.connection import MotherDuckConnection, MotherDuckSettings


@pytest.fixture
def mock_settings() -> MotherDuckSettings:
    settings = MotherDuckSettings(
        motherduck_token="test_token", motherduck_database="test_db"
    )
    with patch.object(
        MotherDuckConnection,
        "settings",
        new_callable=PropertyMock,
        return_value=settings,
    ):
        yield settings


@pytest.fixture
def mock_connection(mock_settings: MotherDuckSettings) -> tuple[MagicMock, MagicMock]:
    with patch("reporting.connection.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        yield mock_connect, mock_conn


def test_successful_connection(
    mock_settings: MotherDuckSettings, mock_connection: tuple[MagicMock, MagicMock]
):
    mock_connect, mock_conn = mock_connection
    connection = MotherDuckConnection()

    with connection.connect() as conn:
        assert conn == mock_conn
        expected_conn_str = "md:test_db?motherduck_token=test_token"
        mock_connect.assert_called_once_with(database=expected_conn_str)


def test_connection_failure(
    mock_settings: MotherDuckSettings, mock_connection: tuple[MagicMock, MagicMock]
):
    mock_connect, _ = mock_connection
    mock_connect.side_effect = ConnectionException("Connection failed")
    connection = MotherDuckConnection()

    with pytest.raises(ConnectionException):
        with connection.connect():
            pass


def test_execute_query_with_params(
    mock_settings: MotherDuckSettings, mock_connection: tuple[MagicMock, MagicMock]
):
    _, mock_conn = mock_connection
    mock_df = MagicMock(spec=pd.DataFrame)
    mock_conn.execute.return_value.df.return_value = mock_df

    connection = MotherDuckConnection()
    query = "SELECT * FROM test WHERE id = ?"
    params = [1]

    result = connection.execute_query(query, params)

    assert result == mock_df
    mock_conn.execute.assert_called_once_with(query, params)


def test_execute_query_without_params(
    mock_settings: MotherDuckSettings, mock_connection: tuple[MagicMock, MagicMock]
):
    _, mock_conn = mock_connection
    mock_df = MagicMock(spec=pd.DataFrame)
    mock_conn.execute.return_value.df.return_value = mock_df

    connection = MotherDuckConnection()
    query = "SELECT * FROM test"

    result = connection.execute_query(query)

    assert result == mock_df
    mock_conn.execute.assert_called_once_with(query, None)


def test_connection_cleanup(
    mock_settings: MotherDuckSettings, mock_connection: tuple[MagicMock, MagicMock]
):
    _, mock_conn = mock_connection
    connection = MotherDuckConnection()

    with connection.connect():
        pass

    mock_conn.close.assert_called_once()
