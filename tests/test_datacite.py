# -*- coding: utf-8 -*-
"""Test Moule for datacite.py"""

import pytest

from data_citation_reporter.datacite import (
    get_single_doi,
    get_dois_from_prefix,
    check_datacite,
)
from data_citation_reporter.static import DATACITE_DOIS_URL

# ==========================================
# Unit tests for the get_single_doi function
# ==========================================


@pytest.fixture(name="test_doi")
def fixture_doi():
    """test_doi"""
    return "10.1234/example.doi"


@pytest.fixture(name="expected_access_url")
def fixture_expected_access_url(test_doi):
    """expected_access_url"""
    return f"{DATACITE_DOIS_URL}/{test_doi}"


@pytest.fixture(name="test_data")
def fixture_data():
    """test_data"""
    return {
        "data": {
            "id": "https://doi.org/10.1234/example.doi",
            "type": "dois",
            "attributes": {
                "titles": [{"title": "Test Paper"}],
                "creators": [{"name": "John Doe"}],
                "publisher": "Test Publisher",
            },
        }
    }


def test_get_single_doi_success(mocker, test_doi, expected_access_url, test_data):
    """Test successful retrieval of DOI metadata"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = test_data

    # Call the function
    result = get_single_doi(test_doi)

    # Verify the result
    assert result == test_data["data"]

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)


def test_get_single_doi_api_error(mocker, test_doi, expected_access_url):
    """Test when API returns None"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = None

    # Call the function
    result = get_single_doi(test_doi)

    # Verify the result
    assert result == {}

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)


