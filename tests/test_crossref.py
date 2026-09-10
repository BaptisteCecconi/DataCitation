# -*- coding: utf-8 -*-
# test_crossref.py

import pytest
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

"""Unit tests for the get_single_doi function"""


@pytest.fixture
def test_doi():
    return URIRefDoi("10.1234/example.doi")


@pytest.fixture
def expected_access_url_crossrefworks(test_doi):
    return f"{CROSSREF_WORKS_URL}/{test_doi}"


@pytest.fixture
def test_message():
    return {
        "title": ["Test Paper"],
        "author": [{"given": "John", "family": "Doe"}],
        "published": {"date-parts": []},
    }


def test_get_single_doi_success(mocker, test_doi, expected_access_url_crossrefworks, test_message):
    """Test successful retrieval of DOI metadata"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = {"message": test_message}

    # Call the function
    result = get_single_doi(test_doi)

    # Verify the result
    assert result == test_message

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url_crossrefworks)


def test_get_single_doi_api_error(mocker, test_doi, expected_access_url_crossrefworks):
    """Test when API returns None"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = None

    # Call the function
    result = get_single_doi(test_doi)

    # Verify the result
    assert result == {}

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url_crossrefworks)


"""Unit tests for the get_datacitations function"""


@pytest.fixture
def test_pid(test_doi):
    return URIRef(f"https://doi.org/{test_doi}")


@pytest.fixture
def expected_access_url_datacitations(test_doi):
    return f"{CROSSREF_DATACITATIONS_URL}?object-id={test_doi}"


@pytest.fixture
def test_data():
    return {
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


def test_get_datacitations_success(mocker, test_data, test_doi, test_pid, expected_access_url_datacitations):
    """Test successful processing of datacitations"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.return_value = test_doi
    mock_urirefdoi = mocker.patch("data_citation_reporter.crossref.URIRefDoi")
    mock_relations = mocker.patch("data_citation_reporter.crossref.CROSSREF_RELATIONS")

    # Mock URIRefDoi calls
    mock_subject1 = URIRef("https://doi.org/10.5678/subject.doi")
    mock_object1 = URIRef("https://doi.org/10.9999/object.doi")
    mock_subject2 = URIRef("https://doi.org/10.1111/subject2.doi")
    mock_object2 = URIRef("https://doi.org/10.2222/object2.doi")
    mock_urirefdoi.side_effect = [
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
    result = get_datacitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 12  # 6 provenance statements × 2 relations

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url_datacitations)

    # Verify triple structure
    # Check DCTERMS relations
    assert (mock_subject1, mock_is_cited_by, mock_object1) in result
    assert (mock_subject2, mock_references, mock_object2) in result

    # Check provenance triples
    statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
    assert len(statement_nodes) == 2  # 1 provenance statements × 2 relations


def test_get_datacitations_api_error(mocker, test_doi, test_pid, expected_access_url_datacitations):
    """Test when API returns None"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = None
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.return_value = test_doi

    # Call the function
    result = get_datacitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # Empty graph returned

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url_datacitations)


def test_get_datacitations_no_results(mocker, test_doi, test_pid):
    """Test with no results"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = {"message": {"total-results": 0, "items": []}}
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.return_value = test_doi

    mock_print = mocker.patch("builtins.print")
    # Call the function
    result = get_datacitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # No triples added

    # Verify print call
    mock_print.assert_any_call(f"{test_doi}: 0")


"""Unit tests for the check_crossref function"""


@pytest.fixture
def src_uri():
    return "https://doi.org/10.1234/source.doi"


@pytest.fixture
def ref_uri():
    return "https://doi.org/10.1234/reference.doi"


@pytest.fixture
def ref_title():
    return "Test Reference Title"


@pytest.fixture
def expected_access_url_crossref():
    return f"{CROSSREF_WORKS_URL}/10.1234/source.doi"


@pytest.fixture
def test_data_with_references(ref_uri):
    return {
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


@pytest.fixture
def test_data_without_references():
    return {
        "message": {
            "publisher": "test publisher",
            "container-title": "test journal name",
            "title": ["Test Paper"],
            "author": [{"given": "John", "family": "Doe"}],
        }
    }


def test_check_crossref_found_by_doi(
    mocker,
    test_data_with_references,
    src_uri,
    ref_uri,
    ref_title,
    expected_access_url_crossref,
):
    """Test reference found by exact DOI match"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_with_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is True
    assert result["status"] == 2
    assert result["message"] == "Found 10.5678/reference.doi in formatted reference"
    assert "reference" in result

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)


def test_check_crossref_found_by_doi_in_field(
    mocker,
    src_uri,
    ref_uri,
    ref_title,
    test_data_with_references,
    expected_access_url_crossref,
):
    """Test reference found by DOI in reference field"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_with_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Modify test data to have DOI in unstructured field instead of DOI field
    test_data_modified = test_data_with_references.copy()
    test_data_modified["message"]["reference"][0].pop("DOI")
    test_data_modified["message"]["reference"][0]["unstructured"] = "See 10.5678/reference.doi for more details"

    mock_get.return_value = test_data_modified

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is True
    assert result["status"] == 1
    assert "reference" in result

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)


def test_check_crossref_found_by_title(
    mocker,
    src_uri,
    ref_uri,
    ref_title,
    test_data_with_references,
    expected_access_url_crossref,
):
    """Test reference found by title match"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_with_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Modify test data to have title match
    test_data_modified = test_data_with_references.copy()
    test_data_modified["message"]["reference"][0]["DOI"] = ""
    test_data_modified["message"]["reference"][0][
        "unstructured"
    ] = "Doe, J. (2023). Test Reference Title. Journal of Tests, 10(1), 123-456"

    mock_get.return_value = test_data_modified

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is True
    assert result["status"] == 1
    assert "reference" in result

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)


def test_check_crossref_found_by_fuzzy_match(
    mocker,
    src_uri,
    ref_uri,
    ref_title,
    test_data_with_references,
    expected_access_url_crossref,
):
    """Test reference found by fuzzy title match"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_with_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Modify test data to have partial title match
    test_data_modified = test_data_with_references.copy()
    test_data_modified["message"]["reference"][0]["DOI"] = ""
    test_data_modified["message"]["reference"][0]["unstructured"] = "Test Reference"

    mock_get.return_value = test_data_modified

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is True
    assert result["status"] == 1
    assert "reference" in result
    assert "71%" in result["message"]

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)


def test_check_crossref_not_found(
    mocker,
    src_uri,
    ref_uri,
    ref_title,
    test_data_without_references,
    expected_access_url_crossref,
):
    """Test reference not found"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_without_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is False
    assert result["status"] == 0
    assert result["message"] == "Reference not found in CrossRef metadata."
    assert "reference" not in result

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)


def test_check_crossref_no_references_section(
    mocker,
    src_uri,
    ref_uri,
    ref_title,
    test_data_without_references,
    expected_access_url_crossref,
):
    """Test when response doesn't have references section"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.crossref.get")
    mock_get.return_value = test_data_without_references
    mock_shorten_doi = mocker.patch("data_citation_reporter.crossref.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]

    # Call the function
    result = check_crossref(src_uri, ref_uri, ref_title)

    # Verify the result
    assert result["found"] is False
    assert result["status"] == 0
    assert result["message"] == "Reference not found in CrossRef metadata."

    # Verify function calls
    mock_get.assert_called_once_with(expected_access_url_crossref)
