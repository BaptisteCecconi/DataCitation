# test_crossref.py
from unittest.mock import patch
from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from data_citation_reporter.crossref import (
    get_single_doi,
    get_datacitations,
    check_crossref,
)
from data_citation_reporter.static import (
    CROSSREF_DATACITATIONS_URL,
    CROSSREF_WORKS_URL,
)
from data_citation_reporter.namespaces import DCITE
from data_citation_reporter.rdf import URIRefDoi


class TestGetSingleDoi:
    """Unit tests for the get_single_doi function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_doi = URIRefDoi("10.1234/example.doi")
        self.expected_access_url = f"{CROSSREF_WORKS_URL}/{self.test_doi}"
        self.test_message = {
            "title": ["Test Paper"],
            "author": [{"given": "John", "family": "Doe"}],
            "published": {"date-parts": []},
        }

    @patch("data_citation_reporter.crossref.get")
    def test_get_single_doi_success(self, mock_get):
        """Test successful retrieval of DOI metadata"""
        # Setup mock
        mock_get.return_value = {"message": self.test_message}

        # Call the function
        result = get_single_doi(self.test_doi)

        # Verify the result
        assert result == self.test_message

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
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


class TestGetDatacitations:
    """Unit tests for the get_datacitations function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.test_doi = "10.1234/example.doi"
        self.test_pid = f"https://doi.org/{self.test_doi}"
        self.expected_access_url = (
            f"{CROSSREF_DATACITATIONS_URL}?object-id={self.test_doi}"
        )

        self.test_data = {
            "message": {
                "total-results": 2,
                "items": [
                    {
                        "subject": {"id": "10.5678/subject.doi"},
                        "object": {"id": "10.9999/object.doi"},
                        "relation": "isCitedBy",
                    },
                    {
                        "subject": {"id": "10.1111/subject2.doi"},
                        "object": {"id": "10.2222/object2.doi"},
                        "relation": "references",
                    },
                ],
            }
        }

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    @patch("data_citation_reporter.crossref.URIRefDoi")
    @patch("data_citation_reporter.crossref.CROSSREF_RELATIONS")
    def test_get_datacitations_success(
        self, mock_relations, mock_uri_ref_doi, mock_shorten_doi, mock_get
    ):
        """Test successful processing of datacitations"""
        # Setup mocks
        mock_get.return_value = self.test_data
        mock_shorten_doi.return_value = self.test_doi

        # Mock URIRefDoi calls
        mock_subject1 = URIRef("https://doi.org/10.5678/subject.doi")
        mock_object1 = URIRef("https://doi.org/10.9999/object.doi")
        mock_subject2 = URIRef("https://doi.org/10.1111/subject2.doi")
        mock_object2 = URIRef("https://doi.org/10.2222/object2.doi")
        mock_uri_ref_doi.side_effect = [
            mock_subject1,
            mock_object1,
            mock_subject2,
            mock_object2,
        ]

        # Mock relations
        mock_is_cited_by = DCITE.isCitedBy
        mock_references = DCITE.references
        mock_relations.__getitem__.side_effect = [
            mock_is_cited_by,
            mock_references,
        ]

        # Call the function
        result = get_datacitations(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 12  # 6 provenance statements × 2 relations

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

        # Verify triple structure
        # Check DCTERMS relations
        assert (mock_subject1, mock_is_cited_by, mock_object1) in result
        assert (mock_subject2, mock_references, mock_object2) in result

        # Check provenance triples
        statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
        assert (
            len(statement_nodes) == 2
        )  # 1 provenance statements × 2 relations

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_get_datacitations_api_error(self, mock_shorten_doi, mock_get):
        """Test when API returns None"""
        # Setup mocks
        mock_get.return_value = None
        mock_shorten_doi.return_value = self.test_doi

        # Call the function
        result = get_datacitations(self.test_pid)

        # Verify the result
        assert isinstance(result, Graph)
        assert len(result) == 0  # Empty graph returned

        # Verify the access URL construction
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_get_datacitations_no_results(self, mock_shorten_doi, mock_get):
        """Test with no results"""
        # Setup mocks
        mock_get.return_value = {"message": {"total-results": 0, "items": []}}
        mock_shorten_doi.return_value = self.test_doi

        with patch("builtins.print") as mock_print:
            # Call the function
            result = get_datacitations(self.test_pid)

            # Verify the result
            assert isinstance(result, Graph)
            assert len(result) == 0  # No triples added

            # Verify print call
            mock_print.assert_any_call(f"{self.test_doi}: 0")


class TestCheckCrossref:
    """Unit tests for the check_crossref function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.src_uri = "https://doi.org/10.1234/source.doi"
        self.ref_uri = "https://doi.org/10.5678/reference.doi"
        self.ref_title = "Test Reference Title"
        self.expected_access_url = (
            "https://api.crossref.org/works/10.1234/source.doi"
        )

        self.test_data_with_references = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.5678/reference.doi",
                        "unstructured": "Doe, J. (2023). Test Reference Title. Journal of Tests, 10(1), 123-456.",
                    },
                    {
                        "DOI": "10.9999/other.doi",
                        "unstructured": "Another Author (2023). Another Paper. Journal of Others, 20(2), 789-012.",
                    },
                ]
            }
        }

        self.test_data_without_references = {
            "message": {
                "title": ["Test Paper"],
                "author": [{"given": "John", "family": "Doe"}],
            }
        }

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_found_by_doi(self, mock_shorten_doi, mock_get):
        """Test reference found by exact DOI match"""
        # Setup mocks
        mock_get.return_value = self.test_data_with_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)

        # Verify the result
        assert result["found"] is True
        assert result["status"] == 2
        assert (
            result["message"]
            == "Found 10.5678/reference.doi in formatted reference"
        )
        assert "reference" in result

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_found_by_doi_in_field(
        self, mock_shorten_doi, mock_get
    ):
        """Test reference found by DOI in reference field"""
        # Setup mocks
        mock_get.return_value = self.test_data_with_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Modify test data to have DOI in unstructured field instead of DOI field
        test_data_modified = self.test_data_with_references.copy()
        test_data_modified["message"]["reference"][0]["DOI"] = ""
        test_data_modified["message"]["reference"][0][
            "unstructured"
        ] = "See 10.5678/reference.doi for more details"

        mock_get.return_value = test_data_modified

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)

        # Verify the result
        assert result["found"] is True
        assert result["status"] == 1
        assert "reference" in result

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_found_by_title(self, mock_shorten_doi, mock_get):
        """Test reference found by title match"""
        # Setup mocks
        mock_get.return_value = self.test_data_with_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Modify test data to have title match
        test_data_modified = self.test_data_with_references.copy()
        test_data_modified["message"]["reference"][0]["DOI"] = ""
        test_data_modified["message"]["reference"][0][
            "unstructured"
        ] = "Doe, J. (2023). Test Reference Title. Journal of Tests, 10(1), 123-456"

        mock_get.return_value = test_data_modified

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)
        print(
            self.ref_title
            in test_data_modified["message"]["reference"][0][
                "unstructured"
            ].lower()
        )

        # Verify the result
        assert result["found"] is True
        assert result["status"] == 1
        assert "reference" in result

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_found_by_fuzzy_match(
        self, mock_shorten_doi, mock_get
    ):
        """Test reference found by fuzzy title match"""
        # Setup mocks
        mock_get.return_value = self.test_data_with_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Modify test data to have partial title match
        test_data_modified = self.test_data_with_references.copy()
        test_data_modified["message"]["reference"][0]["DOI"] = ""
        test_data_modified["message"]["reference"][0][
            "unstructured"
        ] = "Test Reference"

        mock_get.return_value = test_data_modified

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)

        # Verify the result
        assert result["found"] is True
        assert result["status"] == 1
        assert "reference" in result
        assert "71%" in result["message"]

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_not_found(self, mock_shorten_doi, mock_get):
        """Test reference not found"""
        # Setup mocks
        mock_get.return_value = self.test_data_without_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)

        # Verify the result
        assert result["found"] is False
        assert result["status"] == 0
        assert result["message"] == "Reference not found in CrossRef metadata."
        assert "reference" not in result

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)

    @patch("data_citation_reporter.crossref.get")
    @patch("data_citation_reporter.crossref.shorten_doi")
    def test_check_crossref_no_references_section(
        self, mock_shorten_doi, mock_get
    ):
        """Test when response doesn't have references section"""
        # Setup mocks
        mock_get.return_value = self.test_data_without_references
        mock_shorten_doi.side_effect = [
            "10.1234/source.doi",
            "10.5678/reference.doi",
        ]

        # Call the function
        result = check_crossref(self.src_uri, self.ref_uri, self.ref_title)

        # Verify the result
        assert result["found"] is False
        assert result["status"] == 0
        assert result["message"] == "Reference not found in CrossRef metadata."

        # Verify function calls
        mock_get.assert_called_once_with(self.expected_access_url)
