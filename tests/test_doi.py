# -*- coding: utf-8 -*-
# test_registration_agency.py

import pytest

from data_citation_reporter.doi import get_registration_agency
from data_citation_reporter.static import DOI_RA_URL


@pytest.fixture
def test_uri():
    return "https://doi.org/10.1234/example.doi"


@pytest.fixture
def expected_doi():
    return "10.1234/example.doi"


@pytest.fixture
def expected_api_url(expected_doi):
    return f"{DOI_RA_URL}/{expected_doi}"


@pytest.fixture
def test_data():
    return [{"RA": "Test Registration Agency"}]


@pytest.fixture
def test_data_no_ra():
    return [{"status": "not found"}]


@pytest.fixture
def custom_api_url():
    return "https://custom.api.example.org/"


"""Unit tests for the get_registration_agency function"""


def test_get_registration_agency_success(mocker, expected_doi, test_data, test_uri):
    """Test successful retrieval of registration agency"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = test_data

    # Call the function
    result = get_registration_agency(test_uri)

    # Verify the result
    assert result == "Test Registration Agency"


def test_get_registration_agency_with_custom_api_url(
    mocker,
    expected_doi,
    test_data,
    test_uri,
    custom_api_url,
):
    """Test with custom API URL"""

    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = test_data

    # Call the function with custom API URL
    result = get_registration_agency(test_uri, api_url=custom_api_url)

    # Verify the result
    assert result == "Test Registration Agency"


def test_get_registration_agency_api_error(mocker, expected_doi, expected_api_url, test_uri):
    """Test RuntimeError when API returns None"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = None  # API error

    # Call and verify exception
    with pytest.raises(
        RuntimeError,
        match=f"Could not get data from {expected_api_url}",
    ):
        get_registration_agency(test_uri)


def test_get_registration_agency_no_ra_key(mocker, expected_doi, test_data_no_ra, test_uri):
    """Test ValueError when 'RA' key is missing from response"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = test_data_no_ra

    # Call and verify exception
    with pytest.raises(ValueError, match="not found: https://doi.org/10.1234/example.doi"):
        get_registration_agency(test_uri)


def test_get_registration_agency_empty_response_list(mocker, expected_doi, test_uri):
    """Test ValueError when response list is empty"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = []  # Empty list

    # Call and verify exception (should raise IndexError when accessing )
    with pytest.raises(IndexError):
        get_registration_agency(test_uri)


def test_get_registration_agency_multiple_items(mocker, expected_doi, test_uri):
    """Test function behavior with multiple items in response (should use first)"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = [
        {"RA": "First Agency", "status": "ok"},
        {"RA": "Second Agency", "status": "ok"},
    ]

    # Call the function
    result = get_registration_agency(test_uri)

    # Verify the result (should return first item's RA)
    assert result == "First Agency"


def test_get_registration_agency_complex_status(mocker, expected_doi, test_uri):
    """Test with complex status message"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = [{"status": "DOI does not exist"}]

    # Call and verify exception
    with pytest.raises(
        ValueError,
        match="DOI does not exist: https://doi.org/10.1234/example.doi",
    ):
        get_registration_agency(test_uri)


def test_get_registration_agency_url_construction(mocker, test_data):
    """Test that the API URL is constructed correctly"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = "10.5678/another.doi"
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = test_data

    # Call the function with different DOI
    different_uri = "https://doi.org/10.5678/another.doi"
    get_registration_agency(different_uri)

    # Verify the URL construction
    expected_url = f"{DOI_RA_URL}/10.5678/another.doi"
    mock_get.assert_called_once_with(expected_url)


def test_get_registration_agency_error_messages_include_full_uri(mocker, expected_doi, test_data_no_ra, test_uri):
    """Test that error messages include the full original URI"""
    # Setup mocks
    mock_shorten_doi = mocker.patch("data_citation_reporter.doi.shorten_doi")
    mock_shorten_doi.return_value = expected_doi
    mock_get = mocker.patch("data_citation_reporter.doi.get")
    mock_get.return_value = test_data_no_ra

    # Call and verify exception with full URI
    with pytest.raises(ValueError, match="not found: https://doi.org/10.1234/example.doi"):
        get_registration_agency(test_uri)
