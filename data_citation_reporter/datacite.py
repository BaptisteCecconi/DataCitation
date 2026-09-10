# -*- coding: utf-8 -*-
"""Module for handling DataCite interfaces."""

from typing import List, Dict

from rdflib import URIRef, Literal, BNode
from rdflib.namespace import PROV, DCTERMS, RDF, SDO, FOAF

from .rdf import shorten_doi
from .static import DATACITE_DOIS_URL
from .connect import get
from .rdf import Graph, URIRefDoi, URIRefBibcode, URIRefArXiv
from .namespaces import BIBLINK, DCITE
from .mappings import RESOURCE_TYPE_SDO_DCMITYPE


def get_single_doi(doi, api_url=DATACITE_DOIS_URL) -> Dict:
    """Get DOI metadata.

    :param doi: DOI (in the form 10.xxxx/yyyy)
    :param api_url: API URL
    """
    access_url = f"{api_url}/{doi}"
    data = get(access_url)
    if data is None:
        return {}
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
    """Check if a URI is present a DataCite DOI metadata record.

    :param src_uri: Source DOI
    :param ref_uri: Reference URI (possibly DOI)
    :return: a dictionary with the status.
    """
    src_doi = shorten_doi(src_uri)
    ref_doi = shorten_doi(ref_uri)

    result = {
        "found": False,
        "message": "Reference not found in DataCite metadata.",
        "status": 0,
    }

    response = get_single_doi(src_doi)
    for related_identifier in response["attributes"]["relatedIdentifiers"]:
        # Some buggy records may bot have a "relatedIdentifier" , so we test first:
        if "relatedIdentifier" in related_identifier.keys():
            if ref_doi == related_identifier["relatedIdentifier"].lower():
                result["found"] = True
                result["reference"] = related_identifier
                result["status"] = 2
                result["message"] = "Reference found in DataCite metadata."
                break
        else:
            print(f"Note:\nIssue with DataCite metadata for {src_doi}")
            print(related_identifier)
    return result


def import_doi(doi: URIRef) -> Graph:
    """Import Datacite DOI metadata

    :param doi: DOI
    :return: Graph object with DOI metadata
    """
    print(f"Found DOI: {str(doi)}")
    metadata = get_single_doi(shorten_doi(doi))
    return parse_doi_metadata_to_graph(metadata)


def parse_doi_metadata_to_graph(metadata: Dict) -> Graph:
    """Parse Datacite DOI metadata into Graph object.

    :param metadata: DOI metadata
    :return: Graph object with DOI metadata
    """
    g = Graph()
    doi = URIRefDoi(metadata["attributes"]["doi"].lower())
    print(f"Found DOI: {str(doi)}")

    publisher = metadata["attributes"]["publisher"]
    # DataCite is the DOI metadata manager:
    g.add((doi, PROV.wasInformedBy, Literal("DataCite")))
    # ObsParis is the publisher:
    g.add((doi, DCTERMS.publisher, Literal(publisher)))
    # the PID is a DOI
    g.add((doi, BIBLINK.scheme, Literal("doi")))
    # the title:
    g.add(
        (
            doi,
            DCTERMS.title,
            Literal(metadata["attributes"]["titles"][0]["title"]),
        )
    )
    # the schema.org and DCMI types:
    g.add((doi, RDF.type, SDO[metadata["attributes"]["types"]["schemaOrg"]]))
    g.add(
        (
            doi,
            RDF.type,
            RESOURCE_TYPE_SDO_DCMITYPE[metadata["attributes"]["types"]["schemaOrg"]],
        )
    )

    # Creators:
    for creator in metadata["attributes"]["creators"]:
        if len(creator["nameIdentifiers"]) > 0:
            # if there is a NameIdentifier (ORCID)
            creator_id = creator["nameIdentifiers"][0]["nameIdentifier"]
            g.add((URIRef(creator_id), RDF.type, FOAF.Person))
            g.add((URIRef(creator_id), FOAF.name, Literal(creator["name"])))
            g.add((URIRef(creator_id), BIBLINK.scheme, Literal("orcid")))
            g.add((doi, DCTERMS.creator, URIRef(creator_id)))
        else:
            tmp = BNode()
            g.add((tmp, RDF.type, FOAF.Person))
            g.add((tmp, FOAF.name, Literal(creator["name"])))
            g.add((doi, DCTERMS.creator, tmp))

    # Related Identifiers
    for reference in metadata["attributes"]["relatedIdentifiers"]:
        try:
            related_id = reference["relatedIdentifier"].lower()
        except KeyError:
            print(reference)
            continue
        related_id_type = reference["relatedIdentifierType"].lower()
        if related_id_type in ["doi", "igsn"]:
            related_uri = URIRefDoi(related_id)
        elif related_id_type == "bibcode":
            related_uri = URIRefBibcode(related_id)
        elif related_id_type == "arxiv":
            related_uri = URIRefArXiv(related_id)
        else:
            related_uri = URIRef(related_id)
        # print(doi, related_uri)
        g.add_with_prov(
            (doi, DCITE[reference["relationType"]], related_uri),
            prov={PROV.wasInformedBy: Literal("ObsParis")},
        )

    # Citations
    for citation in metadata["relationships"]["citations"]["data"]:
        if citation["type"] == "dois":
            related_doi = URIRefDoi(citation["id"])
        else:
            print(f"{citation['type']} citation type is not supported")
            continue
        g.add_with_prov(
            (related_doi, DCITE.cites, doi),
            prov={PROV.wasInformedBy: Literal("DataCite Commons")},
        )
    for part in metadata["relationships"]["parts"]["data"]:
        if part["type"] == "dois":
            related_doi = URIRefDoi(part["id"])
        else:
            print(f"{part['type']} citation type is not supported")
            continue
        g.add_with_prov(
            (related_doi, DCITE.hasPart, doi),
            prov={PROV.wasInformedBy: Literal("DataCite Commons")},
        )
    for part in metadata["relationships"]["partOf"]["data"]:
        if part["type"] == "dois":
            related_doi = URIRefDoi(part["id"])
        else:
            print(f"{part['type']} citation type is not supported")
            continue
        g.add_with_prov(
            (related_doi, DCITE.isPartOf, doi),
            prov={PROV.wasInformedBy: Literal("DataCite Commons")},
        )

    return g
