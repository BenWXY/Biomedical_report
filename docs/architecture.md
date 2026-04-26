# Architecture Design

Chinese version: [architecture_zh.md](architecture_zh.md).

This project is a target-centric biomedical competitive intelligence prototype. It collects public clinical trial and literature records for a target such as `HER2` or `PD-L1`, normalizes the data, optionally asks an LLM to draft the main narrative sections, and writes Markdown/HTML reports.

## 1. Runtime Flow

1. The CLI entrypoint receives a target, output format, language, and optional `--offline` / `--verbose` flags.
2. `Settings.from_env()` loads cache paths, report paths, source limits, API timeouts, PubMed metadata, and optional LLM settings.
3. `IntelligencePipeline.from_settings()` builds the cache, HTTP client, source list, LLM analyzer, and report renderer.
4. Each configured `DataSource` fetches records for the target and returns a `SourceResult`.
5. The pipeline separates records into `TrialRecord` and `PublicationRecord`, deduplicates them, and builds an `IntelligenceBundle`.
6. `LLMReportAnalyzer` optionally sends the structured bundle to an OpenAI-compatible Chat Completions API through the OpenAI Python SDK.
7. If LLM analysis succeeds, the four core report sections use the LLM output. If the key is missing or the call fails, the renderer uses deterministic local summaries.
8. `ReportRenderer` writes Markdown, HTML, or both to `reports/`.
9. `CacheStore.record_report()` stores report version metadata for traceability.

## 2. Main Modules

- `research_intel.__main__`: CLI parser, logging setup, pipeline invocation, and user-facing command output.
- `research_intel.config`: environment-based settings for cache, report output, public API behavior, and LLM provider configuration.
- `research_intel.app`: pipeline orchestration, source execution, deduplication, LLM analysis handoff, and report version recording.
- `research_intel.models`: shared dataclasses for `TrialRecord`, `PublicationRecord`, `SourceResult`, and `IntelligenceBundle`.
- `research_intel.http`: small resilient HTTP client used by live public data sources.
- `research_intel.cache`: SQLite-backed cache with a JSON fallback when SQLite is unavailable.
- `research_intel.llm`: optional OpenAI SDK-based report analyzer for OpenAI-compatible providers, including DashScope compatible mode.
- `research_intel.report`: deterministic report summaries, tables, embedded SVG charts, Markdown output, and dependency-free Markdown-to-HTML rendering.
- `research_intel.sources`: pluggable collectors behind the `DataSource` interface.
- `tests`: offline tests for orchestration and report generation.

## 3. Data Sources

The current live pipeline includes:

- `ClinicalTrialsSource`: queries ClinicalTrials.gov v2 and normalizes studies into `TrialRecord`.
- `PubMedSource`: queries PubMed E-utilities and normalizes articles into `PublicationRecord`.

Offline mode replaces live sources with:

- `OfflineDemoSource`: returns built-in HER2 records for deterministic local testing and grading.

All sources implement:

```python
def fetch(self, target: str) -> SourceResult:
```

`SourceResult` carries normalized records, source-level warnings, and whether the response came from cache. The pipeline currently renders `TrialRecord` and `PublicationRecord` directly. New source categories, such as approvals, patents, conference abstracts, or company pipeline pages, can initially map into these record types or introduce new model classes plus renderer support.

## 4. Caching And Persistence

`CacheStore` uses SQLite by default. It creates two tables:

- `cache_entries`: source API payloads keyed by source/query parameters with TTL-based reuse.
- `report_versions`: generated report path metadata keyed by target, format, path, and creation time.

If SQLite initialization or access fails, `CacheStore` falls back to a JSON file next to the configured SQLite path. This keeps the prototype runnable in restricted environments.

The default cache path is `.cache/research_intel.sqlite3`, but it can be changed with `RESEARCH_INTEL_CACHE`. Generated reports go to `reports/` by default and can be changed with `RESEARCH_INTEL_REPORTS`.

## 5. LLM Analysis

