# -*- coding: utf-8 -*-
"""Module for handling NASA ADS/SciX interfaces."""

from urllib.parse import urlencode
from pathlib import Path

import yaml
from rdflib import Literal, URIRef
from rdflib.namespace import DCTERMS, PROV

from .rdf import shorten_doi, Graph, URIRefDoi
from .connect import get

token_file = Path(__file__).parent.parent / "tokens.yaml"
with open(token_file, encoding="utf-8") as f:
    token_data = yaml.load(f, Loader=yaml.FullLoader)

TOKEN = token_data["ads"]

API_URL = "https://api.adsabs.harvard.edu/v1"


def get_nasa_ads(
    uri: URIRef,
    #    method: str = "full",
    api_url: str = API_URL,
    token: str = TOKEN,
    use_cache: bool = True,
) -> Graph:
    """Get citations from NASA ADS

    :param uri: URI of searched citation
    :param method: Default is "full" (not yet implemented)
    :param api_url: API URL of NASA ADS
    :param token: user token
    :param use_cache: Use cached data
    :return: Graph of citations
    """
    g = Graph()
    doi = shorten_doi(uri)
    query = urlencode({"q": f"full:{doi}", "fl": "doi"})

    access_url = f"{api_url}/search/query?{query}"
    data = get(
        access_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
        use_cache=use_cache,
    )["response"]

    if data["numFound"] > 0:
        for result in data["docs"]:
            if len(result["doi"]) > 0:
                print(result["doi"][0])
                g.add_with_prov(
                    (URIRefDoi(result["doi"][0]), DCTERMS.references, uri),
                    prov={PROV.wasInformedBy: Literal("NASA ADS")},
                )

    return g
