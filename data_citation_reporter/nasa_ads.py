# -*- coding: utf-8 -*-
from rdflib import Literal, URIRef
from .rdf import shorten_doi, Graph, URIRefDoi
from rdflib.namespace import DCTERMS, PROV
from .connect import get
from urllib.parse import urlencode
import yaml
from pathlib import Path

token_file = Path(__file__).parent.parent / "tokens.yaml"
with open(token_file) as f:
    token = yaml.load(f, Loader=yaml.FullLoader)

TOKEN = token["ads"]

api_url = "https://api.adsabs.harvard.edu/v1"


def get_nasa_ads(
    uri: URIRef,
    method: str = "full",
    api_url: str = api_url,
    token: str = TOKEN,
) -> Graph:
    """Get citations from NASA ADS

    :param uri: URI of searched citation
    :param method: Default is "full" (not yet implemented)
    :param api_url: API URL of NASA ADS
    :param token: user token
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
