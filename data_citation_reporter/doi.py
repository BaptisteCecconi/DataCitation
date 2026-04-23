from typing import Union
from .static import DOI_RA_URL
from .rdf import shorten_doi, URIRefDoi
from .connect import get
from rdflib import URIRef


def get_registration_agency(
    uri: Union[str, URIRef], api_url: str = DOI_RA_URL
) -> str:
    """Retrieve the registration agency from DOI.

    :param uri: URI of the DOI (URIRef object or str).
    :param api_url: URL of the Registration Agency resolver.
    :return: string of the registration agency ("Datacite", "CrossRef"...)
    """

    doi = shorten_doi(URIRefDoi(uri))
    access_url = f"{api_url}{doi}"
    data = get(access_url)
    if data is None:
        raise RuntimeError(f"Could not get data from {access_url}")
    else:
        data = data[0]
        if "RA" not in data.keys():
            raise ValueError(f"{data['status']}: {str(uri)}")
        else:
            return data["RA"]
