# test_registration_agency.py
import pytest

from unittest.mock import patch

from data_citation_reporter.doi import get_registration_agency
from data_citation_reporter.static import DOI_RA_URL


class TestGetRegistrationAgency:
    """Unit tests for the get_registration_agency function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_uri = "https://doi.org/10.1234/example.doi"
        self.expected_doi = "10.1234/example.doi"
        self.expected_api_url = f"{DOI_RA_URL}{self.expected_doi}"
        self.test_data = [{"RA": "Test Registration Agency"}]
        self.test_data_no_ra = [{"status": "not found"}]

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_success(self, mock_shorten_doi, mock_get):
        """Test successful retrieval of registration agency"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = self.test_data

        # Call the function
        result = get_registration_agency(self.test_uri)

        # Verify the result
        assert result == "Test Registration Agency"

        # Verify function calls
        mock_shorten_doi.assert_called_once_with(self.test_uri)
        mock_get.assert_called_once_with(self.expected_api_url)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_with_custom_api_url(
        self, mock_shorten_doi, mock_get
    ):
        """Test with custom API URL"""
        custom_api_url = "https://custom.api.example.org/"
        expected_custom_url = f"{custom_api_url}{self.expected_doi}"

        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = self.test_data

        # Call the function with custom API URL
        result = get_registration_agency(self.test_uri, api_url=custom_api_url)

        # Verify the result
        assert result == "Test Registration Agency"

        # Verify function calls
        mock_shorten_doi.assert_called_once_with(self.test_uri)
        mock_get.assert_called_once_with(expected_custom_url)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_api_error(
        self, mock_shorten_doi, mock_get
    ):
        """Test RuntimeError when API returns None"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = None  # API error

        # Call and verify exception
        with pytest.raises(
            RuntimeError,
            match=f"Could not get data from {self.expected_api_url}",
        ):
            get_registration_agency(self.test_uri)

        # Verify function calls
        mock_shorten_doi.assert_called_once_with(self.test_uri)
        mock_get.assert_called_once_with(self.expected_api_url)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_no_ra_key(
        self, mock_shorten_doi, mock_get
    ):
        """Test ValueError when 'RA' key is missing from response"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = self.test_data_no_ra

        # Call and verify exception
        with pytest.raises(
            ValueError, match="not found: https://doi.org/10.1234/example.doi"
        ):
            get_registration_agency(self.test_uri)

        # Verify function calls
        mock_shorten_doi.assert_called_once_with(self.test_uri)
        mock_get.assert_called_once_with(self.expected_api_url)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_empty_response_list(
        self, mock_shorten_doi, mock_get
    ):
        """Test ValueError when response list is empty"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = []  # Empty list

        # Call and verify exception (should raise IndexError when accessing )
        with pytest.raises(IndexError):
            get_registration_agency(self.test_uri)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_multiple_items(
        self, mock_shorten_doi, mock_get
    ):
        """Test function behavior with multiple items in response (should use first)"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = [
            {"RA": "First Agency", "status": "ok"},
            {"RA": "Second Agency", "status": "ok"},
        ]

        # Call the function
        result = get_registration_agency(self.test_uri)

        # Verify the result (should return first item's RA)
        assert result == "First Agency"

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_complex_status(
        self, mock_shorten_doi, mock_get
    ):
        """Test with complex status message"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = [{"status": "DOI does not exist"}]

        # Call and verify exception
        with pytest.raises(
            ValueError,
            match="DOI does not exist: https://doi.org/10.1234/example.doi",
        ):
            get_registration_agency(self.test_uri)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_url_construction(
        self, mock_shorten_doi, mock_get
    ):
        """Test that the API URL is constructed correctly"""
        # Setup mocks
        mock_shorten_doi.return_value = "10.5678/another.doi"
        mock_get.return_value = self.test_data

        # Call the function with different DOI
        different_uri = "https://doi.org/10.5678/another.doi"
        get_registration_agency(different_uri)

        # Verify the URL construction
        expected_url = f"{DOI_RA_URL}10.5678/another.doi"
        mock_get.assert_called_once_with(expected_url)

    @patch("data_citation_reporter.doi.get")
    @patch("data_citation_reporter.doi.shorten_doi")
    def test_get_registration_agency_error_messages_include_full_uri(
        self, mock_shorten_doi, mock_get
    ):
        """Test that error messages include the full original URI"""
        # Setup mocks
        mock_shorten_doi.return_value = self.expected_doi
        mock_get.return_value = self.test_data_no_ra

        # Call and verify exception with full URI
        with pytest.raises(
            ValueError, match="not found: https://doi.org/10.1234/example.doi"
        ):
            get_registration_agency(self.test_uri)
