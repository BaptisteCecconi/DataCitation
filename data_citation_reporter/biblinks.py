# -*- coding: utf-8 -*-
"""Module for handling IVOA Biblinks."""

from rdflib import Literal, URIRef
from rdflib.namespace import PROV

from .connect import get
from .static import BIBLINKS_URL
from .rdf import URIRefBibcode, URIRefDoi, Graph
from .namespaces import VOREL, BIBLINK


def get_biblinks(pid: URIRef, access_url: str = BIBLINKS_URL, use_cache: bool = True) -> Graph:
    """Return a graph from IVOA biblinks endpoint.

    Args:
        pid: persistent identifier
        access_url: biblink endpoint URL
        use_cache: whether to use cached data
    Returns:
        Graph
    """
    g = Graph()

    data = get(access_url, use_cache=use_cache)
    if data is None:
        return g

    for item in data:
        data_doi = URIRefDoi(item["dataset-ref"])
        bib_ref = item["bib-ref"]
        relation = item["relationship"]
        pid_type = item.get("bib-format", "bibcode")

        if pid_type == "bibcode":
            bib_pid = URIRefBibcode(bib_ref)
        elif pid_type == "doi":
            bib_pid = URIRefDoi(bib_ref)
        else:
            raise ValueError(f"Unknown bib-format: {pid_type}")

        subj = bib_pid
        pred = VOREL[relation]

        if data_doi == pid:

            g.add_with_prov(
                (subj, pred, data_doi),
                prov={PROV.wasInformedBy: Literal("biblinks")},
            )
            g.add((subj, BIBLINK.scheme, Literal(pid_type)))

    return g
