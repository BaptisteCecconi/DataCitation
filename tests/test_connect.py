# -*- coding: utf-8 -*-
# test_api_client.py

import pytest
from requests.exceptions import ConnectionError, HTTPError
import json

from data_citation_reporter.connect import get


@pytest.fixture
def test_url():
    return "http://example.org/api"


@pytest.fixture
def test_headers():
    return {"Authorization": "Bearer token123"}


def test_get_success(mocker, test_url, test_headers):
    """Success test - status 200 with valid JSON output"""
    # Mock of the response
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"key": "value", "data": "test"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Calling the function
    result = get(test_url, test_headers, use_cache=False)

    # Checking
    assert result == {"key": "value", "data": "test"}


def test_get_connection_error(mocker, test_url, test_headers):
    """Test with connection error"""
    # Simulate a connection error
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = ConnectionError("Connection failed")

    # Capture the print output
    mock_print = mocker.patch("builtins.print")

    result = get(test_url, test_headers, use_cache=False)

    # Verify that the function returns None
    assert result is None

    # Verify that the error message was printed
    mock_print.assert_any_call("Connection failed")


def test_get_http_error(mocker, test_url, test_headers):
    """Test with HTTP error (ex: 404, 500, etc.)"""
    # Mock the response with HTTP error
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
    mock_get.return_value = mock_response

    mock_print = mocker.patch("builtins.print")

    result = get(test_url, test_headers, use_cache=False)

    # Verify that the function returns None
    assert result is None

    # Verify that the error message was printed
    mock_print.assert_any_call("HTTP error occurred:", "404 Not Found")


def test_get_json_decode_error(mocker, test_url, test_headers):
    """Test with response that is not valid JSON"""
    # Mock the response with invalid JSON
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = json.decoder.JSONDecodeError("Invalid JSON", "", 0)
    mock_get.return_value = mock_response

    mock_print = mocker.patch("builtins.print")

    result = get(test_url, test_headers, use_cache=False)

    # Verify that the function returns None
    assert result is None

    # Verify that the error message was printed
    mock_print.assert_called_with("Invalid JSON: line 1 column 1 (char 0)")


def test_get_empty_response(mocker, test_url, test_headers):
    """Test with empty JSON response"""
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get(test_url, test_headers, use_cache=False)

    assert result == {}


def test_get_large_response(mocker, test_url, test_headers):
    """Test with large JSON response"""
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    large_data = {"items": [i for i in range(1000)]}
    mock_response.json.return_value = large_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get(test_url, test_headers, use_cache=False)

    assert result == large_data
    assert len(result["items"]) == 1000


def test_get_empty_header(mocker, test_url, test_headers):
    """Test with empty header"""
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"key": "value", "data": "test"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get(test_url, use_cache=False)

    assert result == {"key": "value", "data": "test"}


def test_get_cache(mocker, test_url, test_headers):
    """Success test - status 200 with valid JSON output"""
    # Mock of the response
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"key": "value", "data": "test"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Calling the function
    result_no_cache = get(test_url, test_headers, use_cache=False)
    result_cache = get(test_url, test_headers, use_cache=True)

    # Checking
    assert result_no_cache == result_cache
