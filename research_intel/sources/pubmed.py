from __future__ import annotations

import html
import logging
from typing import Any, Dict, Iterable, List

from research_intel.cache import CacheStore
from research_intel.http import HttpClient, HttpError
from research_intel.models import PublicationRecord, SourceResult
from research_intel.sources.base import DataSource


class PubMedSource(DataSource):
    name = "PubMed"
    search_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    fetch_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(
        self,
        http: HttpClient,
        cache: CacheStore,
        ttl_seconds: int,
        retmax: int = 25,
        email: str = "",
        tool: str = "research-intel-prototype",
    ):
        self.http = http
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.retmax = retmax
        self.email = email
        self.tool = tool
        self.logger = logging.getLogger(__name__)

    def fetch(self, target: str) -> SourceResult:
        key = f"pubmed:{target.lower()}:{self.retmax}"
        cached = self.cache.get(key, self.ttl_seconds)
        if cached is not None:
            return SourceResult(self.name, [PublicationRecord(**row) for row in cached], from_cache=True)

        try:
            ids = self._search_ids(target)
            if not ids:
                return SourceResult(self.name, [], [f"No PubMed records found for {target}"])
            records = self._summaries(ids)
        except HttpError as exc:
            return SourceResult(self.name, [], [str(exc)])

        self.cache.set(key, [record.to_dict() for record in records])
        return SourceResult(self.name, records)

    def _base_params(self) -> Dict[str, str]:
        params = {"retmode": "json", "tool": self.tool}
        if self.email:
            params["email"] = self.email
        return params

    def _search_ids(self, target: str) -> List[str]:
        params = self._base_params()
        params.update(
            {
                "db": "pubmed",
                "term": f'{target}[Title/Abstract] OR {target}[MeSH Terms]',
                "sort": "pub date",
                "retmax": str(self.retmax),
            }
        )
        payload = self.http.get_json(self.search_endpoint, params)
        return payload.get("esearchresult", {}).get("idlist", [])

    def _summaries(self, ids: Iterable[str]) -> List[PublicationRecord]:
        params = self._base_params()
        params.update({"db": "pubmed", "id": ",".join(ids)})
        payload = self.http.get_json(self.summary_endpoint, params)
        result = payload.get("result", {})
        records = []
        for pmid in result.get("uids", []):
            item = result.get(pmid, {})
            records.append(
                PublicationRecord(
                    pmid=pmid,
                    title=html.unescape(item.get("title", "")).rstrip("."),
                    authors=[author.get("name", "") for author in item.get("authors", [])[:8] if author.get("name")],
                    journal=item.get("fulljournalname") or item.get("source", "Unknown"),
                    publication_date=item.get("pubdate", ""),
                    abstract="",
                    keywords=[],
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                )
            )
        return records

