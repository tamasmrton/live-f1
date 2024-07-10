import pytest
import requests
import requests_mock
from unittest.mock import patch
from time import sleep

from utils.requests_wrapper import get

# Sample endpoint and params
endpoint = "https://example.com/api"
params = {"key": "value"}


def test_get_success(requests_mock):
    requests_mock.get(endpoint, json={"data": "value"}, status_code=200)

    response = get(endpoint, params)

    assert response.status_code == 200
    assert response.json() == {"data": "value"}


def test_get_retry_and_success(requests_mock):
    requests_mock.get(
        endpoint,
        [
            {"status_code": 500},
            {"status_code": 500},
            {"json": {"data": "value"}, "status_code": 200},
        ],
    )

    with patch("utils.requests_wrapper.sleep", return_value=None):
        response = get(endpoint, params, retries=3)

    assert response.status_code == 200
    assert response.json() == {"data": "value"}


def test_get_fail_after_retries(requests_mock):
    requests_mock.get(endpoint, status_code=500)

    with patch("utils.requests_wrapper.sleep", return_value=None):
        response = get(endpoint, params, retries=3)

    assert response.status_code == 500
