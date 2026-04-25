from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TrialRecord:
    nct_id: str
    title: str
    sponsor: str = "Unknown"
    phase: str = "Unknown"
    status: str = "Unknown"
    enrollment: Optional[int] = None
    interventions: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    start_date: str = ""
    completion_date: str = ""
    url: str = ""
    source: str = "ClinicalTrials.gov"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nct_id": self.nct_id,
            "title": self.title,
            "sponsor": self.sponsor,
            "phase": self.phase,
            "status": self.status,
            "enrollment": self.enrollment,
            "interventions": self.interventions,
            "countries": self.countries,
            "start_date": self.start_date,
            "completion_date": self.completion_date,
            "url": self.url,
            "source": self.source,
        }


@dataclass(frozen=True)
class PublicationRecord:
    pmid: str
    title: str
    authors: List[str] = field(default_factory=list)
    journal: str = "Unknown"
    publication_date: str = ""
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    url: str = ""
    source: str = "PubMed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "publication_date": self.publication_date,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "url": self.url,
            "source": self.source,
        }


@dataclass(frozen=True)
class SourceResult:
    source_name: str
    records: List[Any]
    warnings: List[str] = field(default_factory=list)
    from_cache: bool = False


@dataclass(frozen=True)
class IntelligenceBundle:
    target: str
    trials: List[TrialRecord]
    publications: List[PublicationRecord]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "trials": [trial.to_dict() for trial in self.trials],
            "publications": [pub.to_dict() for pub in self.publications],
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

