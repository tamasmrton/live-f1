from unittest.mock import MagicMock
import pytest
import pandas as pd
from reporting.runner import ReportingRunner
from reporting.query_registry import QueryRegistry
from reporting.connection import MotherDuckConnection


@pytest.fixture
def mock_query_registry() -> MagicMock:
    query_registry = MagicMock(spec=QueryRegistry)
    query_registry.get_query.return_value = "SELECT * FROM test"
    return query_registry


@pytest.fixture
def mock_connection() -> MagicMock:
    connection = MagicMock(spec=MotherDuckConnection)
    return connection


@pytest.fixture
def runner(
    mock_query_registry: MagicMock, mock_connection: MagicMock
) -> ReportingRunner:
    return ReportingRunner(
        query_registry=mock_query_registry, connection=mock_connection
    )


def test_get_race_weekends(
    runner: ReportingRunner, mock_query_registry: MagicMock, mock_connection: MagicMock
) -> None:
    """Test fetching race weekend data."""
    # Arrange
    expected_df = pd.DataFrame({"race_weekend": ["Test GP 2024"]})
    mock_connection.execute_query.return_value = expected_df

    # Act
    result = runner._get_race_weekends()

    # Assert
    mock_query_registry.get_query.assert_called_once_with(query_name="f1_race_weekends")
    mock_connection.execute_query.assert_called_once_with("SELECT * FROM test")
    pd.testing.assert_frame_equal(result, expected_df)


def test_get_lap_data(
    runner: ReportingRunner, mock_query_registry: MagicMock, mock_connection: MagicMock
) -> None:
    """Test fetching lap data for a specific session."""
    # Arrange
    session_key = 123
    expected_df = pd.DataFrame({"lap_number": [1, 2, 3]})
    mock_connection.execute_query.return_value = expected_df

    # Act
    result = runner._get_lap_data(sessions_key=session_key)

    # Assert
    mock_query_registry.get_query.assert_called_once_with(query_name="f1_laps")
    mock_connection.execute_query.assert_called_once_with(
        "SELECT * FROM test", params=[session_key]
    )
    pd.testing.assert_frame_equal(result, expected_df)


def test_get_drivers(
    runner: ReportingRunner, mock_query_registry: MagicMock, mock_connection: MagicMock
) -> None:
    """Test fetching drivers for a specific session."""
    # Arrange
    session_key = 123
    expected_df = pd.DataFrame({"driver_name": ["Driver 1", "Driver 2"]})
    mock_connection.execute_query.return_value = expected_df

    # Act
    result = runner._get_drivers(sessions_key=session_key)

    # Assert
    mock_query_registry.get_query.assert_called_once_with(query_name="f1_drivers")
    mock_connection.execute_query.assert_called_once_with(
        "SELECT * FROM test", params=[session_key]
    )
    pd.testing.assert_frame_equal(result, expected_df)
