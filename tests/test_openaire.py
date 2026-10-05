# -*- coding: utf-8 -*-
"""Test module for scholexplorer.py"""

from collections import namedtuple
import pytest

from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from data_citation_reporter.openaire import (
    get_openaire_graph,
    get_openaire_graph_v3,
    get_scholexplorer,
    get_scholexplorer_v3,
)
from data_citation_reporter.namespaces import CITO
from data_citation_reporter.rdf import URIRefDoi


@pytest.fixture(name="test_doi")
def fixture_doi():
    """test_doi"""
    return "10.1234/example.doi"


@pytest.fixture(name="test_pid")
def fixture_pid(test_doi):
    """test_pid"""
    return URIRefDoi(f"https://doi.org/{test_doi}")


@pytest.fixture(name="expected_access_url")
def fixture_expected_access_url(test_doi):
    """expected_access_url"""
    return f"https://api.openaire.eu/graph/v1/researchProducts/links?targetPid={test_doi}&page=0&pageSize=100"


@pytest.fixture(name="test_data")
def fixture_data():
    """test_data"""
    return {
        "header": {
            "debug": {},
            "numFound": 2,
            "maxScore": 1.1,
            "queryTime": 20,
            "page": 0,
            "pageSize": 100,
            "totalPages": 1,
            "totalLinks": 2,
            "totalCitationsCount": 2,
            "countsByType": {},
            "nextCursor": "",
        },
        "results": [
            {
                "source": {
                    "identifiers": [
                        {
                            "id": "10.5678/another.doi",
                            "idScheme": "doi",
                            "idUrl": "https://doi.org/10.5678/another.doi",
                        },
                        {
                            "id": "identifier",
                            "idScheme": "other",
                            "idUrl": "other://identifier",
                        },
                    ]
                },
                "target": {
                    "identifiers": [
                        {
                            "id": "10.1234/example.doi",
                            "idScheme": "doi",
                            "idUrl": "https://doi.org/10.1234/example.doi",
                        }
                    ]
                },
                "relType": {"name": "Cites", "typeSchema": "datacite", "type": "cites"},
                #                    "provenance": ["DataCite", "CrossRef"],
            },
            {
                "source": {
                    "identifiers": [
                        {
                            "id": "identifier",
                            "idScheme": "other",
                            "idUrl": "other://identifier",
                        },
                        {
                            "id": "10.9999/test.doi",
                            "idScheme": "doi",
                            "idUrl": "https://doi.org/10.9999/test.doi",
                        },
                    ]
                },
                "target": {
                    "identifiers": [
                        {
                            "id": "10.1234/example.doi",
                            "idScheme": "doi",
                            "idUrl": "https://doi.org/10.1234/example.doi",
                        }
                    ]
                },
                "relType": {"name": "References", "typeSchema": "datacite", "type": "references"},
                #                    "provenance": ["ORCID"],
            },
        ],
        "facets": {},
    }


@pytest.fixture(name="test_data_no_doi")
def fixture_data_no_doi():
    """test_data_no_doi"""
    return {
        "header": {
            "debug": {},
            "numFound": 2,
            "maxScore": 1.1,
            "queryTime": 20,
            "page": 0,
            "pageSize": 100,
            "totalPages": 1,
            "totalLinks": 2,
            "totalCitationsCount": 2,
            "countsByType": {},
            "nextCursor": "",
        },
        "results": [
            {
                "source": {
                    "identifiers": [
                        {"id": "identifier", "idScheme": "openaireIdentifier", "idUrl": "other://identifier"}
                    ]
                },
                "target": {
                    "identifiers": [
                        {
                            "id": "10.1234/example.doi",
                            "idScheme": "doi",
                            "idUrl": "https://doi.org/10.1234/example.doi",
                        }
                    ]
                },
                "relType": {"type": "cites", "typeSchema": "datacite", "name": "Cites"},
                #                    "provenance": ["DataCite"],
            }
        ],
        "facets": {},
    }


@pytest.fixture(name="test_empty_data")
def fixture_empty_data():
    """test_empty_data"""
    return {
        "header": {
            "debug": {},
            "numFound": 0,
            "maxScore": 0,
            "queryTime": 20,
            "page": 0,
            "pageSize": 100,
            "totalPages": 1,
            "totalLinks": 0,
            "totalCitationsCount": 0,
            "countsByType": {},
            "nextCursor": "",
        },
        "results": [],
        "facets": {},
    }


@pytest.fixture(name="custom_api_url")
def fixture_custom_api_url():
    """custom_api_url"""
    return "https://custom.api.example.org/graph/v1/researchProducts/links"


# ==============================================
# Unit tests for the get_openaire_graph function
# ==============================================


