from __future__ import annotations

import html
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from research_intel.models import IntelligenceBundle, PublicationRecord, TrialRecord


class ReportRenderer:
    def render_markdown(self, bundle: IntelligenceBundle, language: str = "chinese") -> str:
        language = self._normalize_language(language)
        if language == "english":
            return self._render_markdown_english(bundle)
        return self._render_markdown_chinese(bundle)

    def _render_markdown_english(self, bundle: IntelligenceBundle) -> str:
        lines = [
            f"# {bundle.target} Competitive Intelligence Report",
            "",
            f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Target Overview",
            "",
            self._section_text(bundle, "target_overview", self._target_overview(bundle.target)),
            "",
            "## Pipeline Overview",
            "",
            self._section_text(bundle, "pipeline_overview", self._pipeline_overview(bundle)),
            "",
            self._phase_chart_markdown(bundle.trials),
            "",
            self._sponsor_product_table(bundle.trials),
            "",
            self._trial_table(bundle.trials),
            "",
            "## Recent Research Dynamics",
            "",
            self._section_text(bundle, "research_dynamics", self._research_dynamics(bundle.publications)),
            "",
            self._publication_chart_markdown(bundle.publications),
            "",
            self._publication_table(bundle.publications),
            "",
            "## Competitive Landscape Assessment",
            "",
            self._section_text(bundle, "competitive_assessment", self._competitive_assessment(bundle)),
            "",
            "## Source Notes",
            "",
            self._source_notes(bundle),
        ]
        return "\n".join(lines).strip() + "\n"

    def _render_markdown_chinese(self, bundle: IntelligenceBundle) -> str:
        lines = [
            f"# {bundle.target} 竞争情报报告",
            "",
            f"生成时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## 靶点概述",
            "",
            self._section_text(bundle, "target_overview", self._target_overview_chinese(bundle.target)),
            "",
            "## 在研管线概览",
            "",
            self._section_text(bundle, "pipeline_overview", self._pipeline_overview_chinese(bundle)),
            "",
            self._phase_chart_markdown(bundle.trials, "在研项目阶段分布"),
            "",
            self._sponsor_product_table_chinese(bundle.trials),
            "",
            self._trial_table_chinese(bundle.trials),
            "",
            "## 近期研究动态",
            "",
            self._section_text(bundle, "research_dynamics", self._research_dynamics_chinese(bundle.publications)),
            "",
            self._publication_chart_markdown(bundle.publications, "文献发表趋势"),
            "",
            self._publication_table_chinese(bundle.publications),
            "",
            "## 竞争格局判断",
            "",
            self._section_text(bundle, "competitive_assessment", self._competitive_assessment_chinese(bundle)),
            "",
            "## 数据来源说明",
            "",
            self._source_notes_chinese(bundle),
        ]
        return "\n".join(lines).strip() + "\n"

    def render_html(self, markdown: str, title: str, language: str = "chinese") -> str:
        body = self._markdown_to_html(markdown)
        html_lang = "en" if self._normalize_language(language) == "english" else "zh-CN"
        return f"""<!doctype html>
<html lang="{html_lang}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 40px; color: #17202a; line-height: 1.55; }}
    h1, h2 {{ color: #143d59; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 8px; vertical-align: top; }}
    th {{ background: #edf4f8; text-align: left; }}
    code {{ background: #f3f5f7; padding: 2px 4px; border-radius: 3px; }}
    svg {{ max-width: 760px; width: 100%; height: auto; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

    def write(
        self,
        bundle: IntelligenceBundle,
        reports_dir: Path,
        format_name: str,
        language: str = "chinese",
    ) -> List[Path]:
        reports_dir.mkdir(parents=True, exist_ok=True)
        safe_target = "".join(ch if ch.isalnum() else "_" for ch in bundle.target).strip("_")
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        language = self._normalize_language(language)
        markdown = self.render_markdown(bundle, language)
        paths: List[Path] = []
        if format_name in {"markdown", "both"}:
            md_path = reports_dir / f"{safe_target}_{stamp}.md"
            md_path.write_text(markdown, encoding="utf-8")
            paths.append(md_path)
        if format_name in {"html", "both"}:
            html_path = reports_dir / f"{safe_target}_{stamp}.html"
            title = f"{bundle.target} report" if language == "english" else f"{bundle.target} 报告"
            html_path.write_text(self.render_html(markdown, title, language), encoding="utf-8")
            paths.append(html_path)
        return paths

    def _target_overview(self, target: str) -> str:
        mechanism = self._known_mechanism_english(target)
        return (
            f"{target} is treated as the user-specified biological target or biomarker. {mechanism} "
            "The analysis combines clinical development signals and recent literature metadata to summarize "
            "mechanism relevance, pipeline maturity, research direction, and competitive risk."
        )

    def _target_overview_chinese(self, target: str) -> str:
        mechanism = self._known_mechanism_chinese(target)
        return (
            f"{target} 是用户指定的生物靶点或生物标志物。{mechanism}"
            "本报告基于采集到的临床试验与文献元数据进行分析归纳，重点判断作用机制相关性、管线成熟度、"
            "近期研究方向以及潜在竞争风险。"
        )

    def _pipeline_overview(self, bundle: IntelligenceBundle) -> str:
        phase_text = self._phase_text(bundle.trials)
        sponsors = Counter(trial.sponsor for trial in bundle.trials if trial.sponsor).most_common(3)
        sponsor_text = ", ".join(name for name, _ in sponsors) or "no clear leading sponsors"
        product_count = len({item for trial in bundle.trials for item in trial.interventions if item})
        return (
            f"The collected set contains {len(bundle.trials)} trial records across {phase_text}. "
            f"The main visible competitors are {sponsor_text}. Across the records, {product_count} distinct "
            "intervention or product names appear, which helps identify active modalities and combination strategies."
        )

    def _pipeline_overview_chinese(self, bundle: IntelligenceBundle) -> str:
        phase_text = self._phase_text_chinese(bundle.trials)
        sponsors = Counter(trial.sponsor for trial in bundle.trials if trial.sponsor).most_common(3)
        sponsor_text = "、".join(name for name, _ in sponsors) or "暂无明确领先企业"
        product_count = len({item for trial in bundle.trials for item in trial.interventions if item})
        return (
            f"本次采集到 {len(bundle.trials)} 条临床试验记录，研发阶段分布为：{phase_text}。"
            f"主要可见竞争企业包括 {sponsor_text}。记录中共出现 {product_count} 个不同干预措施或产品名称，"
            "可用于判断活跃技术路线、联合用药策略和适应症扩展方向。"
        )

    def _research_dynamics(self, publications: List[PublicationRecord]) -> str:
        if not publications:
            return "No publication records were available for research interpretation."
        recent = publications[:3]
        signals = []
        for pub in recent:
            signal = pub.abstract or ", ".join(pub.keywords) or pub.title
            signals.append(f"- {self._cell(pub.title)}: {self._cell(signal[:220])}")
        return "\n".join(
            ["Recent literature signals from the collected records:"]
            + signals
            + ["Interpretation: these topics should be reviewed for mechanism validation, biomarker segmentation, and changes in treatment positioning."]
        )

    def _research_dynamics_chinese(self, publications: List[PublicationRecord]) -> str:
        if not publications:
            return "暂无可用于研究解读的文献记录。"
        recent = publications[:3]
        signals = []
        for pub in recent:
            signal = pub.abstract or "；".join(pub.keywords) or pub.title
            signals.append(f"- {self._cell(pub.title)}：{self._cell(signal[:220])}")
        return "\n".join(
            ["近期关键文献信号如下："]
            + signals
            + ["解读：上述主题应重点用于验证作用机制、识别生物标志物分层机会，并观察治疗定位或临床策略是否发生变化。"]
        )

    def _trial_table(self, trials: List[TrialRecord]) -> str:
        if not trials:
            return "No clinical trial records were available."
        rows = [
            "| NCT ID | Title | Sponsor | Phase | Status | Enrollment | Interventions | Countries |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- |",
        ]
        for trial in trials:
            rows.append(
                "| "
                + " | ".join(
                    [
                        self._link(trial.nct_id, trial.url),
                        self._cell(trial.title),
                        self._cell(trial.sponsor),
                        self._cell(trial.phase),
                        self._cell(trial.status),
                        str(trial.enrollment or ""),
                        self._cell(", ".join(trial.interventions[:4])),
                        self._cell(", ".join(trial.countries[:5])),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    def _trial_table_chinese(self, trials: List[TrialRecord]) -> str:
        if not trials:
            return "暂无可用临床试验记录。"
        rows = [
            "| NCT ID | 标题 | 申办方 | 阶段 | 状态 | 入组人数 | 干预措施/产品 | 国家/地区 |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- |",
        ]
        for trial in trials:
            rows.append(
                "| "
                + " | ".join(
                    [
                        self._link(trial.nct_id, trial.url),
                        self._cell(trial.title),
                        self._cell(trial.sponsor),
                        self._cell(trial.phase),
                        self._cell(trial.status),
                        str(trial.enrollment or ""),
                        self._cell(", ".join(trial.interventions[:4])),
                        self._cell(", ".join(trial.countries[:5])),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    def _sponsor_product_table(self, trials: List[TrialRecord]) -> str:
        if not trials:
            return "No sponsor/product records were available."
        grouped: Dict[str, List[str]] = defaultdict(list)
        for trial in trials:
            sponsor = trial.sponsor or "Unknown"
            products = trial.interventions or ["Unspecified intervention"]
            for product in products:
                if product and product not in grouped[sponsor]:
                    grouped[sponsor].append(product)
        rows = [
            "| Sponsor / Company | Products or interventions | Trial count |",
            "| --- | --- | ---: |",
        ]
        sponsor_counts = Counter(trial.sponsor or "Unknown" for trial in trials)
        for sponsor, count in sponsor_counts.most_common():
            rows.append(f"| {self._cell(sponsor)} | {self._cell(', '.join(grouped[sponsor][:6]))} | {count} |")
        return "\n".join(rows)

    def _sponsor_product_table_chinese(self, trials: List[TrialRecord]) -> str:
        if not trials:
            return "暂无可用企业和产品记录。"
        grouped: Dict[str, List[str]] = defaultdict(list)
        for trial in trials:
            sponsor = trial.sponsor or "Unknown"
            products = trial.interventions or ["未注明干预措施"]
            for product in products:
                if product and product not in grouped[sponsor]:
                    grouped[sponsor].append(product)
        rows = [
            "| 主要竞争企业/机构 | 产品或干预措施 | 相关试验数 |",
            "| --- | --- | ---: |",
        ]
        sponsor_counts = Counter(trial.sponsor or "Unknown" for trial in trials)
        for sponsor, count in sponsor_counts.most_common():
            rows.append(f"| {self._cell(sponsor)} | {self._cell(', '.join(grouped[sponsor][:6]))} | {count} |")
        return "\n".join(rows)

    def _publication_table(self, publications: List[PublicationRecord]) -> str:
        if not publications:
            return "No publication records were available."
        rows = [
            "| PMID | Title | Journal | Date | Authors | Key signal |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for pub in publications:
            rows.append(
                "| "
                + " | ".join(
                    [
                        self._link(pub.pmid, pub.url),
                        self._cell(pub.title),
                        self._cell(pub.journal),
                        self._cell(pub.publication_date),
                        self._cell(", ".join(pub.authors[:4])),
                        self._cell(pub.abstract[:180] or ", ".join(pub.keywords[:5])),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    def _publication_table_chinese(self, publications: List[PublicationRecord]) -> str:
        if not publications:
            return "暂无可用文献记录。"
        rows = [
            "| PMID | 标题 | 期刊 | 日期 | 作者 | 关键信号 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for pub in publications:
            rows.append(
                "| "
                + " | ".join(
                    [
                        self._link(pub.pmid, pub.url),
                        self._cell(pub.title),
                        self._cell(pub.journal),
                        self._cell(pub.publication_date),
                        self._cell(", ".join(pub.authors[:4])),
                        self._cell(pub.abstract[:180] or ", ".join(pub.keywords[:5])),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    def _competitive_assessment(self, bundle: IntelligenceBundle) -> str:
        active = [trial for trial in bundle.trials if "RECRUIT" in trial.status.upper() or "ACTIVE" in trial.status.upper()]
        late = [trial for trial in bundle.trials if "3" in trial.phase or "PHASE3" in trial.phase.upper()]
        sponsors = Counter(trial.sponsor for trial in bundle.trials if trial.sponsor)
        concentration = sponsors.most_common(1)[0][0] if sponsors else "no single sponsor"
        return (
            f"- Current competition: {len(bundle.trials)} collected trials suggest visible activity led by {concentration}.\n"
            f"- Maturity: {len(late)} phase 3-like records and {len(active)} active/recruiting records indicate the near-term pressure level.\n"
            "- Opportunities: monitor differentiated modalities, combinations, biomarker segmentation, and tumor-type expansion.\n"
            "- Risks: public-source records can lag sponsor strategy; pivotal studies, regulatory status, and unpublished conference data require analyst validation."
        )

    def _competitive_assessment_chinese(self, bundle: IntelligenceBundle) -> str:
        active = [trial for trial in bundle.trials if "RECRUIT" in trial.status.upper() or "ACTIVE" in trial.status.upper()]
        late = [trial for trial in bundle.trials if "3" in trial.phase or "PHASE3" in trial.phase.upper()]
        sponsors = Counter(trial.sponsor for trial in bundle.trials if trial.sponsor)
        concentration = sponsors.most_common(1)[0][0] if sponsors else "暂无单一领先企业"
        return (
            f"- 当前竞争态势：采集到 {len(bundle.trials)} 条临床试验记录，显示该方向已有明确研发活动，代表性参与方为 {concentration}。\n"
            f"- 管线成熟度：其中 {len(late)} 条记录接近或属于 3 期阶段，{len(active)} 条记录处于活跃或招募状态，提示需关注近期读出、注册路径或适应症扩展。\n"
            "- 潜在机会：可重点比较差异化技术路线、联合用药方案、生物标志物分层、地域布局和新瘤种扩展。\n"
            "- 主要风险：公开数据库可能滞后于企业真实策略，关键注册研究、监管状态、会议摘要和未公开数据仍需人工复核。"
        )

    def _source_notes(self, bundle: IntelligenceBundle) -> str:
        warnings = bundle.warnings or ["No collector warnings."]
        cache_note = ", ".join(bundle.metadata.get("cache_sources", [])) or "No cached source hits reported."
        analysis_source = "LLM analysis" if bundle.metadata.get("analysis_source") == "llm" else "deterministic fallback analysis"
        return "\n".join(
            [f"- {self._cell(warning)}" for warning in warnings]
            + [f"- Cache: {cache_note}", f"- Analysis source: {analysis_source}"]
        )

    def _source_notes_chinese(self, bundle: IntelligenceBundle) -> str:
        warnings = bundle.warnings or ["采集器未报告警告。"]
        cache_note = ", ".join(bundle.metadata.get("cache_sources", [])) or "未命中缓存来源。"
        analysis_source = "LLM 分析" if bundle.metadata.get("analysis_source") == "llm" else "规则化回退分析"
        return "\n".join(
            [f"- {self._cell(warning)}" for warning in warnings]
            + [f"- 缓存：{cache_note}", f"- 分析来源：{analysis_source}"]
        )

    def _phase_chart_markdown(self, trials: Iterable[TrialRecord], title: str = "Trial phase distribution") -> str:
        counts = Counter(trial.phase or "Unknown" for trial in trials)
        return self._bar_svg(counts, title)

    def _publication_chart_markdown(self, publications: Iterable[PublicationRecord], title: str = "Publication trend") -> str:
        counts: Dict[str, int] = Counter((pub.publication_date[:4] or "Unknown") for pub in publications)
        return self._bar_svg(counts, title)

    def _bar_svg(self, counts: Dict[str, int], title: str) -> str:
        if not counts:
            return f"_{title}: no data._"
        labels = list(counts.keys())[:8]
        max_count = max(counts.values()) or 1
        width = 720
        row_height = 30
        height = 50 + row_height * len(labels)
        lines = [f'<svg role="img" aria-label="{html.escape(title)}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
        lines.append(f'<text x="0" y="20" font-size="16" font-family="Arial">{html.escape(title)}</text>')
        for i, label in enumerate(labels):
            y = 42 + i * row_height
            bar_width = int((counts[label] / max_count) * 480)
            lines.append(f'<text x="0" y="{y + 15}" font-size="12" font-family="Arial">{html.escape(label)}</text>')
            lines.append(f'<rect x="150" y="{y}" width="{bar_width}" height="18" fill="#2f7f95" />')
            lines.append(f'<text x="{160 + bar_width}" y="{y + 15}" font-size="12" font-family="Arial">{counts[label]}</text>')
        lines.append("</svg>")
        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        lines = markdown.splitlines()
        html_lines: List[str] = []
        in_table = False
        for line in lines:
            if line.startswith("<svg") or line.startswith("<text") or line.startswith("<rect") or line == "</svg>":
                html_lines.append(line)
            elif line.startswith("# "):
                html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("| ") and line.endswith(" |"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if all(set(cell) <= {"-", ":", " "} for cell in cells):
                    continue
                tag = "th" if not in_table else "td"
                if not in_table:
                    html_lines.append("<table>")
                    in_table = True
                html_lines.append("<tr>" + "".join(f"<{tag}>{self._markdown_links(cell)}</{tag}>" for cell in cells) + "</tr>")
            else:
                if in_table:
                    html_lines.append("</table>")
                    in_table = False
                if line.startswith("- "):
                    html_lines.append(f"<p>{html.escape(line)}</p>")
                elif line:
                    html_lines.append(f"<p>{self._markdown_links(line)}</p>")
        if in_table:
            html_lines.append("</table>")
        return "\n".join(html_lines)

    def _markdown_links(self, text: str) -> str:
        if text.startswith("[") and "](" in text and text.endswith(")"):
            label, url = text[1:].split("](", 1)
            return f'<a href="{html.escape(url[:-1])}">{html.escape(label)}</a>'
        return html.escape(text)

    def _link(self, label: str, url: str) -> str:
        if not url:
            return self._cell(label)
        return f"[{self._cell(label)}]({url})"

    def _cell(self, value: str) -> str:
        return str(value).replace("|", "/").replace("\n", " ").strip()

    def _section_text(self, bundle: IntelligenceBundle, key: str, fallback: str) -> str:
        analysis = bundle.metadata.get("llm_analysis")
        if isinstance(analysis, dict) and analysis.get(key):
            return str(analysis[key]).strip()
        return fallback

    def _phase_text(self, trials: List[TrialRecord]) -> str:
        counts = Counter(trial.phase or "Unknown" for trial in trials)
        return ", ".join(f"{phase}: {count}" for phase, count in counts.items()) or "unknown phases"

    def _phase_text_chinese(self, trials: List[TrialRecord]) -> str:
        counts = Counter(trial.phase or "未知阶段" for trial in trials)
        return "、".join(f"{phase} {count} 项" for phase, count in counts.items()) or "未知阶段"

    def _known_mechanism_english(self, target: str) -> str:
        normalized = target.upper().replace("-", "")
        if normalized in {"HER2", "ERBB2"}:
            return "HER2/ERBB2 is a receptor tyrosine kinase in the EGFR family; amplification or overexpression can drive tumor growth and is targetable with antibodies, ADCs, and kinase inhibitors."
        if normalized in {"PDL1", "CD274"}:
            return "PD-L1/CD274 is an immune checkpoint ligand that suppresses T-cell activity through PD-1 binding; blockade can restore anti-tumor immune responses."
        if normalized.startswith("KRAS"):
            return "KRAS is a small GTPase in the RAS/MAPK pathway; oncogenic mutations can maintain proliferative signaling and create mutation-specific drug opportunities."
        return "Mechanism details are inferred from collected public records; analyst review should add curated biology and pathway context for this target."

    def _known_mechanism_chinese(self, target: str) -> str:
        normalized = target.upper().replace("-", "")
        if normalized in {"HER2", "ERBB2"}:
            return "HER2/ERBB2 属于 EGFR 家族受体酪氨酸激酶，扩增或过表达可驱动肿瘤生长，常见干预方式包括抗体、抗体偶联药物和小分子激酶抑制剂。"
        if normalized in {"PDL1", "CD274"}:
            return "PD-L1/CD274 是免疫检查点配体，可通过结合 PD-1 抑制 T 细胞活性；阻断该通路有助于恢复抗肿瘤免疫反应。"
        if normalized.startswith("KRAS"):
            return "KRAS 是 RAS/MAPK 通路中的小 GTP 酶，致癌突变可维持增殖信号，并形成突变特异性的药物开发机会。"
        return "当前作用机制主要依据采集到的公开记录进行归纳，后续仍建议补充人工整理的靶点生物学和通路背景。"

    def _normalize_language(self, language: str) -> str:
        value = (language or "chinese").strip().lower()
        aliases = {
            "cn": "chinese",
            "zh": "chinese",
            "zh-cn": "chinese",
            "中文": "chinese",
            "chinese": "chinese",
            "en": "english",
            "英文": "english",
            "english": "english",
        }
        if value not in aliases:
            raise ValueError("language must be chinese or english")
        return aliases[value]
