# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""Module for handling OpenAire Graph V3 API."""

from enum import Enum

from pydantic import BaseModel
from rdflib import URIRef

from ..mappings import OPENAIRE_RELATIONS
from ..rdf import URIRefDoi, URIRefArXiv


class RecordTypeEnum(str, Enum):
    """RecordTypeEnum class for OpenAire Graph V3 API parsing"""

    publication = "publication"
    dataset = "dataset"
    other = "other"
    software = "software"
    datasource = "datasource"
    organization = "organization"
    project = "project"
    person = "person"


class OpenAccessRouteEnum(str, Enum):
    """OpenAccessRouteEnum class for OpenAire Graph V3 API parsing"""

    gold = "gold"
    green = "green"
    hybrid = "hybrid"
    bronze = "bronze"


class SearchHeader(BaseModel):
    """SearchHeader class for OpenAire Graph V3 API parsing"""

    debug: dict = None
    numFound: int = None
    maxScore: float | int = None
    queryTime: int = None
    page: int
    pageSize: int = None
    totalPages: int
    totalLinks: int
    totalCitationsCount: int = None
    countsByType: dict = None
    nextCursor: str = None


class Pid(BaseModel):
    """Pid class for OpenAire Graph V3 API parsing"""

    value: str
    typeCode: str
    typeLabel: str


class Provenance(BaseModel):
    """Provenance class for OpenAire Graph V3 API parsing"""

    dsId: str
    dsName: str


class AccessRight(BaseModel):
    """AccessRight class for OpenAire Graph V3 API parsing"""

    code: str
    label: str
    openAccessRoute: OpenAccessRouteEnum


class APC(BaseModel):
    """APC class for OpenAire Graph V3 API parsing"""

    currency: str
    amount: str


class CodeLabel(BaseModel):
    """CodeLabel class for OpenAire Graph V3 API parsing"""

    code: str
    label: str


class Measure(BaseModel):
    """Measure class for OpenAire Graph V3 API parsing"""

    id: str
    unit: list[CodeLabel]


class Country(BaseModel):
    """Country class for OpenAire Graph V3 API parsing"""

    code: str
    label: str


class Instance(BaseModel):
    """Instance class for OpenAire Graph V3 API parsing"""

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
    """Funder class for OpenAire Graph V3 API parsing"""

    id: str
    shortname: str
    name: str
    jurisdiction: Country
    pid: list[Pid]


class FundingLevel(BaseModel):
    """FundingLevel class for OpenAire Graph V3 API parsing"""

    id: str
    description: str
    name: str


class Funding(BaseModel):
    """Funding class for OpenAire Graph V3 API parsing"""

    funder: Funder
    level0: FundingLevel
    level1: FundingLevel
    level2: FundingLevel


class DeclaredAffiliation(BaseModel):
    """DeclaredAffiliation class for OpenAire Graph V3 API parsing"""

    rorId: str
    openOrgId: str


class AuthorPidSchemeValue(BaseModel):
    """AuthorPidSchemeValue class for OpenAire Graph V3 API parsing"""

    scheme: str
    value: str


class AuthorPid(BaseModel):
    """AuthorPid class for OpenAire Graph V3 API parsing"""

    id: AuthorPidSchemeValue
    provenance: Provenance


class Author(BaseModel):
    """Author class for OpenAire Graph V3 API parsing"""

    id: str
    fullName: str
    name: str
    surname: str
    rank: int
    pid: AuthorPid


class EoscIfGuidelines(BaseModel):
    """EoscIfGuidelines class for OpenAire Graph V3 API parsing"""

    code: str


class Language(BaseModel):
    """Language class for OpenAire Graph V3 API parsing"""

    code: str
    label: str


class ResultCountry(BaseModel):
    """ResultCountry class for OpenAire Graph V3 API parsing"""

    code: str
    label: str
    provenance: Provenance


class SubjectSchemeValue(BaseModel):
    """SubjectSchemeValue class for OpenAire Graph V3 API parsing"""

    scheme: str
    value: str


class Subject(BaseModel):
    """Subject class for OpenAire Graph V3 API parsing"""

    subject: SubjectSchemeValue
    provenance: Provenance


class BestAccessRight(BaseModel):
    """BestAccessRight class for OpenAire Graph V3 API parsing"""

    code: str
    label: str
    scheme: str


class ApiResearchProductsResponse(BaseModel):
    """ApiResearchProductsResponse class for OpenAire Graph V3 API parsing"""

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
    """ResearchProductsSearchResponseV3 class for OpenAire Graph V3 API parsing"""

    header: SearchHeader
    results: list[ApiResearchProductsResponse]
    facets: dict


class Identifier(BaseModel):
    """Identifier class for OpenAire Graph V3 API parsing"""

    id: str
    idScheme: str
    idUrl: str | None


class Entity(BaseModel):
    """Entity class for OpenAire Graph V3 API parsing"""

    name: str
    identifiers: list[Identifier]


class Node(BaseModel):
    """Node class for OpenAire Graph V3 API parsing"""

    identifiers: list[Identifier]
    title: str | None = None
    type: str | None = None
    instanceType: str | None = None
    publicationDate: str | None = None
    authors: list[Entity] | None = None
    collectedFrom: list[Entity] | None = None


class RelType(BaseModel):
    """RelType class for OpenAire Graph V3 API parsing"""

    name: str
    type: str = None
    typeSchema: str


class RelationType(BaseModel):
    """RelationType class for OpenAire Graph V3 API parsing"""

    source: Node
    target: Node
    relType: RelType


class SearchResponseRelationType(BaseModel):
    """SearchResponseRelationType class for OpenAire Graph V3 API parsing"""

    header: SearchHeader
    results: list[RelationType]
    facets: dict = None


class Relation:
    """Relation class"""

    def __init__(self, data):
        self.target = data.target
        self.source = data.source
        self.relation = data.relType

    @staticmethod
    def _identifiers(data):
        identifiers = {}
        for identifier in data:
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
        """target"""
        return self._select_pid(self._target)

    @target.setter
    def target(self, data):
        self._target = self._identifiers(data.identifiers)

    @property
    def source(self):
        """source"""
        return self._select_pid(self._source)

    @source.setter
    def source(self, data):
        self._source = self._identifiers(data.identifiers)

    @property
    def relation(self):
        """relation"""
        return self._relation[1]

    @relation.setter
    def relation(self, data):
        openaire_relation = data.name if data.type is None else data.type
        self._relation = (data.name, OPENAIRE_RELATIONS[data.typeSchema][openaire_relation])

    @property
    def relation_openaire(self):
        """relation (openaire version)"""
        return self._relation[0]


class OpenAireGraphLinksResultV3:
    """OpenAireGraphLinksResultV3 class"""

    def __init__(self, raw_data: dict):
        self.data = SearchResponseRelationType(**raw_data)
        print(f"Found {self.data.header.totalLinks} relations.")
        self.version = 3
        self.relations = [Relation(item) for item in self.data.results]
