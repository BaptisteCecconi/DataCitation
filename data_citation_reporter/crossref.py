# -*- coding: utf-8 -*-
"""Module for handling CrossRef interfaces."""

from typing import Dict

from thefuzz import fuzz
from rdflib import URIRef, Literal, BNode
from rdflib.namespace import PROV, DCTERMS, RDF, FOAF

from .static import (
    CROSSREF_DATACITATIONS_URL,
    CROSSREF_WORKS_URL,
)
from .mappings import CROSSREF_RELATIONS, CROSSREF_TYPES
from .rdf import URIRefDoi, shorten_doi, Graph
from .namespaces import BIBLINK
from .connect import get


def get_single_doi(doi: str) -> Dict:
    """Get DOI metadata.

    :param doi: DOI (in the form 10.xxxx/yyyy)
    """
    access_url = f"{CROSSREF_WORKS_URL}/{doi}"
    data = get(access_url)
    if data is None:
        return {}
    return data["message"]


# def get_eventdata(pid, api_url=CROSSREF_EVENTDATA_URL):
#     g = Graph()
#     doi = shorten_doi(pid)
#     email = "baptiste.cecconi@obspm.fr"
#     rows = "1000"
#     access_url = f"{api_url}?mailto={email}&rows={rows}&subj-id={doi}"
#
#     data = get(access_url)
#     if data is not None:
#         ndata = len(data['message']['events'])
#         print(f"{doi}: {ndata}")
#         if ndata > 0:
#             citation_set = set()
#             for event in data['message']['events']:
#                 source_pid = event['obj_id']
#                 print(source_pid)
#                 if source_pid.startswith('https://doi.org/'):
#                     item = (source_pid.replace('https://doi.org/', ''), 'doi')
#                 else:
#                     item = (source_pid, 'pid')
#                     break
#                 citation_set.add(item)
#             print(f"citing: {', '.join([f'{cite_item[1]}:{cite_item[0]}'
#             for cite_item in citation_set])}")
#
#             src_pid = URIRef(f"https://doi.org/{doi}".lower())
#             # dirty fix:
#             if "202346913" in event['obj_id']:
#                 bib_pid = URIRef("https://doi.org/10.1051/0004-6361/202346913")
#             else:
#                 bib_pid = URIRef(event['obj_id'].lower())
#
#             g.add_with_prov(
#                 (src_pid, DCTERMS.isReferencedBy, bib_pid),
#                 prov={PROV.wasInformedBy: Literal("CrossRef EventData")}
#             )
#             g.add_with_prov(
#                 (bib_pid, DCTERMS.references, src_pid),
#                 prov={PROV.wasInformedBy: Literal("CrossRef EventData")}
#             )
#             g.add((bib_pid, BIBLINK.scheme, Literal("doi")))
#
#     return g


def get_datacitations(pid: URIRef, api_url=CROSSREF_DATACITATIONS_URL):
    """Get citation data from CrossRef DataCitations API.

    :param pid: Persistent identifier
    :param api_url: Openaire Scholexplorer API URL (defaults to CROSSREF_DATACITATIONS_URL)
    :return: citation data as a Graph object
    """
    g = Graph()
    doi = shorten_doi(pid)
    access_url = f"{api_url}?object-id={doi}"

    data = get(access_url)
    if data is not None:
        ndata = data["message"]["total-results"]
        print(f"{doi}: {ndata}")
        if ndata > 0:
            for item in data["message"]["items"]:
                subj = item["subject"]["id"]
                obj = item["object"]["id"]
                relation = item["relation"]
                print(f"{subj} {relation} {obj}")
                g.add_with_prov(
                    (
                        URIRefDoi(subj),
                        CROSSREF_RELATIONS[relation],
                        URIRefDoi(obj),
                    ),
                    prov={PROV.wasInformedBy: Literal("CrossRef DataCitations")},
                )

    return g


def check_crossref(src_uri, ref_uri, ref_title, api_url=CROSSREF_WORKS_URL):
    """Check if a URI is present a CrossRef DOI metadata record.

    :param src_uri: Source DOI
    :param ref_uri: Reference URI (possibly DOI)
    :param ref_title: Reference title
    :param api_url: Openaire Scholexplorer API URL (defaults to CROSSREF_WORKS_URL)
    :return: a dictionary with the status.
    """

    src_doi = shorten_doi(src_uri)
    ref_doi = shorten_doi(ref_uri)

    result = {
        "found": False,
        "message": "Reference not found in CrossRef metadata.",
        "status": 0,
    }
    access_url = f"{api_url}{src_doi}"

    data = get(access_url)
    if data is not None:
        if "reference" in data["message"].keys():
            for reference in data["message"]["reference"]:
                if reference.get("DOI", "").lower() == ref_doi:
                    result["found"] = True
                    result["reference"] = reference
                    result["message"] = f"Found {ref_doi} in formatted reference"
                    result["status"] = 2
                else:
                    for k, v in reference.items():
                        if ref_doi in v.lower():
                            result["found"] = True
                            result["reference"] = reference
                            result["message"] = f"Found {ref_doi} in {k} reference"
                            result["status"] = 1
                            break
                        if ref_title.lower() in v.lower():
                            result["found"] = True
                            result["reference"] = reference
                            result["message"] = f"Found title of {ref_doi} in {k} reference"
                            result["status"] = 1
                            break
                        title = v.lower()
                        ratio = fuzz.ratio(ref_title, title)
                        if ratio > 70:
                            result["found"] = True
                            result["reference"] = reference
                            result["message"] = f"Detected title of {ref_doi} in {k} reference ({ratio}%)"
                            result["status"] = 1

    return result


def import_doi(doi: URIRef) -> Graph:
    """Import CrossRef DOI metadata

    :param doi: DOI
    :return: Graph object with DOI metadata
    """
    print(f"Found DOI: {str(doi)}")
    metadata = get_single_doi(shorten_doi(doi))
    return parse_doi_metadata_to_graph(metadata)


def parse_doi_metadata_to_graph(metadata: Dict) -> Graph:
    """Parse CrossRef DOI metadata into Graph object.

    :param metadata: DOI metadata
    :return: Graph object with DOI metadata
    """
    g = Graph()
    doi = URIRefDoi(metadata["DOI"].lower())
    print(f"Found DOI: {str(doi)}")

    # CrossRef is the DOI metadata manager:
    g.add((doi, PROV.wasInformedBy, Literal("CrossRef")))
    # ObsParis is the publisher:
    g.add((doi, DCTERMS.publisher, Literal(metadata["publisher"])))
    # the PID is a DOI
    g.add((doi, BIBLINK.scheme, Literal("doi")))
    # the title:
    g.add((doi, DCTERMS.title, Literal(metadata["title"][0])))
    # the schema.org and DCMI types:
    g.add((doi, RDF.type, CROSSREF_TYPES[metadata["type"]]))
    # Creators:
    for creator in metadata["author"]:
        name = f"{creator['family']}, {creator['given']}"
        if "ORCID" in creator.keys():
            # if there is a NameIdentifier (ORCID)
            creator_id = creator["ORCID"]
            g.add((URIRef(creator_id), RDF.type, FOAF.Person))
            g.add((URIRef(creator_id), FOAF.name, Literal(name)))
            g.add((URIRef(creator_id), BIBLINK.scheme, Literal("orcid")))
            g.add((doi, DCTERMS.creator, URIRef(creator_id)))
        else:
            tmp = BNode(name)
            g.add((tmp, RDF.type, FOAF.Person))
            g.add((tmp, FOAF.name, Literal(name)))
            g.add((doi, DCTERMS.creator, tmp))

    return g
