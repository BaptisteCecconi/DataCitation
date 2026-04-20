import rdflib
from rdflib import URIRef, BNode
from rdflib.namespace import RDF
from .static import REVERSE_PROPERTY


def URIRefDoi(pid):
    """Create a URIRef for a DOI.

    The DOI input syntax is checked to provide a homogeneous output

    :param pid: identifier for the DOI
    :return: URIRef for the DOI
    """

    pidl = pid.lower()
    if pidl.startswith("https://doi.org/"):
        uri = pidl
    elif pidl.startswith("http://doi.org/"):
        uri = pidl.replace("http://doi.org/", "https://doi.org/")
    elif pidl.startswith("http://dx.doi.org/"):
        uri = pidl.replace("http://dx.doi.org/", "https://doi.org/")
    elif pidl.startswith("https://dx.doi.org/"):
        uri = pidl.replace("https://dx.doi.org/", "https://doi.org/")
    elif pidl.startswith("doi:"):
        uri = pidl.replace("doi:", "https://doi.org/")
    elif pidl.startswith("10."):
        uri = f"https://doi.org/{pidl}"
    else:
        raise ValueError(f"Invalid DOI syntax: {pid}")
    return URIRef(uri)


def shorten_doi(uri):
    return str(uri).replace("https://doi.org/", "")


def URIRefBibcode(pid):
    """Create a URIRef for a Bibcode.

    The Bibcode input syntax is checked to provide a homogeneous output

    :param pid: identifier for the Bibcode
    :return: URIRef for the Bibcode
    """
    if pid.startswith("https://adsabs.harvard.edu/abs/"):
        uri = pid
    elif pid.startswith("https://ui.adsabs.harvard.edu/abs/"):
        uri = pid.replace("https://ui.", "https://")
    else:
        uri = f"https://adsabs.harvard.edu/abs/{pid}"
    return URIRef(uri)


def URIRefArXiv(pid):
    """Create a URIRef for an ArXiv.

    The ArXiv input syntax is checked to provide a homogeneous output

    :param pid: identifier for the ArXiv
    :return: URIRef for the ArXiv
    """
    if pid.startswith("https://arxiv.org/abs/"):
        uri = pid
    else:
        uri = f"https://arxiv.org/abs/{pid}"
    return URIRef(uri)


def reverse(predicate_uri):
    """Reverse a predicate URI.

    :param predicate_uri: predicate URI
    :return: reversed predicate URI
    """
    return REVERSE_PROPERTY[predicate_uri]


class Graph(rdflib.Graph):
    def add_with_prov(self, triple, prov=None):
        """New method to add triple and include provenance metadata about the triple."""
        if prov is not None:
            t = BNode()
            s, p, o = triple
            self.add((t, RDF.type, RDF.Statement))
            self.add((t, RDF.subject, s))
            self.add((t, RDF.predicate, p))
            self.add((t, RDF.object, o))
            for k, v in prov.items():
                self.add((t, k, v))
        self.add(triple)