The LLM layer is optional and only affects narrative report sections. It does not collect data.

`LLMReportAnalyzer` receives the final `IntelligenceBundle`, builds a structured prompt containing top trial and publication records, and calls:

```python
client.chat.completions.create(...)
```

The expected model response is JSON with these keys:

- `target_overview`
- `pipeline_overview`
- `research_dynamics`
- `competitive_assessment`

The report renderer uses those values when `bundle.metadata["analysis_source"] == "llm"`. Otherwise it uses deterministic fallback summaries.

Provider configuration:

- OpenAI: `OPENAI_API_KEY`, optional `RESEARCH_INTEL_LLM_MODEL`, optional `RESEARCH_INTEL_LLM_ENDPOINT`.
- DashScope compatible mode: `DASHSCOPE_API_KEY`, typically `qwen-plus` and `https://dashscope.aliyuncs.com/compatible-mode/v1`.
- Explicit overrides: `RESEARCH_INTEL_LLM_API_KEY`, `RESEARCH_INTEL_LLM_MODEL`, `RESEARCH_INTEL_LLM_ENDPOINT`, `RESEARCH_INTEL_LLM_TIMEOUT`.

The code accepts either a base URL such as `https://api.openai.com/v1` or a legacy chat-completions endpoint such as `https://api.openai.com/v1/chat/completions`; it normalizes the latter into an SDK base URL.

## 6. Report Generation

The report renderer produces:

- Markdown reports for easy review, diffing, and editing.
- HTML reports for browser viewing.
- Embedded SVG charts for trial phase distribution and publication trends.

Reports are Chinese by default. `--language english` switches section labels and generated prose to English. If LLM output exists, it fills the four core sections; tables, charts, source notes, and deterministic calculations remain local.

The HTML renderer includes a small built-in Markdown converter. This keeps the project lightweight while handling common formatting that may appear in deterministic sections or LLM output, including headings, bullet lists, numbered lists, links, bold text, italics, inline code, tables, and embedded SVG charts.

## 7. Error Handling

The project favors graceful degradation:

- Live API failures are captured as source warnings where possible.
- Cache hits reduce repeated network dependency.
- Offline mode provides deterministic no-network execution.
- Missing or failing LLM configuration falls back to local summaries.
- `--verbose` enables debug logging for troubleshooting source and pipeline behavior.

## 8. Adding New Sources

To add a source:

1. Create a module under `research_intel/sources/`.
2. Implement `DataSource.fetch(target)`.
3. Normalize records into existing models or add a new model when the data deserves its own report section.
4. Return `SourceResult` with records and warnings.
5. Register the source in `research_intel/sources/__init__.py` if it should be imported from the package.
6. Add it to the live source list in `IntelligencePipeline.from_settings()`.
7. Add focused tests using offline fixtures or mocked payloads.

Good candidates are FDA approvals and labels, EMA/NMPA regulatory records, ASCO/ESMO/AACR conference abstracts, patent databases, company pipeline pages, and press releases.

## 9. Risks And Mitigations

- Public databases may lag sponsor disclosures. Mitigation: include source warnings and keep analyst review in the workflow.
- API schemas may change. Mitigation: isolate parsing in source modules and test normalization.
- Network instability can break live runs. Mitigation: cache, logging, warnings, and offline fixtures.
- Duplicate records can distort counts. Mitigation: deduplicate by stable IDs such as NCT ID and PMID.
- LLM output may hallucinate or overstate conclusions. Mitigation: pass structured inputs, require JSON, prohibit invented facts in the system prompt, and fall back to deterministic summaries.
- Credentials can leak if hard-coded. Mitigation: read API keys from environment variables only.

## 10. Future Extensions

- Dedicated models and report sections for approvals, patents, conferences, and company disclosures.
- Source ranking and staged summarization for large result sets.
- Citation-preserving LLM evidence blocks.
- PDF export.
- Web UI with target history, report comparison, and source drill-down.
- Background jobs for long-running live data collection.
