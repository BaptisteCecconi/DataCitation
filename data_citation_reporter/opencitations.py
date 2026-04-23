# -*- coding: utf-8 -*-
from .static import OPENCITATIONS_URL
from .namespaces import BIBLINK
from .rdf import Graph, URIRefDoi
from .connect import get
from rdflib import Literal
from rdflib.namespace import DCTERMS, PROV


def get_opencitations(pid, api_url=OPENCITATIONS_URL):

    g = Graph()
    doi = str(pid).replace("https://doi.org/", "")

    access_url = f"{api_url}/citations/{doi}"
    data = get(access_url)
    if data is None:
        return g

    print(f"{doi}: {len(data)}")
    if len(data) > 0:
        citation_set = set((item["citing"], "doi") for item in data)
        print(
            f"citing: {', '.join([f'doi:{cite_item[0]}' for cite_item in citation_set])}"
        )

        src_pid = URIRefDoi(doi)
        for identifier, schema in citation_set:
            bib_pid = URIRefDoi(identifier)
            g.add_with_prov(
                (bib_pid, DCTERMS.references, src_pid),
                prov={PROV.wasInformedBy: Literal("OpenCitations")},
            )
            g.add((bib_pid, BIBLINK.scheme, Literal(schema)))

    return g
