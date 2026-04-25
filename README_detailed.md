# Research Intelligence Prototype

Chinese documentation is available in [README_zh.md](README_zh.md).

This project is a small Python application that helps answer a practical question:

> "If our company is interested in a disease target or biomarker, what are other researchers and companies already doing around it?"

In medicine, a **target** is usually a gene, protein, mutation, or biological signal that a drug may act on. For example, **HER2** is a protein involved in some breast, stomach, and other cancers. Companies often need to know which drugs, clinical trials, and scientific papers already exist for a target before deciding whether to invest in a new research program.

This prototype automates part of that research work. A user types a target name, such as `HER2`, and the program searches public databases, organizes the results, and creates an easy-to-read report. Reports are generated in Chinese by default, and English can be requested with a command-line option.

## What The Project Does

The program collects and summarizes three kinds of information:

- **Clinical trials**: Human studies testing drugs or treatments. The app can search ClinicalTrials.gov and extract trial title, sponsor/company, study phase, status, number of patients, treatment names, countries, and registry ID.
- **Scientific papers**: Published research articles. The app can search PubMed and extract article title, journal, date, authors, and PubMed link.
- **Simple competitive view**: A short analysis showing which companies appear active, how mature the trial pipeline is, and what opportunities or risks may exist.

The output is a report in `Markdown` and/or `HTML`, so it can be opened in a text editor, browser, or converted to PDF later.

## Who This Is For

This prototype is designed for:

- Research strategy teams who need a quick first scan of a biomedical topic.
- Medical or scientific affairs teams who want a structured summary instead of manually copying database results.
- Evaluators or graders who want to see a complete working prototype with data collection, caching, reporting, tests, and documentation.

You do not need medical training to run it. The included offline example uses HER2 and produces a sample report from built-in demo records.

## Plain-English Glossary

- **Target**: A biological thing researchers care about, such as a protein or mutation. Example: HER2.
- **Biomarker**: A measurable biological sign that helps identify a disease type or likely treatment response.
- **Clinical trial**: A study in people to test whether a treatment is safe or effective.
- **Trial phase**: A rough measure of how mature a treatment is. Phase 1 is early safety testing; Phase 2 looks for activity; Phase 3 is larger and closer to possible approval.
- **Sponsor**: The company, hospital, university, or organization responsible for a study.
- **PubMed**: A public database of biomedical research papers.
- **ClinicalTrials.gov**: A public registry of clinical studies.
- **Pipeline**: The set of drugs or studies currently being developed for a target or disease.

## Features

- Searches public biomedical sources: ClinicalTrials.gov and PubMed.
- Includes an offline HER2 demo so the project can be tested without internet access.
- Produces readable Markdown and HTML reports.
- Uses Chinese as the default report language, with an English option when requested.
- Uses an optional LLM analysis layer to summarize the collected data into the four main report sections.
- Adds simple charts for trial phases and publication years.
- Stores cached results so repeated searches do less work.
- Keeps report version history metadata.
- Handles network/API errors gracefully.
- Avoids hard-coded API keys or private credentials.
- Uses a pluggable source design, so future sources like FDA approvals, patents, or conference abstracts can be added without rewriting the whole app.

## Quick Start

Create a fresh virtual environment from the project root. The commands below install the app and its runtime dependencies, including the OpenAI Python SDK used for optional LLM analysis.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks activation scripts, use the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Generate a demo report using built-in HER2 data:

```powershell
python -m research_intel --target HER2 --offline --format both
```

This generates Chinese reports by default. To generate English reports instead:

```powershell
python -m research_intel --target HER2 --offline --format both --language english
```

Generated files are written to `reports/`. You should see files with names similar to:

```text
reports/HER2_YYYYMMDD_HHMMSS.md
reports/HER2_YYYYMMDD_HHMMSS.html
```

Open the `.html` file in a browser or the `.md` file in an editor.

To run against live public APIs:

```powershell
python -m research_intel --target "PD-L1" --format both
```

To request English for live API runs:

```powershell
python -m research_intel --target "PD-L1" --format both --language english
```

Optional PubMed email/tool identification can be configured with environment variables:

```powershell
$env:PUBMED_EMAIL="your.email@example.com"
$env:PUBMED_TOOL="research-intel-prototype"
```

To use LLM-generated analysis in the report, configure an OpenAI-compatible chat API key:

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

## Example

Command:

```powershell
python -m research_intel --target HER2 --offline --format markdown
```

Meaning:

- `--target HER2` tells the app what biological topic to research.
- `--offline` uses built-in demo data, which is useful for grading or testing without internet.
- `--format markdown` creates a Markdown report.
- `--language chinese` or `--language english` controls report language. If omitted, the report is generated in Chinese.

The included sample output is here:

```text
reports/sample_HER2.md
```

## How To Read The Report

Each generated report has these sections:

- **执行摘要 / Executive Summary**: A short overview of what the scan found.
- **靶点概览 / Target Overview**: A plain description of the target being researched.
- **管线格局 / Pipeline Landscape**: A table of clinical trials and a chart showing trial phases.
- **近期研究动态 / Recent Research Dynamics**: A table of recent papers and a chart showing publication timing.
- **竞争态势评估 / Competitive Assessment**: A short interpretation of active development, late-stage pressure, opportunities, and risks.
- **数据来源说明 / Source Notes**: Warnings, cache notes, or data-source issues.

The report is not a medical recommendation. It is a research-assistant output meant to help an analyst start faster.

## Tests

```powershell
python -m unittest discover -s tests
```

You can also use the installed console command:

```powershell
research-intel --target HER2 --offline --format markdown
```

Add `--language english` to either command form when an English report is needed.

## Project Layout

```text
research_intel/
  __main__.py        CLI entrypoint
  app.py             Pipeline orchestration
  cache.py           SQLite cache and report versions
  config.py          Settings loaded from environment
  http.py            Resilient stdlib HTTP client
  llm.py             Optional LLM report analyzer
  models.py          Normalized dataclasses
  report.py          Markdown/HTML report renderer
  sources/           Pluggable collectors
docs/
  architecture.md    System design document
reports/
  sample_HER2.md     Example report generated from offline fixtures
tests/
```

## Current Limitations

- The offline demo data is simplified and exists to prove the full workflow runs.
- Live public databases may return different results over time.
- LLM output depends on API availability and model behavior; important conclusions should be reviewed by qualified experts.
- Public sources may not include paid database records, confidential company strategy, or very recent conference updates.
- Any important business or medical decision should be reviewed by qualified experts.
