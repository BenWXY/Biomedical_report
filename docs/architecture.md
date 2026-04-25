# Architecture Design

## 1. Overall Architecture

The system is organized as a linear but extensible intelligence pipeline:

1. CLI/API layer receives a target name such as HER2, PD-L1, or KRAS G12C.
2. Source orchestrator invokes registered data source plugins.
3. Collectors fetch and normalize public data into shared dataclasses.
4. SQLite cache stores raw normalized results with TTL to reduce repeated network calls.
5. Analysis/report renderer aggregates records and generates Markdown/HTML output.
6. Report version metadata is stored for traceability and later comparison.

Module responsibilities:

- `research_intel.__main__`: command-line entrypoint and logging setup.
- `research_intel.app`: pipeline orchestration, deduplication, and version recording.
- `research_intel.sources`: public-data collectors behind a common `DataSource` interface.
- `research_intel.models`: normalized trial, publication, and bundle schemas.
- `research_intel.cache`: SQLite cache and report history.
- `research_intel.report`: structured analysis, tables, and embedded charts.
- `tests`: offline unit tests for core behavior.

## 2. Key Technology Choices

- Python 3.9+: fast to prototype, rich standard library, easy for reviewers to run.
- Standard library HTTP and SQLite: avoids fragile dependency installation during grading.
- ClinicalTrials.gov v2 API: official public trial registry data with structured fields.
- PubMed E-utilities: official literature metadata source.
- Markdown and HTML reports: readable, diffable, and easy to convert to PDF later.
- Pluggable source interface: adding ASCO/ESMO, patents, FDA/EMA/NMPA, or private databases only requires a new `DataSource` implementation.

## 3. Data Flow

1. User runs `python -m research_intel --target HER2`.
2. The pipeline loads environment-based settings and initializes cache/HTTP clients.
3. Each source receives the target and returns `SourceResult`.
4. Records are normalized as `TrialRecord` or `PublicationRecord`.
5. The pipeline deduplicates by stable identifiers such as NCT ID and PMID.
6. The renderer calculates phase distribution, publication year trend, sponsor concentration, and competitive signals.
7. Markdown/HTML files are written to `reports/`.
8. `report_versions` stores target, format, path, and timestamp.

## 4. Handling Large Result Sets and LLM Context Limits

For large data volumes, the production version should use a staged reduction strategy:

1. Retrieve and persist all source records incrementally.
2. Rank records by recency, phase, status, sponsor relevance, indication match, and source confidence.
3. Summarize each source independently into compact evidence blocks.
4. Feed only top-ranked records and source-level summaries into an LLM.
5. Preserve citations and source IDs so analysts can audit every conclusion.
6. Generate final sections from structured intermediate summaries instead of raw full records.

The current prototype implements deterministic aggregation plus an optional LLM summarizer behind a small interface. API keys are read from environment variables and are never committed. If the LLM key is missing or the LLM call fails, report generation falls back to deterministic local summaries.

## 5. Risk and Mitigation

- Public databases can lag sponsor disclosures. Mitigation: include source timestamps, warnings, and analyst review notes.
- API schemas can change. Mitigation: isolate parsing in collector modules and test normalization.
- Network instability can break live runs. Mitigation: retries, logging, cache, and offline fixtures.
- Duplicates across sources can distort counts. Mitigation: stable-ID deduplication.
- LLM hallucination risk. Mitigation: structured inputs, citation-preserving summaries, and deterministic fallback calculations.
- Sensitive credentials. Mitigation: environment configuration and no hard-coded API keys.

## 6. Future Extensions

- FDA/EMA/NMPA approval and label collectors.
- Patent collectors for WIPO/Google Patents/Lens.
- Conference abstract collectors for ASCO, ESMO, AACR, and ACR.
- Background asynchronous job queue with status endpoint.
- PDF rendering through a dedicated converter.
- Web UI with target history, report diffing, and source drill-down.
