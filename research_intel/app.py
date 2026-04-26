from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from research_intel.cache import CacheStore
from research_intel.config import Settings
from research_intel.http import HttpClient
from research_intel.llm import LLMReportAnalyzer
from research_intel.models import IntelligenceBundle, PublicationRecord, TrialRecord
from research_intel.report import ReportRenderer
from research_intel.sources import ClinicalTrialsSource, DataSource, OfflineDemoSource, PubMedSource


@dataclass(frozen=True)
class RunResult:
    bundle: IntelligenceBundle
    report_paths: List[Path]


class IntelligencePipeline:
    def __init__(self, settings: Settings, sources: Iterable[DataSource], analyzer: LLMReportAnalyzer = None):
        self.settings = settings
        self.sources = list(sources)
        self.cache = CacheStore(settings.cache_path)
        self.analyzer = analyzer
        self.renderer = ReportRenderer()
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_settings(cls, settings: Settings, offline: bool = False) -> "IntelligencePipeline":
        cache = CacheStore(settings.cache_path)
        http = HttpClient(settings.timeout_seconds)
        ttl_seconds = settings.cache_ttl_hours * 3600
        if offline:
            sources: List[DataSource] = [OfflineDemoSource()]
        else:
            sources = [
                ClinicalTrialsSource(http, cache, ttl_seconds, settings.max_trials),
                PubMedSource(
                    http,
                    cache,
                    ttl_seconds,
                    settings.max_publications,
                    settings.pubmed_email,
                    settings.pubmed_tool,
                ),
            ]
        analyzer = None
        if not offline:
            analyzer = LLMReportAnalyzer(
                api_key=settings.llm_api_key,
                endpoint=settings.llm_endpoint,
                model=settings.llm_model,
                timeout_seconds=settings.llm_timeout_seconds,
            )
        pipeline = cls(settings, sources, analyzer)
        pipeline.cache = cache
        return pipeline

    def run(self, target: str, format_name: str = "markdown", language: str = "chinese") -> RunResult:
        target = target.strip()
        if not target:
            raise ValueError("target must not be empty")

        trials: List[TrialRecord] = []
        publications: List[PublicationRecord] = []
        warnings: List[str] = []
        cache_sources: List[str] = []

        for source in self.sources:
            self.logger.info("Fetching source=%s target=%s", source.name, target)
            result = source.fetch(target)
            warnings.extend(result.warnings)
            if result.from_cache:
                cache_sources.append(result.source_name)
            for record in result.records:
                if isinstance(record, TrialRecord):
                    trials.append(record)
                elif isinstance(record, PublicationRecord):
                    publications.append(record)

        metadata = {"cache_sources": cache_sources, "source_count": len(self.sources)}
        bundle = IntelligenceBundle(
            target=target,
            trials=self._dedupe_trials(trials),
            publications=self._dedupe_publications(publications),
            warnings=warnings,
            metadata=metadata,
        )
        if self.analyzer:
            analysis = self.analyzer.analyze(bundle, language)
            if analysis:
                metadata["llm_analysis"] = analysis
                metadata["analysis_source"] = "llm"
            else:
                metadata["analysis_source"] = "deterministic_fallback"
        paths = self.renderer.write(bundle, self.settings.reports_dir, format_name, language)
        for path in paths:
            self.cache.record_report(target, path.suffix.lstrip("."), path)
        return RunResult(bundle, paths)

    def _dedupe_trials(self, records: List[TrialRecord]) -> List[TrialRecord]:
        seen = set()
        output = []
        for record in records:
            key = record.nct_id or record.title.lower()
            if key not in seen:
                seen.add(key)
                output.append(record)
        return output

    def _dedupe_publications(self, records: List[PublicationRecord]) -> List[PublicationRecord]:
        seen = set()
        output = []
        for record in records:
            key = record.pmid or record.title.lower()
            if key not in seen:
                seen.add(key)
                output.append(record)
        return output
