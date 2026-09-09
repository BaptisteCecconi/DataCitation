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
    "references": DCITE["references"],
    "cites": DCITE["cites"],
    "is_part_of": DCITE["isPartOf"],
}

CROSSREF_TYPES = {
    "journal-article": SDO.ScholarlyArticle,
}

OPENAIRE_SCHEMAS = {"datacite": DCITE}
