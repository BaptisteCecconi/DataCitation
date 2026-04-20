from .rdf import shorten_doi
from .static import DATACITE_DOIS_URL
from .connect import get
from typing import List, Dict


def get_single_doi(doi, api_url=DATACITE_DOIS_URL) -> Dict:
    """Get DOI metadata.

    :param doi: DOI (in the form 10.xxxx/yyyy)
    :param api_url: API URL
    """
    access_url = f"{api_url}/{doi}"
    data = get(access_url)
    if data is None:
        return {}
    else:
        return data["data"]


def get_dois_from_prefix(doi_prefix: str, api_url=DATACITE_DOIS_URL) -> List:
    """Download all DOIs registered for the provided DOI prefix.

    :param doi_prefix: DOI prefix to look for
    :param api_url: API URL
    """

    page_size = 50
    access_url = f"{api_url}?prefix={doi_prefix}&page%5Bsize%5D={page_size}"
    dois = []

    while True:
        # While there is a next page, repeat the query and load DOIs
        data = get(access_url)
        dois.extend(data["data"])

        if "next" in data["links"].keys():
            access_url = data["links"]["next"]
        else:
            break

    return dois


def check_datacite(src_uri, ref_uri):
    src_doi = shorten_doi(src_uri)
    ref_doi = shorten_doi(ref_uri)

    result = {
        "found": False,
        "message": "Reference not found in DataCite metadata.",
        "status": 0,
    }

    response = get_single_doi(src_doi)
    for related_identifier in response["attributes"]["relatedIdentifiers"]:
        if ref_doi == related_identifier["relatedIdentifier"].lower():
            result["found"] = True
            result["reference"] = related_identifier
            result["status"] = 2
            result["message"] = "Reference found in DataCite metadata."
            break
    return result
