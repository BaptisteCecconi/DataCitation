# -*- coding: utf-8 -*-
from .connect import get
from .static import BIBLINKS_URL
from .rdf import URIRefBibcode, URIRefDoi, Graph
from .namespaces import VOREL, BIBLINK
from rdflib import Literal, URIRef
from rdflib.namespace import PROV


def get_biblinks(pid: URIRef, access_url: str = BIBLINKS_URL) -> Graph:

    g = Graph()

    data = get(access_url)
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
            raise ValueError("Unknown bib-format: {}".format(pid_type))

        subj = bib_pid
        pred = VOREL[relation]

        if data_doi == pid:

            g.add_with_prov(
                (subj, pred, data_doi),
                prov={PROV.wasInformedBy: Literal("biblinks")},
            )
            g.add((subj, BIBLINK.scheme, Literal(pid_type)))

    return g
