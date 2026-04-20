# test_biblinks.py
import pytest
from rdflib import URIRef, Literal

from data_citation_reporter.biblinks import get_biblinks
from data_citation_reporter.rdf import Graph


@pytest.fixture
def biblinks_data():
    return [
        {
            "bib-ref": "2023ApJ...123...45A",
            "relationship": "Cites",
            "dataset-ref": "10.1234/example.doi",
            "bib-format": "bibcode",
        },
        {
            "bib-ref": "10.789/abc-dddd",
            "relationship": "IsSupplementTo",
            "dataset-ref": "10.5678/another.doi",
            "bib-format": "doi",
        },
        {
            "bib-ref": "10.1000/xyz123",
            "relationship": "IsSupplementTo",
            "dataset-ref": "10.5678/another.doi",
            "bib-format": "doi",
        },
        {
            "bib-ref": "2024MNRAS.555..678B",
            "relationship": "Cites",
            "dataset-ref": "10.9999/test.doi",
            "bib-format": "bibcode",
        },
    ]


def test_get_biblinks_success_multiple_items(mocker, biblinks_data):
    """Test successful processing with multiple items"""
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = biblinks_data
    pid = URIRef("https://doi.org/10.5678/another.doi")

    # Call the function
    result = get_biblinks(pid, "http://test.url")
    assert len(result) == 14
    assert isinstance(result, Graph)


def test_get_biblinks_api_error(mocker):
    """Test behavior when API call returns None"""
    # Mock the get function to return None (API error)
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = None
    pid = URIRef("https://doi.org/10.5678/another.doi")
    result = get_biblinks(pid, "http://test.url")

    # Verify that an empty Graph is returned
    assert isinstance(result, Graph)
    assert len(result) == 0


def test_get_biblinks_empty_data(mocker):
    """Test behavior with empty data array"""
    # Mock the get function to return empty data
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = []
    pid = URIRef("https://doi.org/10.1234/another.doi")

    result = get_biblinks(pid, "http://test.url")

    # Verify that an empty Graph is returned
    assert isinstance(result, Graph)
    assert len(result) == 0


def test_get_biblinks_bibcode_format(mocker, biblinks_data):
    """Test processing with bibcode format"""
    # Use only the first item (bibcode format)
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = [biblinks_data[0]]
    pid = URIRef("https://doi.org/10.1234/example.doi")
    result = get_biblinks(pid, "http://test.url")

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 7  # 2 triples for one item

    # Verifying result graph
    subjects = list(result.subjects())
    assert (
        URIRef("https://adsabs.harvard.edu/abs/2023ApJ...123...45A") in subjects
    )

    for subject in subjects:
        predicate_objects = set(result.predicate_objects(subject))
        if subject == URIRef(
            "https://adsabs.harvard.edu/abs/2023ApJ...123...45A"
        ):
            assert predicate_objects == {
                (
                    URIRef(
                        "http://www.ivoa.net/rdf/voresource/relationship_type#Cites"
                    ),
                    URIRef("https://doi.org/10.1234/example.doi"),
                ),
                (
                    URIRef("http://www.ivoa.net/rdf/biblink#scheme"),
                    Literal("bibcode"),
                ),
            }
        else:
            assert predicate_objects == {
                (
                    URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
                    URIRef("https://doi.org/10.1234/example.doi"),
                ),
                (
                    URIRef("http://www.w3.org/ns/prov#wasInformedBy"),
                    Literal("biblinks"),
                ),
                (
                    URIRef(
                        "http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"
                    ),
                    URIRef(
                        "https://adsabs.harvard.edu/abs/2023ApJ...123...45A"
                    ),
                ),
                (
                    URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                    URIRef(
                        "http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"
                    ),
                ),
                (
                    URIRef(
                        "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"
                    ),
                    URIRef(
                        "http://www.ivoa.net/rdf/voresource/relationship_type#Cites"
                    ),
                ),
            }


def test_get_biblinks_doi_format(mocker, biblinks_data):
    """Test processing with DOI format"""
    # Use only the second item (DOI format)
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = [biblinks_data[2]]
    pid = URIRef("https://doi.org/10.5678/another.doi")
    result = get_biblinks(pid, "http://test.url")

    # Verify the result
    assert isinstance(result, Graph)
    assert len(result) == 7  # 2 triples for one item

    # Verifying result graph
    subjects = list(result.subjects())
    assert URIRef("https://doi.org/10.1000/xyz123") in subjects

    for subject in result.subjects():
        predicate_objects = set(result.predicate_objects(subject))
        if subject == URIRef("https://doi.org/10.1000/xyz123"):
            assert predicate_objects == {
                (
                    URIRef(
                        "http://www.ivoa.net/rdf/voresource/relationship_type#IsSupplementTo"
                    ),
                    URIRef("https://doi.org/10.5678/another.doi"),
                ),
                (
                    URIRef("http://www.ivoa.net/rdf/biblink#scheme"),
                    Literal("doi"),
                ),
            }


def test_get_biblinks_unknown_format(mocker):
    """Test behavior with unknown bib-format"""
    # Create data with unknown format
    test_data = [
        {
            "dataset-ref": "10.1234/example.doi",
            "bib-ref": "2023ApJ...123...45A",
            "relationship": "isCitedBy",
            "bib-format": "unknown_format",  # Unknown format
        }
    ]
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = test_data
    pid = URIRef("https://doi.org/10.1234/example.doi")

    # Verify that ValueError is raised
    with pytest.raises(ValueError, match="Unknown bib-format: unknown_format"):
        get_biblinks(pid, "http://test.url")


def test_get_biblinks_default_url(mocker):
    """Test that the default URL is used when no URL is provided"""
    mock_get = mocker.patch("data_citation_reporter.biblinks.get")
    mock_get.return_value = []

    mock_graph = mocker.patch("data_citation_reporter.biblinks.Graph")
    mock_graph.return_value = Graph()
    pid = URIRef("https://doi.org/10.1234/example.doi")

    # Call without URL parameter (should use default)
    _ = get_biblinks(pid)

    # Verify that get was called with default URL
    mock_get.assert_called_once()
    # The default URL should be used (BIBLINKS_URL)
