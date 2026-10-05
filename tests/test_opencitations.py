# -*- coding: utf-8 -*-
# test_opencitations.py

import pytest

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCTERMS, PROV, RDF

from data_citation_reporter.opencitations import get_opencitations
from data_citation_reporter.static import OPENCITATIONS_V1_URL
from data_citation_reporter.namespaces import BIBLINK


@pytest.fixture
def test_doi():
    return "10.1234/example.doi"


@pytest.fixture
def test_pid(test_doi):
    return f"https://doi.org/{test_doi}"


@pytest.fixture
def expected_access_url(test_doi):
    return f"{OPENCITATIONS_V1_URL}/citations/{test_doi}"


@pytest.fixture
def test_data():
    return [
        {"citing": "10.5678/another.doi"},
        {"citing": "10.9999/test.doi"},
    ]


@pytest.fixture
def expected_citation_set():
    return {
        ("10.5678/another.doi", "doi"),
        ("10.9999/test.doi", "doi"),
    }


@pytest.fixture
def custom_api_url():
    return "https://custom.api.example.org/"


"""Unit tests for the get_opencitations function"""


def test_get_opencitations_success(mocker, test_data, test_pid, expected_access_url, test_doi, expected_citation_set):
    """Test successful processing with citation data"""
    # Mock the get function
    mock_get = mocker.patch("data_citation_reporter.opencitations.get")
    mock_get.return_value = test_data

    # Call the function
    result = get_opencitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 14  # 7 triples per citation × 3 unique citations

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)

    # Verify triple structure
    src_uri = URIRef(f"https://doi.org/{test_doi}".lower())
    citing_uris = [URIRef(f"https://doi.org/{cite[0]}".lower()) for cite in expected_citation_set]

    # Check DCTERMS.references triples
    for citing_uri in citing_uris:
        assert (citing_uri, DCTERMS.references, src_uri) in result

    # Check BIBLINK.scheme triples with actual schema values
    for citing_uri, schema in expected_citation_set:
        expected_uri = URIRef(f"https://doi.org/{citing_uri}".lower())
        assert (expected_uri, BIBLINK.scheme, Literal(schema)) in result


def test_get_opencitations_success_empty_data(mocker, test_pid, expected_access_url):
    """Test with empty citation data"""
    # Mock the get function with empty data
    mock_get = mocker.patch("data_citation_reporter.opencitations.get")
    mock_get.return_value = []

    # Call the function
    result = get_opencitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # No triples added

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)


def test_get_opencitations_api_error(mocker, test_pid, expected_access_url):
    """Test when API returns None (connection error)"""
    # Mock the get function to return None
    mock_get = mocker.patch("data_citation_reporter.opencitations.get")
    mock_get.return_value = None

    # Call the function
    result = get_opencitations(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # Empty graph returned

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)


def test_get_opencitations_custom_api_url(mocker, custom_api_url, test_doi, test_data, test_pid):
    """Test with custom API URL"""
    expected_custom_url = f"{custom_api_url}/citations/{test_doi}"

    # Mock the get function
    mock_get = mocker.patch("data_citation_reporter.opencitations.get")
    mock_get.return_value = test_data

    # Call the function with custom API URL
    result = get_opencitations(test_pid, api_url=custom_api_url)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 14

    # Verify the custom URL was used
    mock_get.assert_called_once_with(expected_custom_url, use_cache=True)


def test_get_opencitations_provenance(mocker, test_data, test_pid):
    """Test that provenance metadata is added correctly"""
    # Mock the get function
    mock_get = mocker.patch("data_citation_reporter.opencitations.get")
    mock_get.return_value = test_data

    # Call the function
    result = get_opencitations(test_pid)

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
