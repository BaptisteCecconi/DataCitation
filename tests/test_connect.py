# -*- coding: utf-8 -*-
"""Test module for connect.py"""

import json
import pytest
from requests import exceptions

from data_citation_reporter.connect import get


@pytest.fixture(name="test_url")
def fixture_url():
    """Test URL"""
    return "http://example.org/api"


@pytest.fixture(name="test_headers")
def fixture_headers():
    """Test headers"""
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
    mock_get.side_effect = exceptions.ConnectionError("Connection failed")

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
    mock_response.raise_for_status.side_effect = exceptions.HTTPError("404 Not Found")
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
    large_data = {"items": list(range(1000))}
    mock_response.json.return_value = large_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get(test_url, test_headers, use_cache=False)

    assert result == large_data
    assert len(result["items"]) == 1000


def test_get_empty_header(mocker, test_url):
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
    result_no_cache = get(test_url + "?get_cache", test_headers, use_cache=False)
    result_cache = get(test_url + "?get_cache", test_headers, use_cache=True)

    # Checking
    assert result_no_cache == result_cache


def test_set_cache(mocker, test_url, test_headers):
    """Test writing into cache"""

    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"key": "value", "data": "test"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = get(test_url + "?set_cache", test_headers, use_cache=False)
    mock_response.json.return_value = {"key": "value", "data": "test1"}
    result1 = get(test_url + "?set_cache", test_headers, update_cache=True)

    assert result == {"key": "value", "data": "test"}
    assert result1 == {"key": "value", "data": "test1"}
