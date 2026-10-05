# -*- coding: utf-8 -*-
# test_nasa_ads.py

import pytest

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, RDF

from data_citation_reporter.nasa_ads import get_nasa_ads
from data_citation_reporter.rdf import URIRefDoi


@pytest.fixture
def test_api():
    return "http://test.url/api"


@pytest.fixture
def test_doi():
    return "10.1234/example.doi"


@pytest.fixture
def test_uri(test_doi):
    return URIRefDoi(f"https://doi.org/{test_doi}")


@pytest.fixture
def expected_query(test_doi):
    return f"full:{test_doi}"


@pytest.fixture
def expected_fl():
    return "doi"


@pytest.fixture
def expected_access_url(test_api, expected_query, expected_fl):
    return f"{test_api}/search/query?q={expected_query}&fl={expected_fl}"


@pytest.fixture
def test_citing1():
    return "10.5678/first.doi"


@pytest.fixture
def test_citing2():
    return "10.9999/second.doi"


@pytest.fixture
def test_citing3():
    return "10.1111/third.doi"


@pytest.fixture
def test_response_with_results(test_citing1, test_citing2, test_citing3):
    return {
        "response": {
            "numFound": 2,
            "docs": [
                {"doi": [test_citing1, test_citing2]},
                {"doi": [test_citing3]},
            ],
        }
    }


@pytest.fixture
def test_response_no_results():
    return {"response": {"numFound": 0, "docs": []}}


"""Unit tests for the get_nasa_ads function"""


def test_get_nasa_ads_success(
    mocker, test_api, test_response_with_results, test_uri, test_citing1, test_citing2, test_citing3
):
    """Test successful processing with results"""
    # Setup mocks
    mock_load_token = mocker.patch("data_citation_reporter.nasa_ads.load_token")
    mock_load_token.return_value = "test_token"
    mock_token = "test_token"
    mock_api_url = test_api

    # Mock get response
    mock_get = mocker.patch("data_citation_reporter.nasa_ads.get")
    mock_get.return_value = test_response_with_results

    # Call the function
    result = get_nasa_ads(test_uri, api_url=mock_api_url, token=mock_token)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 12  # 6 triples per citation × 2 unique citations

    # Verify the access URL construction
    expected_url = f"{test_api}/search/query?q=full%3A10.1234%2Fexample.doi&fl=doi"
    mock_get.assert_called_once_with(
        expected_url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer test_token",
        },
        use_cache=True,
    )

    for triple in result:
        print(triple)
    # Verify triple structure using mocked objects
    src_uri = URIRef(test_uri)
    assert (
        URIRefDoi(test_citing1),
        DCTERMS.references,
        src_uri,
    ) in result
    assert (
        URIRefDoi(test_citing3),
        DCTERMS.references,
        src_uri,
    ) in result
    assert (
        URIRefDoi(test_citing2),
        DCTERMS.references,
        src_uri,
    ) not in result

    # Check provenance triples
    statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
    assert len(statement_nodes) == 2  # 2 provenance statements


def test_get_nasa_ads_no_results(mocker, test_response_no_results, test_uri, test_api):
    """Test with no results found"""
    # Setup mocks
    mock_load_token = mocker.patch("data_citation_reporter.nasa_ads.load_token")
    mock_load_token.return_value = "test_token"
    mock_get = mocker.patch("data_citation_reporter.nasa_ads.get")
    mock_get.return_value = test_response_no_results

    # Call the function
    result = get_nasa_ads(test_uri, api_url=test_api, token="test_token")

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # Empty graph returned


def test_get_nasa_ads_custom_api_url(mocker, test_response_with_results, test_uri):
    """Test with custom API URL"""
    # Setup mocks
    mock_load_token = mocker.patch("data_citation_reporter.nasa_ads.load_token")
    mock_load_token.return_value = "test_token"

    # Mock get response
    mock_get = mocker.patch("data_citation_reporter.nasa_ads.get")
    mock_get.return_value = test_response_with_results

    custom_api_url = "https://custom.api.example.org/v1"

    # Call the function with custom API URL
    result = get_nasa_ads(test_uri, api_url=custom_api_url, token="test_token")

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
        use_cache=True,
    )


def test_get_nasa_ads_empty_doi_list(mocker, test_doi, test_uri):
    """Test with empty DOI list in result"""
    # Setup mocks
    mock_load_token = mocker.patch("data_citation_reporter.nasa_ads.load_token")
    mock_load_token.return_value = "test_token"
    mock_shorten_doi = mocker.patch("data_citation_reporter.nasa_ads.shorten_doi")
    mock_shorten_doi.return_value = test_doi

    # Test data with empty DOI list
    test_data_empty_doi = {"response": {"numFound": 1, "docs": [{"doi": []}]}}
    mock_get = mocker.patch("data_citation_reporter.nasa_ads.get")
    mock_get.return_value = test_data_empty_doi

    # Call the function
    result = get_nasa_ads(test_uri)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # No triples added for empty DOI list
