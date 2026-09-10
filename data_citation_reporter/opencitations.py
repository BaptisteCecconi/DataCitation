# -*- coding: utf-8 -*-
"""Module for handling OpenCitation interfaces."""

from rdflib import Literal
from rdflib.namespace import DCTERMS, PROV

from .static import OPENCITATIONS_URL
from .namespaces import BIBLINK
from .rdf import Graph, URIRefDoi
from .connect import get


def get_opencitations(pid, api_url=OPENCITATIONS_URL):
    """Get citation data from OpenCitations API.

    :param pid: Persistent identifier
    :param api_url: OpenCitations API URL (defaults to OPENCITATIONS_URL)
    :return: citation data as a Graph object
    """
    g = Graph()
    doi = str(pid).replace("https://doi.org/", "")

    access_url = f"{api_url}/citations/{doi}"
    data = get(access_url)
    if data is None:
        return g

    print(f"{doi}: {len(data)}")
    if len(data) > 0:
        # extract "citing" doi, except when the value in an empty string.
        # TODO: explore how to process this case anyway
        #       this means that the citing resource doesn't have a DOI, like, e.g. an arXiv record
        citation_set = set((item["citing"], "doi") for item in data if item["citing"] != "")
        print(f"citing: {', '.join([f'doi:{cite_item[0]}' for cite_item in citation_set])}")

        src_pid = URIRefDoi(doi)
        for identifier, schema in citation_set:
            bib_pid = URIRefDoi(identifier)
            g.add_with_prov(
                (bib_pid, DCTERMS.references, src_pid),
                prov={PROV.wasInformedBy: Literal("OpenCitations")},
            )
            g.add((bib_pid, BIBLINK.scheme, Literal(schema)))

    return g
