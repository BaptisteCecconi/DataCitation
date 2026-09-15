# -*- coding: utf-8 -*-
"""Utility module for storing mappings."""

from rdflib import URIRef
from rdflib.namespace import DCMITYPE, SDO, DCTERMS

from .namespaces import CITO, FRBR, VOREL

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


CROSSREF_TYPES = {
    "journal-article": SDO.ScholarlyArticle,
}

DATACITE_RELATIONS = {
    "IsCitedBy": CITO.isCitedBy,
    "Cites": CITO.cites,
    "IsSupplementTo": FRBR.supplementOf,
    "IsSupplementedBy": FRBR.supplement,
    "IsContinuedBy": FRBR.successor,
    "Continues": FRBR.successorOf,
    "IsDescribedBy": CITO.isDescribedBy,
    "Describes": CITO.describes,
    "HasMetadata": CITO.citesAsMetadataDocument,
    "IsMetadataFor": CITO.isCitedAsMetadataDocumentBy,
    "HasVersion": DCTERMS.hasVersion,
    "IsVersionOf": DCTERMS.isVersionOf,
    "IsPreviousVersionOf": FRBR.revision,
    "IsNewVersionOf": FRBR.revisionOf,
    "IsPartOf": DCTERMS.isPartOf,
    "HasPart": DCTERMS.hasPart,
    "IsPublishedIn": FRBR.partOf,
    "IsReferencedBy": CITO.isCitedForInformationBy,
    "References": CITO.citesForInformation,
    "IsDocumentedBy": CITO.isDocumentedBy,
    "Documents": CITO.documents,
    "IsCompiledBy": CITO.isCompiledBy,
    "Compiles": CITO.compiles,
    "IsVariantFormOf": FRBR.arrangementOf,
    "IsOriginalFormOf": FRBR.arrangement,
    "IsReviewedBy": CITO.isReviewedBy,
    "Reviews": CITO.reviews,
    "IsDerivedFrom": CITO.citesAsDataSource,
    "IsSourceOf": CITO.isCitedAsDataSourceBy,
    "IsRequiredBy": DCTERMS.isRequiredBy,
    "Requires": DCTERMS.requires,
    "IsObsoletedBy": DCTERMS.isReplacedBy,
    "Obsoletes": DCTERMS.replaces,
    "IsCollectedBy": CITO.providesDataFor,
    "Collects": CITO.usesDataFrom,
    "IsTranslationOf": FRBR.translationOf,
    "HasTranslation": FRBR.translation,
    "IsIdenticalTo": DCTERMS.identifier,
    "Other": DCTERMS.relation,
}

PREDICATE_REPRESENTATIONS = {
    # SPAR DataCite predicates
    CITO.isCitedBy: "is cited by",
    CITO.cites: "cites",
    FRBR.supplementOf: "is supplement to",
    FRBR.supplement: "is supplemented by",
    FRBR.successor: "is continued by",
    FRBR.successorOf: "continues",
    CITO.isDescribedBy: "is described by",
    CITO.describes: "describes",
    CITO.citesAsMetadataDocument: "has metadata",
    CITO.isCitedAsMetadataDocumentBy: "is metadata for",
    DCTERMS.hasVersion: "has version",
    DCTERMS.isVersionOf: "is version of",
    FRBR.revision: "is previous version of",
    FRBR.revisionOf: "is new version of",
    DCTERMS.isPartOf: "is part of",
    DCTERMS.hasPart: "has part",
    FRBR.partOf: "is published in",
    CITO.isCitedForInformationBy: "is referenced by",
    CITO.citesForInformation: "references",
    CITO.isDocumentedBy: "is documented by",
    CITO.documents: "documents",
    CITO.isCompiledBy: "is compiled by",
    CITO.compiles: "compiles",
    FRBR.arrangementOf: "is variant form of",
    FRBR.arrangement: "is original form of",
    CITO.isReviewedBy: "is reviewed by",
    CITO.reviews: "reviews",
    CITO.citesAsDataSource: "is derived from",
    CITO.isCitedAsDataSourceBy: "is source of",
    DCTERMS.isRequiredBy: "is required by",
    DCTERMS.requires: "requires",
    DCTERMS.isReplacedBy: "is obsoleted by",
    DCTERMS.replaces: "obsoletes",
    CITO.providesDataFor: "is collected by",
    CITO.usesDataFrom: "is collected by",
    FRBR.translationOf: "is translation of",
    FRBR.translation: "has translation",
    DCTERMS.identifier: "is identical to",
    DCTERMS.relation: "is related to",
    # extra predicates
    DCTERMS.references: "references",
    VOREL.Cites: "cites",
}


def datacite_relation(key: str) -> URIRef:
    """Resolve Datacite relations, as defined by SPAR/Datacite

    :param key: datacite relations key
    :return: Relation
    """

    def clean_up(key: str) -> str:
        # first check if the input key is in the list of DATACITE_RELATIONS keys, ignoring the case
        for item in DATACITE_RELATIONS.keys():
            if key.lower() == item.lower():
                return item
        key = key.replace(" ", "_")
        key = key.replace("-", "_")
        parts = key.split("_")
        if len(parts) > 1:
            return "".join([item.capitalize() for item in key.split("_")])
        else:
            return key[0].upper() + key[1:]

    clean_key = clean_up(key)
    print(clean_key)

    if clean_key in DATACITE_RELATIONS.keys():
        return DATACITE_RELATIONS[clean_key]
    else:
        raise KeyError(key)


def predicate_repr(term: str) -> str:
    """String representation as defined by Datacite

    :param uri: SPAR/Datacite equivalent URI
    :return: string representation
    """
    return PREDICATE_REPRESENTATIONS[term]


OPENAIRE_RELATIONS = {
    "datacite": {
        "cites": DATACITE_RELATIONS["Cites"],
        "compiles": DATACITE_RELATIONS["Compiles"],
        "continues": DATACITE_RELATIONS["Continues"],
        "documents": DATACITE_RELATIONS["Documents"],
        "haspart": DATACITE_RELATIONS["HasPart"],
        "isidenticalto": DATACITE_RELATIONS["IsIdenticalTo"],
        "isnewversionof": DATACITE_RELATIONS["IsNewVersionOf"],
        "issourceof": DATACITE_RELATIONS["IsSourceOf"],
        "obsoletes": DATACITE_RELATIONS["Obsoletes"],
        "references": DATACITE_RELATIONS["References"],
        "hasamongtopnsimilardocuments": DATACITE_RELATIONS["Other"],
    }
}

CROSSREF_RELATIONS = {
    "references": DATACITE_RELATIONS["References"],
    "cites": DATACITE_RELATIONS["Cites"],
    "is_part_of": DATACITE_RELATIONS["IsPartOf"],
    "is_supplemented_by": DATACITE_RELATIONS["IsSupplementedBy"],
    "is-supplemented-by": DATACITE_RELATIONS["IsSupplementedBy"],
}
