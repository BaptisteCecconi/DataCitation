# test_datacite.py
from unittest.mock import patch

from data_citation_reporter.datacite import (
    get_single_doi,
    get_dois_from_prefix,
    check_datacite,
)
from data_citation_reporter.static import DATACITE_DOIS_URL


class TestGetSingleDoi:
    """Unit tests for the get_single_doi function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_doi = "10.1234/example.doi"
        self.expected_access_url = f"{DATACITE_DOIS_URL}/{self.test_doi}"
        self.test_data = {
            "data": {
                "id": "https://doi.org/10.1234/example.doi",
                "type": "dois",
                "attributes": {
                    "titles": [{"title": "Test Paper"}],
                    "creators": [{"name": "John Doe"}],
                    "publisher": "Test Publisher",
                },
            }
        }

    @patch("data_citation_reporter.datacite.get")
    def test_get_single_doi_success(self, mock_get):
        """Test successful retrieval of DOI metadata"""
        # Setup mock
        mock_get.return_value = self.test_data

        # Call the function
        result = get_single_doi(self.test_doi)

        # Verify the result
        assert result == self.test_data["data"]

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.datacite.get")
    def test_get_single_doi_api_error(self, mock_get):
        """Test when API returns None"""
        # Setup mock
        mock_get.return_value = None

        # Call the function
        result = get_single_doi(self.test_doi)

        # Verify the result
        assert result == {}

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.datacite.get")
    def test_get_single_doi_empty_data(self, mock_get):
        """Test when response contains empty data"""
        # Setup mock
        mock_get.return_value = {"data": {}}

        # Call the function
        result = get_single_doi(self.test_doi)

        # Verify the result
        assert result == {}

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)


class TestGetDoisFromPrefix:
    """Unit tests for the get_dois_from_prefix function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_prefix = "10.1234"
        self.initial_access_url = (
            f"{DATACITE_DOIS_URL}?prefix={self.test_prefix}&page%5Bsize%5D=50"
        )

        # Test data for first page
        self.first_page_data = {
            "data": [
                {"id": "10.1234/first.doi", "type": "dois"},
                {"id": "10.1234/second.doi", "type": "dois"},
            ],
            "links": {
                "next": "https://api.datacite.org/dois?prefix=10.1234&page%5Bsize%5D=50&page=2"
            },
        }

        # Test data for second page (final page)
        self.second_page_data = {
            "data": [
                {"id": "10.1234/third.doi", "type": "dois"},
                {"id": "10.1234/fourth.doi", "type": "dois"},
            ],
            "links": {},  # No next link, indicating final page
        }

    @patch("data_citation_reporter.datacite.get")
    def test_get_dois_from_prefix_single_page(self, mock_get):
        """Test with single page of results"""
        # Setup mock for single page
        single_page_data = {
            "data": [
                {"id": "10.1234/first.doi", "type": "dois"},
                {"id": "10.1234/second.doi", "type": "dois"},
            ],
            "links": {},  # No next link
        }
        mock_get.return_value = single_page_data

        # Call the function
        result = get_dois_from_prefix(self.test_prefix)

        # Verify the result
        assert len(result) == 2
        assert result[0]["id"] == "10.1234/first.doi"
        assert result[1]["id"] == "10.1234/second.doi"

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.initial_access_url)

    @patch("data_citation_reporter.datacite.get")
    def test_get_dois_from_prefix_multiple_pages(self, mock_get):
        """Test with multiple pages of results"""
        # Setup mock to return different data for each call
        mock_get.side_effect = [self.first_page_data, self.second_page_data]

        # Call the function
        result = get_dois_from_prefix(self.test_prefix)

        # Verify the result
        assert len(result) == 4
        dois = [item["id"] for item in result]
        assert "10.1234/first.doi" in dois
        assert "10.1234/second.doi" in dois
        assert "10.1234/third.doi" in dois
        assert "10.1234/fourth.doi" in dois

    @patch("data_citation_reporter.datacite.get")
    def test_get_dois_from_prefix_empty_data(self, mock_get):
        """Test with empty data array"""
        # Setup mock
        mock_get.return_value = {"data": [], "links": {}}

        # Call the function
        result = get_dois_from_prefix(self.test_prefix)

        # Verify the result
        assert result == []

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.initial_access_url)

    @patch("data_citation_reporter.datacite.get")
    def test_get_dois_from_prefix_custom_page_size(self, mock_get):
        """Test with custom page size"""
        custom_page_size = 100

        # Setup mock
        mock_get.return_value = {
            "data": [{"id": "10.1234/test.doi", "type": "dois"}],
            "links": {},
        }

        # Call the function with custom page size
        result = get_dois_from_prefix(
            self.test_prefix,
            api_url=f"{DATACITE_DOIS_URL}?prefix={self.test_prefix}&page%5Bsize%5D={custom_page_size}",
        )

        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == "10.1234/test.doi"


