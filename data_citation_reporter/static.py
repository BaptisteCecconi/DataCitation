# -*- coding: utf-8 -*-
"""Utility module for static values."""

from rdflib.namespace import DCTERMS

from .namespaces import DCITE

DOI_PREFIX_PADC = "10.25935"

BIBLINKS_URL = "http://voparis-tap-maser.obspm.fr/__system__/biblinks/links/biblinks.json"
SCHOLEXPLORER_V1_URL = "http://api.scholexplorer.openaire.eu/v1/linksFromPid"
OPENAIREGRAPH_V1_URL = "https://api.openaire.eu/graph/v1/researchProducts/links"
OPENCITATIONS_URL = "http://opencitations.net/index/api/v1"
CROSSREF_EVENTDATA_URL = "https://api.eventdata.crossref.org/v1/events"
CROSSREF_DATACITATIONS_URL = "https://api.crossref.org/beta/datacitations/"
CROSSREF_WORKS_URL = "https://api.crossref.org/works/"
DOI_RA_URL = "https://doi.org/ra/"
DATACITE_DOIS_URL = "https://api.datacite.org/dois"

REVERSE_PROPERTY = {
    DCITE.IsPartOf: DCITE.HasPart,
    DCITE.HasPart: DCITE.IsPartOf,
    DCITE.Documents: DCITE.IsDocumentedBy,
    DCITE.IsDocumentedBy: DCITE.Documents,
    DCITE.Cites: DCITE.IsCitedBy,
    DCITE.IsCitedBy: DCITE.Cites,
    DCITE.References: DCITE.IsReferencedBy,
    DCITE.IsReferencedBy: DCITE.References,
    DCITE.IsDerivedFrom: DCITE.IsSourceOf,
    DCITE.IsSourceOf: DCITE.IsDerivedFrom,
    DCITE.IsDescribedBy: DCITE.Describes,
    DCITE.Describes: DCITE.IsDescribedBy,
    DCITE.IsNewVersionOf: DCITE.IsPreviousVersionOf,
    DCITE.IsPreviousVersionOf: DCITE.IsNewVersionOf,
    DCITE.IsSupplementTo: DCITE.Supplements,
    DCITE.Supplements: DCITE.IsSupplementTo,
    DCTERMS.isPartOf: DCTERMS.hasPart,
    DCTERMS.hasPart: DCTERMS.isPartOf,
    DCTERMS.references: DCTERMS.isReferencedBy,
    DCTERMS.isReferencedBy: DCTERMS.references,
}
