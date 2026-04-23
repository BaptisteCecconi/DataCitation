# test_rdf.py
import pytest
from rdflib import URIRef, Literal, Graph
from rdflib.namespace import RDF

from data_citation_reporter.rdf import (
    URIRefDoi,
    shorten_doi,
    URIRefBibcode,
    URIRefArXiv,
    reverse,
    Graph as CustomGraph,
)


def test_doi_https_full_url():
    """Test with complete HTTPS DOI URL"""
    result = URIRefDoi("https://doi.org/10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_uriref_doi():
    """Test with complete HTTPS DOI URL"""
    expected = URIRef("https://doi.org/10.1234/example.doi")
    result = URIRefDoi(expected)
    assert result == expected


def test_uriref_doi_lowercase():
    """Test with complete HTTPS DOI URL"""
    expected = URIRef("https://doi.org/10.1234/example.doi")
    result = URIRefDoi(URIRef("https://doi.org/10.1234/Example.DOI"))
    assert result == expected


def test_doi_http_to_https():
    """Test HTTP DOI URL converted to HTTPS"""
    result = URIRefDoi("http://doi.org/10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_dx_http_to_https():
    """Test dx.doi.org HTTP converted to HTTPS"""
    result = URIRefDoi("http://dx.doi.org/10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_dx_https_to_https():
    """Test dx.doi.org HTTPS converted to standard HTTPS"""
    result = URIRefDoi("https://dx.doi.org/10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_prefix_to_url():
    """Test doi: prefix converted to URL"""
    result = URIRefDoi("doi:10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_10_prefix_to_url():
    """Test 10. prefix converted to URL"""
    result = URIRefDoi("10.1234/example.doi")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_case_insensitive():
    """Test DOI handling is case insensitive"""
    result = URIRefDoi("DOI:10.1234/Example.DOI")
    expected = URIRef("https://doi.org/10.1234/example.doi")
    assert result == expected


def test_doi_invalid_syntax():
    """Test invalid DOI syntax raises ValueError"""
    with pytest.raises(ValueError, match="Invalid DOI syntax: invalid.doi"):
        URIRefDoi("invalid.doi")


def test_doi_empty_string():
    """Test empty string raises ValueError"""
    with pytest.raises(ValueError, match="Invalid DOI syntax: "):
        URIRefDoi("")


def test_shorten_doi_full_url():
    """Test shortening complete DOI URL"""
    uri = URIRef("https://doi.org/10.1234/example.doi")
    result = shorten_doi(uri)
    expected = "10.1234/example.doi"
    assert result == expected


def test_shorten_doi_already_short():
    """Test shortening already short DOI"""
    uri = URIRef("10.1234/example.doi")
    result = shorten_doi(uri)
    expected = "10.1234/example.doi"
    assert result == expected


def test_shorten_doi_case_sensitivity():
    """Test case sensitivity preservation"""
    uri = URIRef("https://doi.org/10.1234/Example.DOI")
    result = shorten_doi(uri)
    expected = "10.1234/Example.DOI"
    assert result == expected


def test_bibcode_ads_full_url():
    """Test with complete ADS URL"""
    result = URIRefBibcode("https://adsabs.harvard.edu/abs/2023ApJ...123...45A")
    expected = URIRef("https://adsabs.harvard.edu/abs/2023ApJ...123...45A")
    assert result == expected


def test_bibcode_ui_ads_to_ads():
    """Test ui.adsabs.harvard.edu URL converted to standard ADS"""
    result = URIRefBibcode(
        "https://ui.adsabs.harvard.edu/abs/2023ApJ...123...45A"
    )
    expected = URIRef("https://adsabs.harvard.edu/abs/2023ApJ...123...45A")
    assert result == expected


def test_bibcode_bare_bibcode():
    """Test bare bibcode converted to ADS URL"""
    result = URIRefBibcode("2023ApJ...123...45A")
    expected = URIRef("https://adsabs.harvard.edu/abs/2023ApJ...123...45A")
    assert result == expected


def test_bibcode_case_sensitivity():
    """Test bibcode case sensitivity preservation"""
    result = URIRefBibcode("2023apj...123...45a")
    expected = URIRef("https://adsabs.harvard.edu/abs/2023apj...123...45a")
    assert result == expected


def test_arxiv_full_url():
    """Test with complete arXiv URL"""
    result = URIRefArXiv("https://arxiv.org/abs/1234.5678")
    expected = URIRef("https://arxiv.org/abs/1234.5678")
    assert result == expected


def test_arxiv_bare_id():
    """Test bare arXiv ID converted to URL"""
    result = URIRefArXiv("1234.5678")
    expected = URIRef("https://arxiv.org/abs/1234.5678")
    assert result == expected


def test_arxiv_with_version():
    """Test arXiv ID with version"""
    result = URIRefArXiv("1234.5678v2")
    expected = URIRef("https://arxiv.org/abs/1234.5678v2")
    assert result == expected


def test_arxiv_case_sensitivity():
    """Test arXiv ID case sensitivity preservation"""
    result = URIRefArXiv("1234.5678ABC")
    expected = URIRef("https://arxiv.org/abs/1234.5678ABC")
    assert result == expected


def test_reverse_existing_predicate(mocker):
    """Test reversing an existing predicate"""
    # Setup mock
    mock_reverse_property = mocker.patch(
        "data_citation_reporter.rdf.REVERSE_PROPERTY"
    )
    test_uri = URIRef("http://example.org/isCitedBy")
    reversed_uri = URIRef("http://example.org/cites")
    mock_reverse_property.__getitem__.return_value = reversed_uri

    result = reverse(test_uri)

    # Verify
    assert result == reversed_uri
    mock_reverse_property.__getitem__.assert_called_once_with(test_uri)


def test_reverse_missing_predicate(mocker):
    """Test reversing a predicate that doesn't exist in REVERSE_PROPERTY"""
    # Setup mock to raise KeyError
    mock_reverse_property = mocker.patch(
        "data_citation_reporter.rdf.REVERSE_PROPERTY"
    )
    test_uri = URIRef("http://example.org/unknownPredicate")
    mock_reverse_property.__getitem__.side_effect = KeyError(test_uri)

    with pytest.raises(KeyError):
        reverse(test_uri)

    mock_reverse_property.__getitem__.assert_called_once_with(test_uri)


def test_inheritance():
    """Test that CustomGraph inherits from rdflib.Graph"""
    graph = CustomGraph()
    assert isinstance(graph, Graph)
    assert isinstance(graph, CustomGraph)


def test_add_with_prov_none():
    """Test add_with_prov with no provenance"""
    graph = CustomGraph()
    triple = (
        URIRef("http://example.org/subject"),
        URIRef("http://example.org/predicate"),
        URIRef("http://example.org/object"),
    )

    # Should not raise any error
    graph.add_with_prov(triple)

    # Verify the triple was added
    assert triple in graph


def test_add_with_prov_with_metadata():
    """Test add_with_prov with provenance metadata"""
    graph = CustomGraph()
    triple = (
        URIRef("http://example.org/subject"),
        URIRef("http://example.org/predicate"),
        URIRef("http://example.org/object"),
    )
    prov = {URIRef("http://example.org/provenance"): Literal("test")}

    # Should not raise any error
    graph.add_with_prov(triple, prov)

    # Verify the triple was added
    assert triple in graph

    # Verify provenance statements were added
    # Look for RDF.Statement nodes
    statement_nodes = list(graph.subjects(RDF.type, RDF.Statement))
    assert len(statement_nodes) == 1

    # Verify the statement has the correct components
    statement_node = statement_nodes[0]
    assert (
        statement_node,
        RDF.subject,
        URIRef("http://example.org/subject"),
    ) in graph
    assert (
        statement_node,
        RDF.predicate,
        URIRef("http://example.org/predicate"),
    ) in graph
    assert (
        statement_node,
        RDF.object,
        URIRef("http://example.org/object"),
    ) in graph

    # Verify provenance metadata
    provenance_pred = URIRef("http://example.org/provenance")
    assert (statement_node, provenance_pred, Literal("test")) in graph


def test_add_with_prov_multiple_provenance():
    """Test add_with_prov with multiple provenance entries"""
    graph = CustomGraph()
    triple = (
        URIRef("http://example.org/subject"),
        URIRef("http://example.org/predicate"),
        URIRef("http://example.org/object"),
    )
    prov = {
        URIRef("http://example.org/source"): Literal("biblinks"),
        URIRef("http://example.org/date"): Literal("2023-01-01"),
    }

    graph.add_with_prov(triple, prov)

    # Verify the triple was added
    assert triple in graph

    # Verify both provenance entries
    statement_nodes = list(graph.subjects(RDF.type, RDF.Statement))
    assert len(statement_nodes) == 1
    statement_node = statement_nodes[0]

    source_pred = URIRef("http://example.org/source")
    date_pred = URIRef("http://example.org/date")

    assert (statement_node, source_pred, Literal("biblinks")) in graph
    assert (statement_node, date_pred, Literal("2023-01-01")) in graph


def test_add_with_prov_empty_provenance_dict():
    """Test add_with_prov with empty provenance dict"""
    graph = CustomGraph()
    triple = (
        URIRef("http://example.org/subject"),
        URIRef("http://example.org/predicate"),
        URIRef("http://example.org/object"),
    )
    prov = {}

    # Should work fine with empty dict
    graph.add_with_prov(triple, prov)

    # Verify the triple was added
    assert triple in graph


def test_add_with_prov_none_provenance():
    """Test add_with_prov with None provenance"""
    graph = CustomGraph()
    triple = (
        URIRef("http://example.org/subject"),
        URIRef("http://example.org/predicate"),
        URIRef("http://example.org/object"),
    )

    # Should work fine with None
    graph.add_with_prov(triple, None)

    # Verify the triple was added
    assert triple in graph