class TestCheckDatacite:
    """Unit tests for the check_datacite function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.src_uri = "https://doi.org/10.1234/source.doi"
        self.ref_uri = "https://doi.org/10.5678/reference.doi"

        # Test data with related identifiers
        self.test_response_with_reference = {
            "attributes": {
                "relatedIdentifiers": [
                    {
                        "relatedIdentifier": "10.5678/reference.doi",
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsCitedBy",
                    },
                    {
                        "relatedIdentifier": "10.9999/other.doi",
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsCitedBy",
                    },
                ]
            }
        }

        # Test data without the specific reference
        self.test_response_without_reference = {
            "attributes": {
                "relatedIdentifiers": [
                    {
                        "relatedIdentifier": "10.9999/other.doi",
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsCitedBy",
                    }
                ]
            }
        }

        # Test data without related identifiers
        self.test_response_no_related = {
            "attributes": {"relatedIdentifiers": []}
        }

    @patch("data_citation_reporter.datacite.get_single_doi")
    @patch("data_citation_reporter.datacite.shorten_doi")
    def test_check_datacite_found(self, mock_shorten_doi, mock_get_single_doi):
        """Test reference found in DataCite metadata"""
        # Setup mocks
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]
        mock_get_single_doi.return_value = self.test_response_with_reference

        # Call the function
        result = check_datacite(self.src_uri, self.ref_uri)

        # Verify the result
        assert result["found"] is True
        assert result["status"] == 2
        assert result["message"] == "Reference found in DataCite metadata."
        assert "reference" in result
        assert (
            result["reference"]["relatedIdentifier"] == "10.5678/reference.doi"
        )

    @patch("data_citation_reporter.datacite.get_single_doi")
    @patch("data_citation_reporter.datacite.shorten_doi")
    def test_check_datacite_not_found(
        self, mock_shorten_doi, mock_get_single_doi
    ):
        """Test reference not found in DataCite metadata"""
        # Setup mocks
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]
        mock_get_single_doi.return_value = self.test_response_without_reference

        # Call the function
        result = check_datacite(self.src_uri, self.ref_uri)

        # Verify the result
        assert result["found"] is False
        assert result["status"] == 0
        assert result["message"] == "Reference not found in DataCite metadata."
        assert "reference" not in result

    @patch("data_citation_reporter.datacite.get_single_doi")
    @patch("data_citation_reporter.datacite.shorten_doi")
    def test_check_datacite_no_related_identifiers(
        self, mock_shorten_doi, mock_get_single_doi
    ):
        """Test when DOI has no related identifiers"""
        # Setup mocks
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]
        mock_get_single_doi.return_value = self.test_response_no_related

        # Call the function
        result = check_datacite(self.src_uri, self.ref_uri)

        # Verify the result
        assert result["found"] is False
        assert result["status"] == 0
        assert result["message"] == "Reference not found in DataCite metadata."
        assert "reference" not in result
