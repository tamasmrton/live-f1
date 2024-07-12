import pendulum
from unittest.mock import patch
from calls.openf1 import OpenF1Connector  # Adjust import as necessary


def test_format_timestamp():
    connector = OpenF1Connector()
    ts = pendulum.datetime(2024, 7, 5, 12, 0, 0)
    assert connector.format_timestamp(ts) == "2024-07-05T12:00:00Z"


@patch("pendulum.today")
def test_get_meetings(mock_today, requests_mock):
    mock_today.return_value = pendulum.datetime(
        2024, 7, 5, 12, 0, 0
    )  # 2024-07-05 is a Friday
    connector = OpenF1Connector()

    requests_mock.get(
        "https://api.openf1.org/v1/meetings",
        json={"data": "meetings_data"},
        status_code=200,
    )

    response = connector.get_meetings()

    assert response.status_code == 200
    assert response.json() == {"data": "meetings_data"}


def test_get_drivers(requests_mock):
    connector = OpenF1Connector()
    meeting_key = 123
    requests_mock.get(
        "https://api.openf1.org/v1/drivers",
        json={"data": "drivers_data"},
        status_code=200,
    )
    response = connector.get_drivers(meeting_key)
    assert response.status_code == 200
    assert response.json() == {"data": "drivers_data"}


def test_get_sessions(requests_mock):
    connector = OpenF1Connector()
    meeting_key = 123
    session_name = "Qualifying"
    requests_mock.get(
        "https://api.openf1.org/v1/sessions",
        json={"data": "sessions_data"},
        status_code=200,
    )
    response = connector.get_sessions(meeting_key, session_name)
    assert response.status_code == 200
    assert response.json() == {"data": "sessions_data"}


def test_get_laps(requests_mock):
    connector = OpenF1Connector()
    session_key = 456
    requests_mock.get(
        "https://api.openf1.org/v1/laps", json={"data": "laps_data"}, status_code=200
    )
    response = connector.get_laps(session_key)
    assert response.status_code == 200
    assert response.json() == {"data": "laps_data"}


def test_get_pits(requests_mock):
    connector = OpenF1Connector()
    session_key = 789
    requests_mock.get(
        "https://api.openf1.org/v1/pit", json={"data": "pits_data"}, status_code=200
    )
    response = connector.get_pits(session_key)
    assert response.status_code == 200
    assert response.json() == {"data": "pits_data"}
