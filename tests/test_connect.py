# -*- coding: utf-8 -*-
# test_api_client.py
from unittest.mock import patch, Mock
from requests.exceptions import ConnectionError, HTTPError
import json

from data_citation_reporter.connect import get


class TestGetAPI:
    """Unit test for the `get()` function"""

    def setup_method(self):
        """Init before each test"""
        self.test_url = "http://example.com/api"
        self.test_headers = {"Authorization": "Bearer token123"}

    @patch("requests.get")
    def test_get_success(self, mock_get):
        """Success test - status 200 with valid JSON output"""
        # Mock of the response
        with patch("builtins.print") as mock_print:
            mock_response = Mock()
            mock_response.json.return_value = {"key": "value", "data": "test"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Calling the function
            result = get(self.test_url, self.test_headers)

            # Checking
            assert result == {"key": "value", "data": "test"}

            # Verify that raise_for_status was called
            mock_get.assert_called_once_with(
                self.test_url, headers=self.test_headers
            )
            mock_response.raise_for_status.assert_called_once()

            # Verify that the requested url message is called
            mock_print.assert_called_once_with(
                "requesting http://example.com/api"
            )

    @patch("requests.get")
    def test_get_connection_error(self, mock_get):
        """Test with connection error"""
        # Simulate a connection error
        mock_get.side_effect = ConnectionError("Connection failed")

        # Capture the print output
        with patch("builtins.print") as mock_print:
            result = get(self.test_url, self.test_headers)

            # Verify that the function returns None
            assert result is None

            # Verify that the error message was printed
            mock_print.assert_any_call("Connection failed")

    @patch("requests.get")
    def test_get_http_error(self, mock_get):
        """Test with HTTP error (ex: 404, 500, etc.)"""
        # Mock the response with HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            result = get(self.test_url, self.test_headers)

            # Verify that the function returns None
            assert result is None

            # Verify that the error message was printed
            mock_print.assert_any_call("HTTP error occurred:", "404 Not Found")

    @patch("requests.get")
    def test_get_json_decode_error(self, mock_get):
        """Test with response that is not valid JSON"""
        # Mock the response with invalid JSON
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.decoder.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            result = get(self.test_url, self.test_headers)

            # Verify that the function returns None
            assert result is None

            # Verify that the error message was printed
            mock_print.assert_called_with(
                "Invalid JSON: line 1 column 1 (char 0)"
            )

    @patch("requests.get")
    def test_get_request_print(self, mock_get):
        """Test that the request message is printed"""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            # Verify that the request message was printed
            mock_print.assert_called_once_with(f"requesting {self.test_url}")

    @patch("requests.get")
    def test_get_empty_response(self, mock_get):
        """Test with empty JSON response"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get(self.test_url, self.test_headers)

        assert result == {}
        mock_get.assert_called_once_with(
            self.test_url, headers=self.test_headers
        )

    @patch("requests.get")
    def test_get_large_response(self, mock_get):
        """Test with large JSON response"""
        large_data = {"items": [i for i in range(1000)]}
        mock_response = Mock()
        mock_response.json.return_value = large_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get(self.test_url, self.test_headers)

        assert result == large_data
        assert len(result["items"]) == 1000

    @patch("requests.get")
    def test_get_empty_header(self, mock_get):
        """Test with empty header"""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value", "data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get(self.test_url)

        assert result == {"key": "value", "data": "test"}
