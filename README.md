# Research Intelligence Prototype

Chinese documentation is available in [README_zh.md](README_zh.md). A longer guide is available in [README_detailed.md](README_detailed.md). Architecture docs are available in English [architecture.md](docs/architecture.md) and Chinese [architecture_zh.md](docs/architecture_zh.md).

This project implements a runnable Python prototype for target-centric biomedical competitive intelligence. It collects data from public sources, normalizes the records, caches query results, and generates structured Markdown/HTML reports.

## Features

- Pluggable data source architecture.
- ClinicalTrials.gov v2 API collector.
- PubMed E-utilities collector.
- Offline demo fixtures for deterministic grading and local testing without public API or LLM calls.
- SQLite cache with TTL and report version history.
- Markdown and HTML report output, with Chinese as the default report language.
- HTML reports convert common Markdown formatting from LLM-generated text into real HTML.
- Optional LLM analysis layer for target overview, pipeline summary, research dynamics, and competitive assessment.
- Inline SVG charts for trial phase distribution and publication trend.
- Basic logging and resilient network/API error handling.
- Unit tests for source orchestration, report generation, LLM fallback behavior, and Markdown-to-HTML rendering.

## Quick Start

Create a fresh virtual environment from the project root. The commands below install the app and its runtime dependencies, including the OpenAI Python SDK used for optional LLM analysis.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks activation scripts, use the venv interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Generate a deterministic offline demo report. Offline mode uses the built-in demo records only; it does not call public APIs or the LLM, even when an LLM API key is configured.

```powershell
python -m research_intel --target HER2 --offline --format both
```

Generated files are written to `reports/`. Reports are generated in Chinese by default. Offline HER2 sample reports are included at `reports/sample_HER2_offline.md` and `reports/sample_HER2_offline.html`; live/online HER2 sample reports are included at `reports/sample_HER2.md` and `reports/sample_HER2.html`.

To generate the report in English, pass `--language english`:

```powershell
python -m research_intel --target HER2 --offline --format both --language english
```

To run against live public APIs:

```powershell
python -m research_intel --target "PD-L1" --format both
```

The same language option works with live API runs:

```powershell
python -m research_intel --target "PD-L1" --format both --language english
```

Optional PubMed email/tool identification can be configured with environment variables:

```powershell
$env:PUBMED_EMAIL="your.email@example.com"
$env:PUBMED_TOOL="research-intel-prototype"
```

To use LLM-generated analysis in the four main report sections, configure an OpenAI-compatible chat API key:

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

DashScope's OpenAI-compatible endpoint is also supported:

```powershell
$env:DASHSCOPE_API_KEY="your-dashscope-api-key"
$env:RESEARCH_INTEL_LLM_MODEL="qwen-plus"
$env:RESEARCH_INTEL_LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

Optional LLM settings:

```powershell
$env:RESEARCH_INTEL_LLM_MODEL="gpt-4o-mini"
$env:RESEARCH_INTEL_LLM_ENDPOINT="https://api.openai.com/v1"
```

No API keys are hard-coded. If the LLM key is not configured or the LLM call fails, the report falls back to deterministic local summaries.

## Tests

```powershell
python -m unittest discover -s tests
```

You can also use the installed console command:

```powershell
research-intel --target HER2 --offline --format markdown
```

Useful CLI options:

- `--target HER2` sets the target or biomarker to research.
- `--offline` uses built-in demo records only; it does not call public APIs or the LLM.
- `--format markdown|html|both` controls output file type.
- `--language chinese|english` controls report language. The default is `chinese`.
- `--verbose` enables debug logging.

## Adding Data Sources

New collectors should follow the existing `DataSource` interface in `research_intel/sources/base.py`.

1. Create a new module under `research_intel/sources/`.
2. Implement a class with a `name` and a `fetch(target: str) -> SourceResult` method.
3. Convert source-specific API responses into the normalized models in `research_intel/models.py`, usually `TrialRecord` or `PublicationRecord`.
4. Return a `SourceResult` with records, warnings, and cache status.
5. Add the new source to the live `sources` list in `IntelligencePipeline.from_settings()`.

The current pipeline automatically deduplicates and renders `TrialRecord` and `PublicationRecord`. For new data categories such as approvals, patents, conference abstracts, or company pipeline pages, either map them into the closest existing record type for a quick prototype or add a new model type and update the pipeline and report renderer.

## Project Layout

```text
.
  .gitignore         Git ignore rules for local/runtime artifacts
  pyproject.toml     Package metadata and console script definition
  requirements.txt   Runtime dependency list for pip installs
  README.md          Main English quick-start documentation
  README_detailed.md Detailed English documentation
  README_zh.md       Chinese documentation
  written_test.md    Original project requirements
research_intel/
  __init__.py        Package marker
  __main__.py        CLI entrypoint
  app.py             Pipeline orchestration
  cache.py           SQLite cache and report versions
  config.py          Settings loaded from environment
  http.py            Resilient stdlib HTTP client
  llm.py             Optional LLM report analyzer
  models.py          Normalized dataclasses
  report.py          Markdown/HTML report renderer
  sources/           Pluggable collectors
    base.py              DataSource interface
    clinical_trials.py   ClinicalTrials.gov collector
    offline.py           Built-in demo fixture source
    pubmed.py            PubMed collector
docs/
  architecture.md       System design document
  architecture_zh.md    Chinese system design document
reports/
  sample_HER2.md        Example Markdown report generated from live/online sources
  sample_HER2.html      Example HTML report generated from live/online sources
  sample_HER2_offline.md / .html  Example reports generated from offline fixtures
  *.md / *.html         Generated report outputs
  *.sqlite3*            Local cache/report metadata databases
tests/
  test_pipeline.py      Offline pipeline and report tests
```