def test_get_openaire_graph_success(mocker, test_data, test_pid):
    """Test successful processing with multiple relations"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = test_data

    # Mock OPENAIRE_SCHEMAS
    mock_is_cited_by = CITO.cites
    mock_references = CITO.citesForInformation

    # Mock URIRefDoi calls
    pid1 = URIRef("https://doi.org/10.5678/another.doi")
    pid2 = URIRef("https://doi.org/10.9999/test.doi")

    result = get_openaire_graph(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 12  # 6 triples per result × 2 results

    for item in result:
        print(item)

    # Verify triple structure
    assert (pid1, mock_is_cited_by, test_pid) in result
    assert (pid2, mock_references, test_pid) in result

    # Check provenance triples
    statement_nodes = list(result.subjects(RDF.type, RDF.Statement))
    assert len(statement_nodes) == 2  # 2 provenance statements


def test_get_openaire_graph_no_doi_source(mocker, test_data_no_doi, test_pid):
    """Test when no DOI is found in source identifiers"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = test_data_no_doi

    # Call the function
    result = get_openaire_graph(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 6  # No triples added for non-DOI sources


def test_get_openaire_graph_empty_data(mocker, test_empty_data, test_pid):
    """Test with empty results"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = test_empty_data

    # Call the function
    result = get_openaire_graph(test_pid)

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 0  # No triples added


def test_get_openaire_graph_custom_api_url(mocker, custom_api_url, test_data, test_pid):
    """Test with custom API URL"""
    # Setup mocks
    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = test_data

    # Call the function with custom API URL
    result = get_openaire_graph_v3(test_pid, api_url=custom_api_url)

    # Verify the result
    assert isinstance(result, Graph)
    for item in result:
        print(item)
    assert len(result) == 12  # 6 x 2 triples


def test_get_openaire_graph_dispatch_v1():
    """Test get_openaire_graph with api_version=1"""

    with pytest.raises(NotImplementedError):
        get_openaire_graph("10.1010/abcd", api_version=1)


def test_get_openaire_graph_dispatch_v2():
    """Test get_openaire_graph with api_version=2"""

    with pytest.raises(NotImplementedError):
        get_openaire_graph("10.1010/abcd", api_version=2)


def test_get_openaire_graph_dispatch_v3(mocker):
    """Test get_openaire_graph with api_version=3"""

    mock_get = mocker.patch("data_citation_reporter.openaire.get_openaire_graph_v3")
    mock_get.return_value = "test"

    result = get_openaire_graph(URIRef("https://doi.org/10.1010/abcd"), api_version=3)

    assert result == "test"
    mock_get.assert_called_once_with("10.1010/abcd", use_cache=True)


def test_get_openaire_graph_dispatch_v4():
    """Test get_openaire_graph with api_version=4"""

    with pytest.raises(NotImplementedError):
        get_openaire_graph("10.1010/abcd", api_version=4)


def test_get_openaire_graph_dispatch_v0():
    """Test get_openaire_graph with api_version=x"""

    with pytest.raises(ValueError):
        get_openaire_graph("10.1010/abcd", api_version=0)


def test_get_openaire_graph_v3(mocker):
    """Test get_openaire_graph_v3"""

    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = None

    result = get_openaire_graph_v3(URIRef("https://doi.org/10.1010/abcd"))

    assert isinstance(result, Graph)
    assert len(result) == 0
    # test that the "targetPid" and "sourcePid" are actually both tested
    assert mock_get.call_count == 2


def test_get_scholexplorer_dispatch_v1():
    """Test get_scholexplorer with api_version=1"""

    with pytest.raises(NotImplementedError):
        get_scholexplorer("10.1010/abcd", api_version=1)


def test_get_scholexplorer_dispatch_v2():
    """Test get_scholexplorer with api_version=2"""

    with pytest.raises(NotImplementedError):
        get_scholexplorer("10.1010/abcd", api_version=2)


def test_get_scholexplorer_dispatch_v3(mocker):
    """Test get_scholexplorer with api_version=3"""

    mock_get = mocker.patch("data_citation_reporter.openaire.get_scholexplorer_v3")
    mock_get.return_value = "test"

    result = get_scholexplorer(URIRef("https://doi.org/10.1010/abcd"), api_version=3)

    assert result == "test"
    mock_get.assert_called_once_with("10.1010/abcd", use_cache=True)


def test_get_scholexplorer_dispatch_v0():
    """Test get_scholexplorer with api_version=0"""

    with pytest.raises(ValueError):
        get_scholexplorer("10.1010/abcd", api_version=0)


def test_get_scholexplorer_v3_empty(mocker):
    """Test get_scholexplorer_v3"""

    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = None

    result = get_scholexplorer_v3(URIRef("https://doi.org/10.1010/abcd"))

    assert isinstance(result, Graph)
    assert len(result) == 0
    # test that the "targetPid" and "sourcePid" are actually both tested
    assert mock_get.call_count == 2


def test_get_scholexplorer_v3(mocker):
    """Test get_scholexplorer_v3"""

    mock_get = mocker.patch("data_citation_reporter.openaire.get")
    mock_get.return_value = 1

    mock_scholexplorer_result_v3 = mocker.patch("data_citation_reporter.openaire.ScholexplorerResultV3")
    Relation = namedtuple("Relation", ["source", "relation", "target"])
    rel = Relation(
        source=URIRef("https://doi.org/10.1010/abcd"),
        relation=URIRef("ns:cites"),
        target=URIRef("https://doi.org/10.2020/defg"),
    )
    mock_scholexplorer_result_v3.return_value.relations = [rel]

    result = get_scholexplorer_v3(URIRef("https://doi.org/10.1010/abcd"))

    assert isinstance(result, Graph)
    assert len(result) == 6
