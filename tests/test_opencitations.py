# -*- coding: utf-8 -*-
# test_opencitations.py
# TODO: refactor test to remove unittest
from unittest.mock import patch
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCTERMS, PROV, RDF

from data_citation_reporter.opencitations import get_opencitations
from data_citation_reporter.static import OPENCITATIONS_URL
from data_citation_reporter.namespaces import BIBLINK


class TestGetOpenCitations:
    """Unit tests for the get_opencitations function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_doi = "10.1234/example.doi"
        self.test_pid = f"https://doi.org/{self.test_doi}"
        self.expected_access_url = f"{OPENCITATIONS_URL}/citations/{self.test_doi}"

        self.test_data = [
            {"citing": "10.5678/another.doi"},
            {"citing": "10.9999/test.doi"},
        ]

        self.expected_citation_set = {
            ("10.5678/another.doi", "doi"),
            ("10.9999/test.doi", "doi"),
        }

    @patch("data_citation_reporter.opencitations.get")
    def test_get_opencitations_success(self, mock_get):
        """Test successful processing with citation data"""
        # Mock the get function
        mock_get.return_value = self.test_data

        # Call the function
        result = get_opencitations(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 14  # 7 triples per citation × 3 unique citations

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

        # Verify triple structure
        src_uri = URIRef(f"https://doi.org/{self.test_doi}".lower())
        citing_uris = [URIRef(f"https://doi.org/{cite[0]}".lower()) for cite in self.expected_citation_set]

        # Check DCTERMS.references triples
        for citing_uri in citing_uris:
            assert (citing_uri, DCTERMS.references, src_uri) in result

        # Check BIBLINK.scheme triples with actual schema values
        for citing_uri, schema in self.expected_citation_set:
            expected_uri = URIRef(f"https://doi.org/{citing_uri}".lower())
            assert (expected_uri, BIBLINK.scheme, Literal(schema)) in result

    @patch("data_citation_reporter.opencitations.get")
    def test_get_opencitations_success_empty_data(self, mock_get):
        """Test with empty citation data"""
        # Mock the get function with empty data
        mock_get.return_value = []

        # Call the function
        result = get_opencitations(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # No triples added

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.opencitations.get")
    def test_get_opencitations_api_error(self, mock_get):
        """Test when API returns None (connection error)"""
        # Mock the get function to return None
        mock_get.return_value = None

        # Call the function
        result = get_opencitations(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # Empty graph returned

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.opencitations.get")
    def test_get_opencitations_custom_api_url(self, mock_get):
        """Test with custom API URL"""
        custom_api_url = "https://custom.api.example.org/"
        expected_custom_url = f"{custom_api_url}/citations/{self.test_doi}"

        # Mock the get function
        mock_get.return_value = self.test_data

        # Call the function with custom API URL
        result = get_opencitations(self.test_pid, api_url=custom_api_url)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 14

        # Verify the custom URL was used
        mock_get.assert_called_once_with(expected_custom_url)

    @patch("data_citation_reporter.opencitations.get")
    def test_get_opencitations_provenance(self, mock_get):
        """Test that provenance metadata is added correctly"""
        # Mock the get function
        mock_get.return_value = self.test_data

        # Call the function
        result = get_opencitations(self.test_pid)

        # Verify provenance triples exist
        statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
        assert len(statement_nodes) == 2  # 3 unique citations

        for statement_node in statement_nodes:
            # Check that each statement has the correct provenance
            assert (
                statement_node,
                PROV.wasInformedBy,
                Literal("OpenCitations"),
            ) in result
