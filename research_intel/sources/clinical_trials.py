from __future__ import annotations

import logging
from typing import Any, Dict, List

from research_intel.cache import CacheStore
from research_intel.http import HttpClient, HttpError
from research_intel.models import SourceResult, TrialRecord
from research_intel.sources.base import DataSource


class ClinicalTrialsSource(DataSource):
    name = "ClinicalTrials.gov"
    endpoint = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, http: HttpClient, cache: CacheStore, ttl_seconds: int, page_size: int = 25):
        self.http = http
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.page_size = page_size
        self.logger = logging.getLogger(__name__)

    def fetch(self, target: str) -> SourceResult:
        key = f"clinicaltrials:{target.lower()}:{self.page_size}"
        cached = self.cache.get(key, self.ttl_seconds)
        if cached is not None:
            return SourceResult(self.name, [self._from_dict(row) for row in cached], from_cache=True)

        params = {
            "query.term": target,
            "pageSize": self.page_size,
            "format": "json",
        }
        try:
            payload = self.http.get_json(self.endpoint, params)
        except HttpError as exc:
            return SourceResult(self.name, [], [str(exc)])

        studies = payload.get("studies", [])
        records = [self._parse_study(study) for study in studies]
        records = [record for record in records if record.title]
        self.cache.set(key, [record.to_dict() for record in records])
        return SourceResult(self.name, records)

    def _parse_study(self, study: Dict[str, Any]) -> TrialRecord:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        contacts = protocol.get("contactsLocationsModule", {})

        nct_id = identification.get("nctId", "")
        phases = design.get("phases") or ["Unknown"]
        enrollment = design.get("enrollmentInfo", {}).get("count")
        interventions = [
            item.get("name", "")
            for item in arms.get("interventions", [])
            if item.get("name")
        ]
        countries = sorted(
            {
                location.get("country", "")
                for location in contacts.get("locations", [])
                if location.get("country")
            }
        )
        return TrialRecord(
            nct_id=nct_id,
            title=identification.get("briefTitle", ""),
            sponsor=sponsor.get("leadSponsor", {}).get("name", "Unknown"),
            phase=", ".join(phases),
            status=status.get("overallStatus", "Unknown"),
            enrollment=enrollment,
            interventions=interventions,
            countries=countries,
            start_date=status.get("startDateStruct", {}).get("date", ""),
            completion_date=status.get("completionDateStruct", {}).get("date", ""),
            url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
        )

    def _from_dict(self, row: Dict[str, Any]) -> TrialRecord:
        return TrialRecord(**row)

