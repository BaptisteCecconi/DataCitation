from .static import SCHOLEXPLORER_URL
from .namespaces import BIBLINK
from .mappings import OPENAIRE_SCHEMAS
from .rdf import URIRefDoi, URIRefArXiv, Graph
import requests
from json import JSONDecodeError
from rdflib import URIRef, Literal
from rdflib.namespace import DCTERMS, PROV


def get_scholexplorer(pid, api_url=SCHOLEXPLORER_URL):

    g = Graph()

    doi = str(pid).replace("https://doi.org/", "")
    access_url = f"{api_url}?pid={doi.replace('/', '%2F')}"
    print(f"requesting {access_url}")
    try:
        response = requests.get(access_url)
        data = response.json()
        print(f"{doi}: {len(data)}")
        if len(data) > 0:
            citation_set = set()
            for item in data:
                for identifiers in item["target"]["identifiers"]:
                    citation_set.add(
                        (identifiers["identifier"], identifiers["schema"])
                    )
            print(
                f"citing: {', '.join([f'{cite_item[1]}:{cite_item[0]}' for cite_item in citation_set])}"
            )
            src_pid = URIRefDoi(doi.lower())
            for identifier, schema in citation_set:
                if schema == "doi":
                    bib_pid = URIRefDoi(identifier)
                elif schema == "arXiv":
                    bib_pid = URIRefArXiv(identifier)
                elif schema == "handle":
                    bib_pid = URIRef(f"http://hdl.handle.net/{identifier}")
                elif schema == "pmc":
                    bib_pid = URIRef(
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{identifier}/"
                    )
                elif schema == "pmid":
                    bib_pid = URIRef(
                        f"https://pubmed.ncbi.nlm.nih.gov/{identifier}/"
                    )
                else:
                    bib_pid = None

                # Add triples both ways:

                # - data "isReferencedBy" bibref
                #                g.add_with_prov(
                #                    (src_pid, DCTERMS.isReferencedBy, bib_pid),
                #                    prov={PROV.wasInformedBy: Literal("scholexplorer")}
                #                )

                # - bibref "references" data
                g.add_with_prov(
                    (bib_pid, DCTERMS.references, src_pid),
                    prov={
                        PROV.wasInformedBy: Literal("Openaire Scholexplorer")
                    },
                )

                g.add((bib_pid, BIBLINK.scheme, Literal(schema)))

    except JSONDecodeError as e:
        print(doi, e)

    return g


# https://api.openaire.eu/graph/v1/researchProducts/links?targetPid=10.25935%2Fnhb2-wy29&page=0&pageSize=100
def get_openaire_graph(
    pid, api_url="https://api.openaire.eu/graph/v1/researchProducts/links"
):
    g = Graph()
    doi = str(pid).replace("https://doi.org/", "")
    access_url = f"{api_url}?targetPid={doi}&page=0&pageSize=100"
    print(f"requesting {access_url}")
    try:
        response = requests.get(access_url)
        data = response.json()["results"]
        print(f"{doi}: {len(data)}")
        if len(data) > 0:
            # citation_set = set()
            for item in data:
                source_pid = None
                for identifier in item["source"]["identifiers"]:
                    if identifier["idScheme"] == "doi":
                        source_pid = URIRefDoi(identifier["idUrl"])
                        break
                if source_pid is not None:
                    relation = OPENAIRE_SCHEMAS[item["relType"]["typeSchema"]][
                        item["relType"]["name"]
                    ]
                    provenance = item["provenance"]

                    provenance = (
                        "OpenAIRE Graph"
                        + f" (via {", ".join([prov for prov in provenance])})"
                    )

                    # citation_set.add((source_pid, relation, provenance))
                    print(f"{source_pid} {relation} {doi} ({provenance})")

                    g.add_with_prov(
                        (source_pid, relation, pid),
                        prov={PROV.wasInformedBy: Literal(provenance)},
                    )

                    g.add((source_pid, BIBLINK.scheme, Literal("doi")))

    except JSONDecodeError as e:
        print(doi, e)

    return g
