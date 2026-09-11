# -*- coding: utf-8 -*-
"""Utility module for storing mappings."""

from rdflib.namespace import DCMITYPE, SDO
from .namespaces import DCITE

# mapping from Schema.org to DCMIType:
RESOURCE_TYPE_SDO_DCMITYPE = {
    "Article": DCMITYPE.Text,
    "Book": DCMITYPE.Collection,
    "Collection": DCMITYPE.Collection,
    "CreativeWork": DCMITYPE.InteractiveResource,
    "Dataset": DCMITYPE.Dataset,
    "Report": DCMITYPE.Text,
    "ScholarlyArticle": DCMITYPE.Text,
    "Service": DCMITYPE.Service,
    "SoftwareSourceCode": DCMITYPE.Software,
}

CROSSREF_RELATIONS = {
    "references": DCITE["References"],
    "cites": DCITE["Cites"],
    "is_part_of": DCITE["IsPartOf"],
    "is_supplemented_by": DCITE["IsSupplementedBy"],
    "is-supplemented-by": DCITE["IsSupplementedBy"],
}

CROSSREF_TYPES = {
    "journal-article": SDO.ScholarlyArticle,
}

OPENAIRE_SCHEMAS = {"datacite": DCITE}
