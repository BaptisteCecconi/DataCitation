# test_nasa_ads.py
from unittest.mock import patch, mock_open
from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, RDF

from data_citation_reporter.nasa_ads import get_nasa_ads
from data_citation_reporter.rdf import URIRefDoi


class TestGetNasaAds:
    """Unit tests for the get_nasa_ads function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_api = "http://test.url/api"
        self.test_doi = "10.1234/example.doi"
        self.test_uri = URIRefDoi(f"https://doi.org/{self.test_doi}")
        self.expected_query = "full:10.1234/example.doi"
        self.expected_fl = "doi"
        self.expected_access_url = f"{self.test_api}/search/query?q={self.expected_query}&fl={self.expected_fl}"

        # Test data with results

        self.test_citing1 = "10.5678/first.doi"
        self.test_citing2 = "10.9999/second.doi"
        self.test_citing3 = "10.1111/third.doi"

        self.test_response_with_results = {
            "response": {
                "numFound": 2,
                "docs": [
                    {"doi": [self.test_citing1, self.test_citing2]},
                    {"doi": [self.test_citing3]},
                ],
            }
        }

        # Test data without results
        self.test_response_no_results = {
            "response": {"numFound": 0, "docs": []}
        }

    @patch("data_citation_reporter.nasa_ads.yaml.load")
    @patch("data_citation_reporter.nasa_ads.get")
    def test_get_nasa_ads_success(self, mock_get, mock_yaml):
        """Test successful processing with results"""
        # Setup mocks
        mock_yaml.return_value = {"ads": "test_token"}
        mock_token = "test_token"
        mock_api_url = self.test_api

        # Mock get response
        mock_get.return_value = self.test_response_with_results

        # Call the function
        result = get_nasa_ads(
            self.test_uri, api_url=mock_api_url, token=mock_token
        )

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 12  # 6 triples per citation × 2 unique citations

        # Verify the access URL construction
        expected_url = f"{self.test_api}/search/query?q=full%3A10.1234%2Fexample.doi&fl=doi"
        mock_get.assert_called_once_with(
            expected_url,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer test_token",
            },
        )

        for triple in result:
            print(triple)
        # Verify triple structure using mocked objects
        src_uri = URIRef(self.test_uri)
        assert (
            URIRefDoi(self.test_citing1),
            DCTERMS.references,
            src_uri,
        ) in result
        assert (
            URIRefDoi(self.test_citing3),
            DCTERMS.references,
            src_uri,
        ) in result
        assert (
            URIRefDoi(self.test_citing2),
            DCTERMS.references,
            src_uri,
        ) not in result

        # Check provenance triples
        statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
        assert len(statement_nodes) == 2  # 2 provenance statements

    @patch("data_citation_reporter.nasa_ads.yaml.load")
    @patch("data_citation_reporter.nasa_ads.get")
    def test_get_nasa_ads_no_results(self, mock_get, mock_yaml):
        """Test with no results found"""
        # Setup mocks
        mock_yaml.return_value = {"ads": "test_token"}
        mock_get.return_value = self.test_response_no_results

        # Call the function
        result = get_nasa_ads(
            self.test_uri, api_url=self.test_api, token="test_token"
        )

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # Empty graph returned

    @patch("data_citation_reporter.nasa_ads.yaml.load")
    @patch(
        "builtins.open", new_callable=mock_open, read_data="ads: test_token\n"
    )
    @patch("data_citation_reporter.nasa_ads.get")
    def test_get_nasa_ads_custom_api_url(self, mock_get, mock_open, mock_yaml):
        """Test with custom API URL"""
        # Setup mocks
        mock_yaml.return_value = {"ads": "test_token"}

        # Mock get response
        mock_get.return_value = self.test_response_with_results

        custom_api_url = "https://custom.api.example.org/v1"

        # Call the function with custom API URL
        result = get_nasa_ads(
            self.test_uri, api_url=custom_api_url, token="test_token"
        )

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 12  # 3 triples for first citation only

        # Verify the custom access URL was used
        expected_url = f"{custom_api_url}/search/query?q=full%3A10.1234%2Fexample.doi&fl=doi"
        mock_get.assert_called_once_with(
            expected_url,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer test_token",
            },
        )

    @patch("data_citation_reporter.nasa_ads.yaml.load")
    @patch(
        "builtins.open", new_callable=mock_open, read_data="ads: test_token\n"
    )
    @patch("data_citation_reporter.nasa_ads.get")
    @patch("data_citation_reporter.nasa_ads.shorten_doi")
    def test_get_nasa_ads_empty_doi_list(
        self, mock_shorten_doi, mock_get, mock_open, mock_yaml
    ):
        """Test with empty DOI list in result"""
        # Setup mocks
        mock_yaml.return_value = {"ads": "test_token"}
        mock_shorten_doi.return_value = self.test_doi

        # Test data with empty DOI list
        test_data_empty_doi = {
            "response": {"numFound": 1, "docs": [{"doi": []}]}
        }
        mock_get.return_value = test_data_empty_doi

        # Call the function
        result = get_nasa_ads(self.test_uri)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # No triples added for empty DOI list
