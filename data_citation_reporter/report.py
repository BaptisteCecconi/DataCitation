# -*- coding: utf-8 -*-
from .namespaces import BIBLINK, VOREL, DCITE
from .datacite import get_dois_from_prefix, get_single_doi, check_datacite
from .mappings import RESOURCE_TYPE_SDO_DCMITYPE
from .nasa_ads import get_nasa_ads
from .doi import get_registration_agency
from .static import DOI_PREFIX_PADC
from .rdf import (
    URIRefDoi,
    URIRefBibcode,
    URIRefArXiv,
    Graph,
    shorten_doi,
)
from .biblinks import get_biblinks
from .openaire import get_scholexplorer, get_openaire_graph
from .opencitations import get_opencitations
from .crossref import get_datacitations, check_crossref
from typing import List, Union, Dict
from rdflib import Literal, URIRef, BNode
from rdflib.namespace import RDF, DCTERMS, PROV, SDO, FOAF


class Report(Graph):
    """The Report class is a rdflib Graph class with a series of extra methods."""

    def __init__(
        self,
        doi: Union[str, List[str]] = None,
        metadata: List[Dict] = None,
        known_citations: List[str] = None,
    ):
        """Initialize the Report class.

        An instance must be initialized with a DOI or a list of DOIs, or the
        Datacite metadata extracted from the DOI or list of DOIs.
        :param doi:
        :param metadata:
        :param known_citations:
        """
        Graph.__init__(self)
        self.bind("biblink", BIBLINK)
        self.bind("vorel", VOREL)
        self.bind("dcite", DCITE)

        self.known_citations = known_citations

        try:
            assert (doi is not None) or (metadata is not None)
        except AssertionError:
            raise AssertionError("doi or metadata must be provided")

        if metadata is None:
            self.dois = doi
            for doi in self.dois:
                doi_short = str(doi).replace("https://doi.org/", "")
                self._import_doi_metadata(get_single_doi(doi_short))

        if doi is None:
            self.dois = [item["attributes"]["doi"].lower() for item in metadata]
            for md in metadata:
                self._import_doi_metadata(md)

    @property
    def dois(self):
        return self._dois

    @dois.setter
    def dois(self, dois):
        if not isinstance(dois, list):
            dois = [dois]
        self._dois = [URIRefDoi(doi) for doi in dois]

    @property
    def known_citations(self):
        return self._known_citations

    @known_citations.setter
    def known_citations(self, known_citations):
        if known_citations is None:
            known_citations = []
        elif not isinstance(known_citations, list):
            known_citations = [known_citations]
        self._known_citations = [URIRefDoi(item) for item in known_citations]

    @classmethod
    def for_prefix(cls, doi_prefix=DOI_PREFIX_PADC):
        g = cls(metadata=get_dois_from_prefix(doi_prefix=doi_prefix))
        return g

    def _import_doi_metadata(self, metadata):
        doi = URIRefDoi(metadata["attributes"]["doi"].lower())
        print(f"Found DOI: {str(doi)}")
        # DataCite is the DOI metadata manager:
        self.add((doi, PROV.wasInformedBy, Literal("DataCite")))
        # ObsParis is the publisher:
        self.add((doi, DCTERMS.publisher, Literal("ObsParis")))
        # the PID is a DOI
        self.add((doi, BIBLINK.scheme, Literal("doi")))
        # the title:
        self.add(
            (
                doi,
                DCTERMS.title,
                Literal(metadata["attributes"]["titles"][0]["title"]),
            )
        )
        # the schema.org and DCMI types:
        self.add((doi, RDF.type, SDO[metadata["attributes"]["types"]["schemaOrg"]]))
        self.add(
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
                self.add((URIRef(creator_id), RDF.type, FOAF.Person))
                self.add((URIRef(creator_id), FOAF.name, Literal(creator["name"])))
                self.add((URIRef(creator_id), BIBLINK.scheme, Literal("orcid")))
                self.add((doi, DCTERMS.creator, URIRef(creator_id)))
            else:
                tmp = BNode()
                self.add((tmp, RDF.type, FOAF.Person))
                self.add((tmp, FOAF.name, Literal(creator["name"])))
                self.add((doi, DCTERMS.creator, tmp))

        for reference in metadata["attributes"]["relatedIdentifiers"]:
            try:
                related_id = reference["relatedIdentifier"].lower()
            except KeyError:
                print(reference)
                continue
            related_id_type = reference["relatedIdentifierType"].lower()
            if related_id_type == "doi":
                related_uri = URIRefDoi(related_id)
            elif related_id_type == "bibcode":
                related_uri = URIRefBibcode(related_id)
            elif related_id_type == "arxiv":
                related_uri = URIRefArXiv(related_id)
            else:
                related_uri = URIRef(related_id)
            # print(doi, related_uri)
            self.add_with_prov(
                (doi, DCITE[reference["relationType"]], related_uri),
                prov={PROV.wasInformedBy: Literal("ObsParis")},
            )

        for citation in metadata["relationships"]["citations"]["data"]:
            if citation["type"] == "dois":
                related_doi = URIRefDoi(citation["id"])
            else:
                print(f"{citation['type']} citation type is not supported")
                continue
            self.add_with_prov(
                (related_doi, DCITE.cites, doi),
                prov={PROV.wasInformedBy: Literal("DataCite Commons")},
            )
        for part in metadata["relationships"]["parts"]["data"]:
            if part["type"] == "dois":
                related_doi = URIRefDoi(part["id"])
            else:
                print(f"{citation['type']} citation type is not supported")
                continue
            self.add_with_prov(
                (related_doi, DCITE.hasPart, doi),
                prov={PROV.wasInformedBy: Literal("DataCite Commons")},
            )
        for part in metadata["relationships"]["partOf"]["data"]:
            if part["type"] == "dois":
                related_doi = URIRefDoi(part["id"])
            else:
                print(f"{citation['type']} citation type is not supported")
                continue
            self.add_with_prov(
                (related_doi, DCITE.isPartOf, doi),
                prov={PROV.wasInformedBy: Literal("DataCite Commons")},
            )

    def pids_from_publisher(self, publisher):
        """select PIDs from a publisher"""
        pids = []
        for s, p, o in self:
            if p == DCTERMS.publisher and str(o) == publisher:
                pids.append(s)
        return pids

    def _include_external_source(self, source, publisher):
        for pid in self.pids_from_publisher(publisher):
            for triple in source(pid):
                self.add(triple)

    def include_biblinks(self, publisher="ObsParis"):
        self._include_external_source(get_biblinks, publisher=publisher)

    def include_scholexplorer(self, publisher="ObsParis"):
        self._include_external_source(get_scholexplorer, publisher=publisher)

    def include_openaire_graph(self, publisher="ObsParis"):
        self._include_external_source(get_openaire_graph, publisher=publisher)

    def include_opencitations(self, publisher="ObsParis"):
        self._include_external_source(get_opencitations, publisher=publisher)

    #    def include_crossref_eventdata(self, publisher="ObsParis"):
    #        return self._include_external_source(get_eventdata, publisher=publisher)

    def include_crossref_datacitations(self, publisher="ObsParis"):
        return self._include_external_source(get_datacitations, publisher=publisher)

    def include_nasa_ads(self, publisher="ObsParis"):
        return self._include_external_source(get_nasa_ads, publisher=publisher)

    def export_citations(self, doi=None, format="md", filename=None):

        if filename is None:
            from io import StringIO

            f = StringIO()
        else:
            from pathlib import Path

            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            f = open(filename, "w")

        if (doi is None) and (len(self.dois) > 1):
            raise ValueError("doi must be provided")
        else:
            doi = self.dois[0]

        citing_pids = set()
        # if filename is None:
        #    filename = f"citations.{format}"

        # with open(filename, "w") as f:
        #    f.write(f"# Data citation report for : {doi}\n")

        f.write(f"# Data citation report for: {doi}\n")
        f.write("\n-------\n")
        doi_metadata = [
            ("title", DCTERMS.title, lambda x: str(x)),
            ("creators", DCTERMS.creator, lambda x: f"[{str(x).split('/')[-1]}]({str(x)})"),
            ("publisher", DCTERMS.publisher, lambda x: str(x)),
            ("product type", RDF.type, lambda x: str(x).split("/")[-1]),
        ]
        for item_name, item_property, item_process in doi_metadata:
            items = set([item_process(x) for x in self.objects(doi, item_property, unique=True)])
            for item in items:
                f.write(f" - **{item_name}**: {item}\n")

        query = """
        PREFIX RDF: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?subject
        WHERE {
            ?statement a RDF:Statement .
            ?statement RDF:subject ?subject .
        }
        """
        nb_citation = len(set(self.query(query)))
        f.write(f"## Number of research products citing the resource: {nb_citation}\n")
        f.write("\n-------\n")
        f.write("## Relations\n")
        f.write("### Known Citations (manual input)\n")
        if len(self.known_citations) > 0:
            for citation in sorted(self.known_citations):
                f.write(f"- {citation}\n")
                citing_pids.add(citation)
        else:
            f.write("- No known citations\n")

        f.write("\n")
        f.write("-------\n")
        f.write("### Discovered Relations\n")
        relations = {}
        query = """
PREFIX RDF: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX PROV: <http://www.w3.org/ns/prov#>
SELECT ?subject ?predicate ?object ?provenance
WHERE {
    ?statement a RDF:Statement .
    ?statement RDF:subject ?subject .
    ?statement RDF:predicate ?predicate .
    ?statement RDF:object ?object .
    ?statement PROV:wasInformedBy ?provenance .
}
"""
        for result in self.query(query):
            subj, predicate, obj, provenance = result
            # if subj == doi:
            #    predicate = reverse(predicate)
            #    subj, obj = obj, subj

            citing_pids.add(subj)
            relations.setdefault(subj, []).append((predicate, obj, provenance))
        #            if subj in relations:
        #                relations[subj].append((predicate, obj, provenance))
        #            else:
        #                relations[subj] = [(predicate, obj, provenance)]

        citing_predicates = {
            DCITE.cites: "cites",
            DCITE.isPartOf: "is part of",
            DCITE.hasPart: "has part",
            DCITE.HasPart: "has part",
            DCITE.documents: "documents",
            DCITE.IsDocumentedBy: "is documented by",
            DCITE.issourceof: "is source of",
            DCITE.IsDerivedFrom: "is derived from",
            DCITE.references: "references",
            DCTERMS.references: "references",
            VOREL.Cites: "cites",
            VOREL.IsSupplementedBy: "is supplemented by",
        }
        for subj in citing_pids:
            f.write(f"- {subj}\n")
            for pred, obj, prov in relations[subj]:
                f.write(f"  - {citing_predicates[pred]} {obj} [{prov}]\n")
        #        for k in sorted(relations.keys()):
        #            f.write(f"- {k}:\n")
        #            for pred, obj, prov in relations[k]:
        #                f.write(f"  {obj} {pred} {k} [{prov}]\n")
        #            for predicate, object, provenance in v:
        #                print(f"- {k} {str(predicate).split('/')[-1]} {object} [{provenance}]")
        f.write("\n")
        f.write("-------\n")
        f.write("## DOI Metadata Citation Assessment Report:\n")
        buttons = ["🔴", "⚪️", "🟢"]
        for citation in sorted(list(citing_pids)):
            try:
                f.write(f"- Verifying [{shorten_doi(citation)}]({citation}):\n\n")
                ra = get_registration_agency(citation)
                if ra.lower() == "datacite":
                    result = check_datacite(src_uri=citation, ref_uri=doi)
                elif ra.lower() == "crossref":
                    title = str(list(self.objects(URIRefDoi(doi), DCTERMS.title))[0]).lower()
                    result = check_crossref(src_uri=citation, ref_uri=doi, ref_title=title)
                else:
                    f.write(f"  Registration Agency {ra} is not supported.\n")
                    continue
                f.write(f"  {buttons[result['status']]} {result['message']}\n")
                if result["found"]:
                    f.write("  ```\n")
                    f.write("  {\n")
                    for k, v in result["reference"].items():
                        f.write(f"    '{k}': '{v}'\n")
                    f.write("  }\n")
                    f.write("  ```\n")
            except ValueError as e:
                f.write(f"  {e}\n")
                f.write("  Skipping.\n")
        if filename is None:
            f.flush()
            f.seek(0)
            print(f.read())
            f.close()
        else:
            f.flush()
            f.close()