def test_get_single_doi_empty_data(mocker, test_doi, expected_access_url):
    """Test when response contains empty data"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = {"data": {}}

    # Call the function
    result = get_single_doi(test_doi)

    # Verify the result
    assert result == {}

    # Verify the access URL construction
    mock_get.assert_called_once_with(expected_access_url, use_cache=True)


# ================================================
# Unit tests for the get_dois_from_prefix function
# ================================================


@pytest.fixture(name="test_prefix")
def fixture_prefix():
    """test_prefix"""
    return "10.1234"


@pytest.fixture(name="initial_access_url")
def fixture_initial_access_url(test_prefix):
    """initial_access_url"""
    return f"{DATACITE_DOIS_URL}?prefix={test_prefix}&page%5Bsize%5D=50"


@pytest.fixture(name="single_page_data")
def fixture_single_page_data():
    """single_page_data"""
    return {
        "data": [
            {"id": "10.1234/first.doi", "type": "dois"},
            {"id": "10.1234/second.doi", "type": "dois"},
        ],
        "links": {},  # No next link
    }


@pytest.fixture(name="first_page_data")
def fixture_first_page_data():
    """first_page_data"""
    return {
        "data": [
            {"id": "10.1234/first.doi", "type": "dois"},
            {"id": "10.1234/second.doi", "type": "dois"},
        ],
        "links": {"next": "https://api.datacite.org/dois?prefix=10.1234&page%5Bsize%5D=50&page=2"},
    }


@pytest.fixture(name="second_page_data")
def fixture_second_page_data():
    """second_page_data"""
    return {
        "data": [
            {"id": "10.1234/third.doi", "type": "dois"},
            {"id": "10.1234/fourth.doi", "type": "dois"},
        ],
        "links": {},  # No next link, indicating final page
    }


def test_get_dois_from_prefix_single_page(
    mocker,
    single_page_data,
    test_prefix,
    initial_access_url,
):
    """Test with single page of results"""
    # Setup mock for single page
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = single_page_data

    # Call the function
    result = get_dois_from_prefix(test_prefix)

    # Verify the result
    assert len(result) == 2
    assert result[0]["id"] == "10.1234/first.doi"
    assert result[1]["id"] == "10.1234/second.doi"

    # Verify the access URL construction
    mock_get.assert_called_once_with(initial_access_url)


def test_get_dois_from_prefix_multiple_pages(mocker, first_page_data, second_page_data, test_prefix):
    """Test with multiple pages of results"""
    # Setup mock to return different data for each call
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.side_effect = [first_page_data, second_page_data]

    # Call the function
    result = get_dois_from_prefix(test_prefix)

    # Verify the result
    assert len(result) == 4
    dois = [item["id"] for item in result]
    assert "10.1234/first.doi" in dois
    assert "10.1234/second.doi" in dois
    assert "10.1234/third.doi" in dois
    assert "10.1234/fourth.doi" in dois


def test_get_dois_from_prefix_empty_data(mocker, test_prefix, initial_access_url):
    """Test with empty data array"""
    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = {"data": [], "links": {}}

    # Call the function
    result = get_dois_from_prefix(test_prefix)

    # Verify the result
    assert not result

    # Verify the access URL construction
    mock_get.assert_called_once_with(initial_access_url)


def test_get_dois_from_prefix_custom_page_size(mocker, test_prefix):
    """Test with custom page size"""
    custom_page_size = 100

    # Setup mock
    mock_get = mocker.patch("data_citation_reporter.datacite.get")
    mock_get.return_value = {
        "data": [{"id": "10.1234/test.doi", "type": "dois"}],
        "links": {},
    }

    # Call the function with custom page size
    result = get_dois_from_prefix(
        test_prefix,
        api_url=f"{DATACITE_DOIS_URL}?prefix={test_prefix}&page%5Bsize%5D={custom_page_size}",
    )

    # Verify the result
    assert len(result) == 1
    assert result[0]["id"] == "10.1234/test.doi"


# ==========================================
# Unit tests for the check_datacite function
# ==========================================


@pytest.fixture(name="src_uri")
def fixture_src_uri():
    """src_uri"""
    return "https://doi.org/10.1234/source.doi"


@pytest.fixture(name="ref_uri")
def fixture_ref_uri():
    """ref_uri"""
    return "https://doi.org/10.5678/reference.doi"


@pytest.fixture(name="test_response_with_reference")
def fixture_response_with_reference():
    """test_response_with_reference"""
    return {
        "attributes": {
            "publisher": "test publisher",
            "relatedIdentifiers": [
                {
                    "relatedIdentifier": "10.5678/reference.doi",
                    "relatedIdentifierType": "DOI",
                    "relationType": "IsCitedBy",
                },
                {
                    "relatedIdentifier": "10.9999/other.doi",
                    "relatedIdentifierType": "DOI",
                    "relationType": "IsCitedBy",
                },
            ],
        }
    }


@pytest.fixture(name="test_response_without_reference")
def fixture_response_without_reference():
    """test_response_without_reference"""
    return {
        "attributes": {
            "publisher": "test publisher",
            "relatedIdentifiers": [
                {
                    "relatedIdentifier": "10.9999/other.doi",
                    "relatedIdentifierType": "DOI",
                    "relationType": "IsCitedBy",
                }
            ],
        }
    }


@pytest.fixture(name="test_response_no_related")
def fixture_response_no_related():
    """test_response_no_related"""
    return {"attributes": {"publisher": "test publisher", "relatedIdentifiers": []}}


def test_check_datacite_found(mocker, src_uri, ref_uri, test_response_with_reference):
    """Test reference found in DataCite metadata"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.datacite.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]
    mock_get_single_doi = mocker.patch("data_citation_reporter.datacite.get_single_doi")
    mock_get_single_doi.return_value = test_response_with_reference

    # Call the function
    result = check_datacite(src_uri, ref_uri)

    # Verify the result
    assert result["found"] is True
    assert result["status"] == 2
    assert result["message"] == "Reference found in DataCite metadata."
    assert "reference" in result
    assert result["reference"]["relatedIdentifier"] == "10.5678/reference.doi"


def test_check_datacite_not_found(mocker, test_response_without_reference, src_uri, ref_uri):
    """Test reference not found in DataCite metadata"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.datacite.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]
    mock_get_single_doi = mocker.patch("data_citation_reporter.datacite.get_single_doi")
    mock_get_single_doi.return_value = test_response_without_reference

    # Call the function
    result = check_datacite(src_uri, ref_uri)

    # Verify the result
    assert result["found"] is False
    assert result["status"] == 0
    assert result["message"] == "Reference not found in DataCite metadata."
    assert "reference" not in result


def test_check_datacite_no_related_identifiers(mocker, test_response_no_related, src_uri, ref_uri):
    """Test when DOI has no related identifiers"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.datacite.shorten_doi")
    mock_shorten_doi.side_effect = [
        "10.1234/source.doi",
        "10.5678/reference.doi",
    ]
    mock_get_single_doi = mocker.patch("data_citation_reporter.datacite.get_single_doi")
    mock_get_single_doi.return_value = test_response_no_related

    # Call the function
    result = check_datacite(src_uri, ref_uri)

    # Verify the result
    assert result["found"] is False
    assert result["status"] == 0
    assert result["message"] == "Reference not found in DataCite metadata."
    assert "reference" not in result
