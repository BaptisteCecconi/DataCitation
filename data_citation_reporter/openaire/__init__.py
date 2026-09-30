# -*- coding: utf-8 -*-
"""Module for handling OpenAire interfaces."""

from rdflib import Literal
from rdflib.namespace import PROV

from ..connect import get
from ..static import (
    SCHOLEXPLORER_V1_URL,
    SCHOLEXPLORER_V2_URL,
    SCHOLEXPLORER_V3_URL,
    OPENAIREGRAPH_V1_URL,
    OPENAIREGRAPH_V2_URL,
    OPENAIREGRAPH_V3_URL,
    OPENAIREGRAPH_V4_URL,
)
from ..rdf import Graph
from .scholexplorer_v3 import ScholexplorerResultV3
from .openaire_graph_v3 import OpenAireGraphLinksResultV3

# Current Default OpenAire API versions :
# - Scholexplorer v3
# - Openaire Graph v3


def get_scholexplorer(pid, api_version: int = 3, use_cache: bool = True):
    """Get citation data from OpenAire Scholexplorer API.

    :param pid: Persistent identifier
    :param api_version: version of the Scholexplorer API (should be 1, 2 or 3, default is 3)
    :param use_cache: Use cached data
    :return: citation data as a Graph object
    """

    doi = str(pid).replace("https://doi.org/", "")
    if api_version not in [1, 2, 3]:
        raise ValueError("API Version must be 1, 2 or 3")

    get_scholexplorer_api = {
        1: get_scholexplorer_v1,
        2: get_scholexplorer_v2,
        3: get_scholexplorer_v3,
    }

    return get_scholexplorer_api[api_version](doi, use_cache=use_cache)


def get_scholexplorer_v1(pid, api_url=SCHOLEXPLORER_V1_URL, use_cache: bool = True):
    raise NotImplementedError


def get_scholexplorer_v2(pid, api_url=SCHOLEXPLORER_V2_URL, use_cache: bool = True):
    raise NotImplementedError


# https://api.scholexplorer.openaire.eu/v3/Links?targetPid=10.25935%2Fwxv0-vr90&page=0&size=100
def get_scholexplorer_v3(pid, api_url=SCHOLEXPLORER_V3_URL, use_cache: bool = True):
    """Get citation data from OpenAire Scholexplorer V3 API.

    The query is done twice, to get relations where the PID is listed as a source or as a target.

    :param pid: Persistent identifier
    :param api_url: Openaire Scholexplorer API URL (defaults to SCHOLEXPLORER_V1_URL)
    :param use_cache: Use cached data
    :return: citation data as a Graph object
    """
    g = Graph()

    doi = str(pid).replace("https://doi.org/", "")

    for pid_role in ["targetPid", "sourcePid"]:
        access_url = f"{api_url}?{pid_role}={doi.replace('/', '%2F')}&page=0&size=100"

        data = get(access_url, use_cache=use_cache)
        if data is None:
            continue

        print(f"{pid_role}={doi}")
        data = ScholexplorerResultV3(data)

        for item in data.relations:
            print(item.source, item.relation, item.target)

            g.add_with_prov(
                (item.source, item.relation, item.target),
                prov={PROV.wasInformedBy: Literal("Openaire Scholexplorer v3")},
            )
    return g


def get_openaire_graph(pid, api_version: int = 3, use_cache: bool = True):
    """Get citation data from OpenAire Graph API.

    :param pid: Persistent identifier
    :param api_version: version of the OpenAire Graph API (should be 1, 2, 3 or 4 default is 3)
    :param use_cache: Use cached data
    :return: citation data as a Graph object
    """

    doi = str(pid).replace("https://doi.org/", "")
    if api_version not in [1, 2, 3, 4]:
        raise ValueError("API Version must be 1, 2, 3 or 4")

    get_openaire_graph_api = {
        1: get_openaire_graph_v1,
        2: get_openaire_graph_v2,
        3: get_openaire_graph_v3,
        4: get_openaire_graph_v4,
    }

    return get_openaire_graph_api[api_version](doi, use_cache=use_cache)


def get_openaire_graph_v1(pid, api_url=OPENAIREGRAPH_V1_URL, use_cache: bool = True):
    raise NotImplementedError


def get_openaire_graph_v2(pid, api_url=OPENAIREGRAPH_V2_URL, use_cache: bool = True):
    raise NotImplementedError


# https://api.openaire.eu/graph/v3/researchProducts/links?targetPid=10.25935%2Fnhb2-wy29&page=0&pageSize=100
def get_openaire_graph_v3(pid, api_url=OPENAIREGRAPH_V3_URL, use_cache: bool = True):
    """Get citation data from OpenAire Graph Links API.

    The query is done twice, to get relations where the PID is listed as a source or as a target.

    :param pid: Persistent identifier
    :param api_url: OpenAire Graph API URL (defaults to OPENAIREGRAPH_V1_URL)
    :param use_cache: Use cached data
    :return: citation data as a Graph object
    """
    g = Graph()

    doi = str(pid).replace("https://doi.org/", "")
    for pid_role in ["targetPid", "sourcePid"]:
        access_url = f"{api_url}?{pid_role}={doi.replace('/', '%2F')}&page=0&pageSize=100"

        data = get(access_url, use_cache=use_cache)
        if data is None:
            return g

        print(f"{pid_role}={doi}")
        data = OpenAireGraphLinksResultV3(data)

        for item in data.relations:
            print(item.source, item.relation, item.target)

            g.add_with_prov(
                (item.source, item.relation, item.target),
                prov={PROV.wasInformedBy: Literal("Openaire Graph Links v3")},
            )
    return g


#    data = data["results"]
#    print(f"{doi}: {len(data)}")
#    if len(data) > 0:
#        # citation_set = set()
#        for item in data:
#            source_pid = None
#            for identifier in item["source"]["identifiers"]:
#                if identifier["idScheme"] == "doi":
#                    source_pid = URIRefDoi(identifier["idUrl"])
#                    break
#            if source_pid is not None:
#                relation = OPENAIRE_RELATIONS[item["relType"]["typeSchema"]][item["relType"]["name"]]
#                provenance = item["provenance"]#
#
#                provenance = "OpenAIRE Graph (via " + ", ".join(provenance) + ")"
#
#                # citation_set.add((source_pid, relation, provenance))
#                print(f"{source_pid} {relation} {doi} ({provenance})")
#
#                g.add_with_prov(
#                    (source_pid, relation, pid),
#                    prov={PROV.wasInformedBy: Literal(provenance)},
#                )
#
#                g.add((source_pid, BIBLINK.scheme, Literal("doi")))
#
#    return g


def get_openaire_graph_v4(pid, api_url=OPENAIREGRAPH_V4_URL, use_cache: bool = True):
    raise NotImplementedError
