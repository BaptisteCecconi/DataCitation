# -*- coding: utf-8 -*-
"""Module for handling reports."""

from io import StringIO
from pathlib import Path
from typing import List, Dict

from rdflib import Literal
from rdflib.namespace import RDF, DCTERMS, PROV

from .biblinks import get_biblinks
from .crossref import get_datacitations, check_crossref
from .crossref import import_doi as crossref_import_doi
from .datacite import get_dois_from_prefix, check_datacite, import_doi, parse_doi_metadata_to_graph
from .datacite import import_doi as datacite_import_doi
from .doi import get_registration_agency
from .namespaces import BIBLINK, VOREL, DCITE
from .nasa_ads import get_nasa_ads
from .openaire import get_scholexplorer, get_openaire_graph
from .opencitations import get_opencitations
from .rdf import URIRefDoi, Graph, shorten_doi
from .static import DOI_PREFIX_PADC


class Report(Graph):
    """The Report class is a rdflib Graph class with a series of extra methods."""

    def __init__(
        self,
        doi: str | List[str] | None = None,
        metadata: List[Dict] | None = None,
        known_citations: List[str] | None = None,
        use_cache: bool = True,
    ):
        """Initialize the Report class.

        An instance must be initialized with a DOI or a list of DOIs, or the
        Datacite metadata extracted from the DOI or list of DOIs.

        :param doi: DOI or list of DOIs
        :param metadata: DOI metadata extracted from a DOI
        :param known_citations: list of known citations (DOIs)
        :param use_cache: use API call cache (default to True)
        """
        Graph.__init__(self)
        self.bind("biblink", BIBLINK)
        self.bind("vorel", VOREL)
        self.bind("dcite", DCITE)

        self.use_cache = use_cache
        if metadata is None and doi is not None:
            self.dois = doi
            for item in self.dois:
                for triple in import_doi(item):
                    self.add(triple)
        elif metadata is not None and doi is None:
            self.dois = [item["attributes"]["doi"].lower() for item in metadata]
            for md in metadata:
                for triple in parse_doi_metadata_to_graph(md):
                    self.add(triple)
        else:
            raise AttributeError("doi or metadata must be provided (exclusively)")

        self.known_citations = known_citations

    @property
    def dois(self):
        """Get list of DOIs"""
        return self._dois

    @dois.setter
    def dois(self, dois):
        """Set list of DOIs"""
        if not isinstance(dois, list):
            dois = [dois]
        self._dois = [URIRefDoi(doi) for doi in dois]

    @property
    def known_citations(self):
        """Get list of known citations"""
        return self._known_citations

    @known_citations.setter
    def known_citations(self, known_citations):
        """Set list of known citations"""
        if known_citations is None:
            known_citations = []
        elif not isinstance(known_citations, list):
            known_citations = [known_citations]
        self._known_citations = [URIRefDoi(item) for item in known_citations]
        self._import_known_citations()

    @classmethod
    def for_prefix(cls, doi_prefix=DOI_PREFIX_PADC):
        """Class method to return a Report object for a given DOI prefix"""
        g = cls(metadata=get_dois_from_prefix(doi_prefix=doi_prefix))
        return g

    def _import_known_citations(self):
        """Import known citations"""
        for doi in self.known_citations:
            print(f"Importing metadata for DOI: {str(doi)}")
            ra = get_registration_agency(doi)
            if ra == "Datacite":
                triples = datacite_import_doi(doi)
            elif ra == "Crossref":
                triples = crossref_import_doi(doi)
            else:
                raise AttributeError(f"Unknown registration agency {ra}")
            for triple in triples:
                self.add(triple)
            self.add_with_prov((doi, DCITE["cites"], self.dois[0]), prov={PROV.wasInformedBy: Literal("Curator")})

    def pids_from_publisher(self, publisher=None):
        """select PIDs from a publisher"""
        if publisher is None:
            return list(self.subjects(DCTERMS.publisher))

        return list(self.subjects(DCTERMS.publisher, Literal(publisher)))

    #        pids = []
    #        for s, p, o in self:
    #            if p == DCTERMS.publisher and str(o) == publisher:
    #                pids.append(s)
    #        return pids

    def _include_external_source(self, source, publisher, use_cache):
        """Include triples from an external source.

        :param source: a function to get the list of triples
        :param publisher: the publisher"""

        if use_cache is None:
            use_cache = self.use_cache
        for pid in self.pids_from_publisher(publisher):
            for triple in source(pid, use_cache=use_cache):
                self.add(triple)

    def include_biblinks(self, publisher=None, use_cache=None):
        """Include biblinks triples for PIDs of a publisher."""
        self._include_external_source(get_biblinks, publisher=publisher, use_cache=use_cache)

    def include_scholexplorer(self, publisher=None, use_cache=None):
        """Include scholexplorer triples for PIDs of a publisher."""
        self._include_external_source(get_scholexplorer, publisher=publisher, use_cache=use_cache)

    def include_openaire_graph(self, publisher=None, use_cache=None):
        """Include openaire graphs triples for PIDs of a publisher."""
        self._include_external_source(get_openaire_graph, publisher=publisher, use_cache=use_cache)

    def include_opencitations(self, publisher=None, use_cache=None):
        """Include opencitations triples for PIDs of a publisher."""
        self._include_external_source(get_opencitations, publisher=publisher, use_cache=use_cache)

    #    def include_crossref_eventdata(self, publisher=None):
    #        return self._include_external_source(get_eventdata, publisher=publisher)

    def include_crossref_datacitations(self, publisher=None, use_cache=None):
        """Include crossref datacitations triples for PIDs of a publisher."""
        self._include_external_source(get_datacitations, publisher=publisher, use_cache=use_cache)

    def include_nasa_ads(self, publisher=None, use_cache=None):
        """Include NASA ADS triples for PIDs of a publisher."""
        self._include_external_source(get_nasa_ads, publisher=publisher, use_cache=use_cache)

    def export_citations(self, doi=None, file_format="md", filename=None, use_cache=None):
        """Export citation data for given DOI.

        :param doi: DOI to export
        :param file_format: format to export (defaults to 'md')
        :param filename: filename to export to
        :param use_cache: whether to use cached data
        """

        if use_cache is None:
            use_cache = self.use_cache
        if filename is None:
            f = StringIO()
        else:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            f = open(filename, "w", encoding="utf-8")

        if (doi is None) and (len(self.dois) > 1):
            raise ValueError("doi must be provided")

        if file_format != "md":
            raise ValueError("file_format must be 'md'")

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
            items = {item_process(x) for x in self.objects(doi, item_property, unique=True)}
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

        # TODO: find a smarter way to do the following mapping
        citing_predicates = {
            DCITE.cites: "cites",
            DCITE.Cites: "cites",
            DCITE.isPartOf: "is part of",
            DCITE.IsPartOf: "is part of",
            DCITE.hasPart: "has part",
            DCITE.haspart: "has part",
            DCITE.HasPart: "has part",
            DCITE.documents: "documents",
            DCITE.IsDocumentedBy: "is documented by",
            DCITE.issourceof: "is source of",
            DCITE.IsDerivedFrom: "was derived from",
            DCITE.IsDescribedBy: "is described by",
            DCITE.references: "references",
            DCITE.References: "references",
            DCITE.IsReferencedBy: "is referenced by",
            DCITE.obsoletes: "obsoletes",
            DCITE.IsObsoletedBy: "is obsoleted by",
            DCITE.isnewversionof: "is new version of",
            DCITE.IsNewVersionOf: "is new version of",
            DCITE.IsSupplementTo: "is supplement to",
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
                    result = check_datacite(src_uri=citation, ref_uri=doi, use_cache=use_cache)
                elif ra.lower() == "crossref":
                    title = str(list(self.objects(URIRefDoi(doi), DCTERMS.title))[0]).lower()
                    result = check_crossref(src_uri=citation, ref_uri=doi, ref_title=title, use_cache=use_cache)
                else:
                    f.write(f"  Registration Agency {ra} is not supported.\n")
                    continue
                if "publisher" in result.keys():
                    f.write(f"  Publisher: {result["publisher"]}\n\n")
                if "container" in result.keys():
                    f.write(f"  Container: {"; ".join(result["container"])}\n\n")
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
