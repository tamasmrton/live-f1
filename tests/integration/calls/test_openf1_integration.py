import pytest
from calls.openf1 import OpenF1Connector


@pytest.fixture
def connector():
    return OpenF1Connector()


def test_get_meetings(connector):
    response = connector.get_meetings()
    assert response.status_code == 200
    data = response.json()
    expected_keys = [
        "circuit_key",
        "circuit_short_name",
        "meeting_key",
        "meeting_code",
        "location",
        "country_key",
        "country_code",
        "country_name",
        "meeting_name",
        "meeting_official_name",
        "gmt_offset",
        "date_start",
        "year",
    ]
    for item in data:
        actual_keys = list(item.keys())
        assert expected_keys.sort() == actual_keys.sort()


def test_get_drivers(connector):
    meeting_key = 1219
    response = connector.get_drivers(meeting_key)
    assert response.status_code == 200
    data = response.json()
    expected_keys = [
        "driver_number",
        "broadcast_name",
        "full_name",
        "name_acronym",
        "team_name",
        "team_colour",
        "first_name",
        "last_name",
        "headshot_url",
        "country_code",
        "session_key",
        "meeting_key",
    ]
    for item in data:
        actual_keys = list(item.keys())
        assert expected_keys.sort() == actual_keys.sort()


def test_get_sessions(connector):
    meeting_key = 1219
    session_name = "Race"
    response = connector.get_sessions(meeting_key, session_name)
    assert response.status_code == 200
    data = response.json()
    expected_keys = [
        "location",
        "country_key",
        "country_code",
        "country_name",
        "circuit_key",
        "circuit_short_name",
        "session_type",
        "session_name",
        "date_start",
        "date_end",
        "gmt_offset",
        "session_key",
        "meeting_key",
        "year",
    ]
    for item in data:
        actual_keys = list(item.keys())
        assert expected_keys.sort() == actual_keys.sort()


def test_get_laps(connector):
    session_key = 9158
    response = connector.get_laps(session_key)
    assert response.status_code == 200
    data = response.json()
    expected_keys = [
        "meeting_key",
        "session_key",
        "driver_number",
        "i1_speed",
        "i2_speed",
        "st_speed",
        "date_start",
        "lap_duration",
        "is_pit_out_lap",
        "duration_sector_1",
        "duration_sector_2",
        "duration_sector_3",
        "segments_sector_1",
        "segments_sector_2",
        "segments_sector_3",
        "lap_number",
    ]
    for item in data:
        actual_keys = list(item.keys())
        assert expected_keys.sort() == actual_keys.sort()


def test_get_pits(connector):
    session_key = 9158
    response = connector.get_pits(session_key)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    expected_keys = [
        "date",
        "driver_number",
        "lap_number",
        "meeting_key",
        "pit_duration",
        "session_key",
    ]
    for item in data:
        actual_keys = list(item.keys())
        assert expected_keys.sort() == actual_keys.sort()
