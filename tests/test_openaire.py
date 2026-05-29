# -*- coding: utf-8 -*-
# test_scholexplorer.py
# TODO: refactor test to remove unittest

from unittest.mock import patch
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF

from data_citation_reporter.openaire import get_openaire_graph
from data_citation_reporter.namespaces import BIBLINK, DCITE
from data_citation_reporter.rdf import URIRefDoi


class TestGetOpenaireGraph:
    """Unit tests for the get_openaire_graph function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_doi = "10.1234/example.doi"
        self.test_pid = URIRefDoi(f"https://doi.org/{self.test_doi}")
        self.expected_access_url = (
            f"https://api.openaire.eu/graph/v1/researchProducts/links?targetPid={self.test_doi}&page=0&pageSize=100"
        )

        # Test data with multiple results
        self.test_data = {
            "results": [
                {
                    "source": {
                        "identifiers": [
                            {
                                "idScheme": "doi",
                                "idUrl": "https://doi.org/10.5678/another.doi",
                            },
                            {
                                "idScheme": "other",
                                "idUrl": "other://identifier",
                            },
                        ]
                    },
                    "relType": {"typeSchema": "datacite", "name": "isCitedBy"},
                    "provenance": ["DataCite", "CrossRef"],
                },
                {
                    "source": {
                        "identifiers": [
                            {
                                "idScheme": "other",
                                "idUrl": "other://identifier",
                            },
                            {
                                "idScheme": "doi",
                                "idUrl": "https://doi.org/10.9999/test.doi",
                            },
                        ]
                    },
                    "relType": {"typeSchema": "datacite", "name": "references"},
                    "provenance": ["ORCID"],
                },
            ]
        }

    @patch("data_citation_reporter.openaire.requests.get")
    @patch("data_citation_reporter.openaire.URIRefDoi")
    def test_get_openaire_graph_success(self, mock_uri_ref_doi, mock_requests_get):
        """Test successful processing with multiple relations"""
        # Setup mocks
        mock_requests_get.return_value.json.return_value = self.test_data

        # Mock OPENAIRE_SCHEMAS
        mock_is_cited_by = DCITE.isCitedBy
        mock_references = DCITE.references

        # Mock URIRefDoi calls
        mock_src_pid1 = URIRef("https://doi.org/10.5678/another.doi")
        mock_src_pid2 = URIRef("https://doi.org/10.9999/test.doi")
        mock_uri_ref_doi.side_effect = [mock_src_pid1, mock_src_pid2]

        result = get_openaire_graph(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 14  # 7 triples per result × 2 results

        for item in result:
            print(item)

        # Verify triple structure
        assert (mock_src_pid1, mock_is_cited_by, self.test_pid) in result
        assert (mock_src_pid2, mock_references, self.test_pid) in result

        # Check BIBLINK.scheme triples
        assert (mock_src_pid1, BIBLINK.scheme, Literal("doi")) in result
        assert (mock_src_pid2, BIBLINK.scheme, Literal("doi")) in result

        # Check provenance triples
        statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
        assert len(statement_nodes) == 2  # 2 provenance statements

    @patch("data_citation_reporter.openaire.requests.get")
    @patch("data_citation_reporter.openaire.URIRefDoi")
    def test_get_openaire_graph_no_doi_source(self, mock_uri_ref_doi, mock_requests_get):
        """Test when no DOI is found in source identifiers"""
        # Setup mocks
        test_data_no_doi = {
            "results": [
                {
                    "source": {"identifiers": [{"idScheme": "other", "idUrl": "other://identifier"}]},
                    "relType": {"typeSchema": "citation", "name": "isCitedBy"},
                    "provenance": ["DataCite"],
                }
            ]
        }
        mock_requests_get.return_value.json.return_value = test_data_no_doi

        # Call the function
        result = get_openaire_graph(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # No triples added for non-DOI sources

    @patch("data_citation_reporter.openaire.requests.get")
    @patch("data_citation_reporter.openaire.URIRefDoi")
    def test_get_openaire_graph_empty_data(self, mock_uri_ref_doi, mock_requests_get):
        """Test with empty results"""
        # Setup mocks
        mock_requests_get.return_value.json.return_value = {"results": []}

        with patch("builtins.print") as mock_print:
            # Call the function
            result = get_openaire_graph(self.test_pid)

            # Verify the result
            assert isinstance(result, Graph)
            assert len(result) == 0  # No triples added

            # Verify print calls
            mock_print.assert_any_call(f"requesting {self.expected_access_url}")
            mock_print.assert_any_call(f"{self.test_doi}: 0")

            # Verify URIRefDoi was not called
            mock_uri_ref_doi.assert_not_called()

    @patch("data_citation_reporter.openaire.requests.get")
    @patch("data_citation_reporter.openaire.URIRefDoi")
    def test_get_openaire_graph_custom_api_url(self, mock_uri_ref_doi, mock_requests_get):
        """Test with custom API URL"""
        custom_api_url = "https://custom.api.example.org/graph/v1/researchProducts/links"

        # Setup mocks
        mock_requests_get.return_value.json.return_value = self.test_data

        # Mock URIRefDoi calls
        mock_src_pid1 = URIRef("https://doi.org/10.5678/another.doi")
        mock_uri_ref_doi.return_value = mock_src_pid1

        # Call the function with custom API URL
        result = get_openaire_graph(self.test_pid, api_url=custom_api_url)

        # Verify the result
        assert isinstance(result, Graph)
        for item in result:
            print(item)
        assert len(result) == 13  # 7 x 2 triples + 1 triple (source pid scheme)
