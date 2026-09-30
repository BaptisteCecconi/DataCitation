# -*- coding: utf-8 -*-
"""Module for handling OpenAire Scholexplorer V3 API."""

from pydantic import BaseModel
from rdflib import URIRef

from ..mappings import OPENAIRE_RELATIONS
from ..rdf import URIRefDoi, URIRefArXiv


class RelationshipType(BaseModel):
    Name: str
    SubType: str
    SubTypeSchema: str


class ScholixIdentifierType(BaseModel):
    ID: str
    IDScheme: str
    IDURL: str | None


class ScholixCreatorType(BaseModel):
    name: str
    identifier: list[ScholixIdentifierType]


class ScholixLinkProviderType(BaseModel):
    name: str
    identifier: list[ScholixIdentifierType]


class ScholixItemType(BaseModel):
    Identifier: list[ScholixIdentifierType]
    Title: str
    Type: str
    subType: str
    Creator: list[ScholixCreatorType]
    PublicationDate: str
    Publisher: list[ScholixLinkProviderType]


class ScholixType(BaseModel):
    RelationshipType: RelationshipType
    source: ScholixItemType
    target: ScholixItemType
    HarvestDate: str
    LicenseURL: str | None
    LinkProvider: list[ScholixLinkProviderType]
    LinkPublicationDate: str


class PageResultType(BaseModel):
    currentPage: int = 1
    totalLinks: int = 1
    totalPages: int = 1
    result: list[ScholixType]


class Relation:
    def __init__(self, data):
        self.target = data.target
        self.source = data.source
        self.relation = data.RelationshipType

    @staticmethod
    def _identifiers(data):
        identifiers = {}
        for identifier in data.Identifier:
            identifiers[identifier.IDScheme] = (identifier.ID, identifier.IDURL)
        return identifiers

    @staticmethod
    def _select_pid(identifier_data):
        pid_schemes = list(identifier_data.keys())
        for scheme, uri_function in [
            ("doi", URIRefDoi),
            ("arXiv", URIRefArXiv),
            ("handle", lambda x: URIRef(f"http://hdl.handle.net/{x}")),
            ("pmc", lambda x: URIRef(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{x}/")),
            ("pmid", lambda x: URIRef(f"https://pubmed.ncbi.nlm.nih.gov/{x}/")),
        ]:
            if scheme in pid_schemes:
                return uri_function(identifier_data[scheme][0])
        return URIRef(identifier_data["openaireIdentifier"][1])

    #        if "doi" in pid_schemes:
    #            return URIRefDoi(identifier)
    #        if "arXiv" in pid_schemes:
    #            return URIRefArXiv(identifier)
    #        if "handle" in pid_schemes:
    #            return URIRef(f"http://hdl.handle.net/{identifier}")
    #        if  in pid_schemes:
    #            return URIRef(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{identifier}/")
    #        if pid_scheme == "pmid":
    #            return URIRef(f"https://pubmed.ncbi.nlm.nih.gov/{identifier}/")

    @property
    def target(self):
        return self._select_pid(self._target)

    @target.setter
    def target(self, data):
        self._target = self._identifiers(data)

    @property
    def target_ids(self):
        return self._target

    @property
    def source(self):
        return self._select_pid(self._source)

    @source.setter
    def source(self, data):
        self._source = self._identifiers(data)

    @property
    def source_ids(self):
        return self._source

    @property
    def relation(self):
        return self._relation[1]

    @relation.setter
    def relation(self, data):
        self._relation = (data.Name, OPENAIRE_RELATIONS[data.SubTypeSchema][data.SubType])

    @property
    def relation_openaire(self):
        return self._relation[0]


class ScholexplorerResultV3:

    def __init__(self, raw_data: dict):
        self.data = PageResultType(**raw_data)
        print(f"Found {self.data.totalLinks} relations.")
        self.version = 3
        self.relations = [Relation(item) for item in self.data.result]
