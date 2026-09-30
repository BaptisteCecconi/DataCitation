# -*- coding: utf-8 -*-
"""Module for handling OpenAire Graph V3 API."""

from enum import Enum

from pydantic import BaseModel
from rdflib import URIRef

from ..mappings import OPENAIRE_RELATIONS
from ..rdf import URIRefDoi, URIRefArXiv


class RecordTypeEnum(str, Enum):
    publication = "publication"
    dataset = "dataset"
    other = "other"
    software = "software"
    datasource = "datasource"
    organization = "organization"
    project = "project"
    person = "person"


class OpenAccessRouteEnum(str, Enum):
    gold = "gold"
    green = "green"
    hybrid = "hybrid"
    bronze = "bronze"


class SearchHeader(BaseModel):
    debug: dict
    numFound: int
    maxScore: float | int
    queryTime: int
    page: int
    pageSize: int
    totalPages: int
    totalLinks: int
    totalCitationsCount: int
    countsByType: dict
    nextCursor: str


class Pid(BaseModel):
    value: str
    typeCode: str
    typeLabel: str


class Provenance(BaseModel):
    dsId: str
    dsName: str


class AccessRight(BaseModel):
    code: str
    label: str
    openAccessRoute: OpenAccessRouteEnum


class APC(BaseModel):
    currency: str
    amount: str


class CodeLabel(BaseModel):
    code: str
    label: str


class Measure(BaseModel):
    id: str
    unit: list[CodeLabel]


class Country(BaseModel):
    code: str
    label: str


class Instance(BaseModel):
    license: str
    accessright: AccessRight
    instancetype: str
    hostedby: Provenance
    url: list[str]
    distributionlocation: str
    collectedfrom: Provenance
    pid: list[Pid]
    alternateIdentifier: list[Pid]
    dateofacceptance: str
    processingcharges: APC
    refereed: str
    measures: list[Measure]
    fulltext: str


class Funder(BaseModel):
    id: str
    shortname: str
    name: str
    jurisdiction: Country
    pid: list[Pid]


class FundingLevel(BaseModel):
    id: str
    description: str
    name: str


class Funding(BaseModel):
    funder: Funder
    level0: FundingLevel
    level1: FundingLevel
    level2: FundingLevel


class DeclaredAffiliation(BaseModel):
    rorId: str
    openOrgId: str


class AuthorPidSchemeValue(BaseModel):
    scheme: str
    value: str


class AuthorPid(BaseModel):
    id: AuthorPidSchemeValue
    provenance: Provenance


class Author(BaseModel):
    id: str
    fullName: str
    name: str
    surname: str
    rank: int
    pid: AuthorPid


class EoscIfGuidelines(BaseModel):
    code: str


class Language(BaseModel):
    code: str
    label: str


class ResultCountry(BaseModel):
    code: str
    label: str
    provenance: Provenance


class SubjectSchemeValue(BaseModel):
    scheme: str
    value: str


class Subject(BaseModel):
    subject: SubjectSchemeValue
    provenance: Provenance


class BestAccessRight(BaseModel):
    code: str
    label: str
    scheme: str


class ApiResearchProductsResponse(BaseModel):
    authors: list[Author]
    openAccessColor: OpenAccessRouteEnum
    publiclyFunded: bool
    eoscIfGuidelines: list[EoscIfGuidelines]
    type: str
    language: Language
    countries: list[ResultCountry]
    subjects: list[Subject]
    mainTitle: str
    subTitle: str
    descriptions: list[str]
    publicationDate: str
    publisher: str
    embargoEndDate: str
    sources: list[str]
    formats: list[str]
    contributors: list[str]
    coverages: list[str]
    bestAccessRight: BestAccessRight


class ResearchProductsSearchResponseV3(BaseModel):
    header: SearchHeader
    results: list[ApiResearchProductsResponse]
    facets: dict


class Identifier(BaseModel):
    id: str
    idScheme: str
    idUrl: str


class Entity(BaseModel):
    name: str
    identifiers: list[Identifier]


class Node(BaseModel):
    identifiers: list[Identifier]
    title: str
    type: str
    instanceType: str
    publicationDate: str
    authors: list[Entity]
    collectedFrom: list[Entity]


class RelType(BaseModel):
    name: str
    type: str
    typeSchema: str


class RelationType(BaseModel):
    source: Node
    target: Node
    relType: RelType


class SearchResponseRelationType(BaseModel):
    header: SearchHeader
    results: list[RelationType]
    facets: dict


class Relation:
    def __init__(self, data):
        self.target = data.target
        self.source = data.source
        self.relation = data.relType

    @staticmethod
    def _identifiers(data):
        identifiers = {}
        for identifier in data.Identifier:
            identifiers[identifier.idScheme] = (identifier.id, identifier.idUrl)
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

    @property
    def target(self):
        return self._select_pid(self._target)

    @target.setter
    def target(self, data):
        self._target = self._identifiers(data.identifiers)

    @property
    def source(self):
        return self._select_pid(self._source)

    @source.setter
    def source(self, data):
        self._source = self._identifiers(data.identifiers)

    @property
    def relation(self):
        return self._relation[1]

    @relation.setter
    def relation(self, data):
        self._relation = (data.name, OPENAIRE_RELATIONS[data.typeSchema][data.type])

    @property
    def relation_openaire(self):
        return self._relation[0]


class OpenAireGraphLinksResultV3:
    def __init__(self, raw_data: dict):
        self.data = SearchResponseRelationType(**raw_data)
        print(f"Found {self.data.header.totalLinks} relations.")
        self.version = 3
        self.relations = [Relation(item) for item in self.data.results]
