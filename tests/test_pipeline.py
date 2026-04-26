import tempfile
import unittest
from pathlib import Path

from research_intel.app import IntelligencePipeline
from research_intel.config import Settings
from research_intel.report import ReportRenderer
from research_intel.sources.offline import OfflineDemoSource


class FakeAnalyzer:
    def analyze(self, bundle, language):
        return {
            "target_overview": "LLM target overview for HER2 mechanism.",
            "pipeline_overview": "LLM pipeline overview with competitors and products.",
            "research_dynamics": "LLM research dynamics summary and interpretation.",
            "competitive_assessment": "LLM competitive assessment with risks and opportunities.",
        }


class MarkdownAnalyzer:
    def analyze(self, bundle, language):
        return {
            "target_overview": "**HER2** overview with [source](https://example.com).",
            "pipeline_overview": "- **Company A**: ADC program\n- Company B: antibody program",
            "research_dynamics": "1. `Study one` signal\n2. Study two signal",
            "competitive_assessment": "### Assessment\n- Risk: public records can lag.",
        }


class PipelineTests(unittest.TestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            cache_path=root / "cache.sqlite3",
            reports_dir=root / "reports",
            timeout_seconds=1,
            cache_ttl_hours=24,
            pubmed_email="",
            pubmed_tool="test",
            max_trials=10,
            max_publications=10,
            llm_api_key="",
            llm_endpoint="https://api.openai.com/v1/chat/completions",
            llm_model="test-model",
            llm_timeout_seconds=1,
        )

    def test_offline_pipeline_generates_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            pipeline = IntelligencePipeline(settings, [OfflineDemoSource()])
            result = pipeline.run("HER2", "both")
            self.assertEqual(len(result.bundle.trials), 3)
            self.assertEqual(len(result.bundle.publications), 2)
            self.assertEqual(len(result.report_paths), 2)
            for path in result.report_paths:
                self.assertTrue(path.exists())

    def test_report_contains_required_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            pipeline = IntelligencePipeline(settings, [OfflineDemoSource()])
            bundle = pipeline.run("HER2", "markdown").bundle
            markdown = ReportRenderer().render_markdown(bundle)
            self.assertIn("靶点概述", markdown)
            self.assertIn("在研管线概览", markdown)
            self.assertIn("近期研究动态", markdown)
            self.assertIn("竞争格局判断", markdown)
            self.assertIn("主要竞争企业", markdown)
            self.assertIn("<svg", markdown)

    def test_report_uses_llm_analysis_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            pipeline = IntelligencePipeline(settings, [OfflineDemoSource()], FakeAnalyzer())
            result = pipeline.run("HER2", "markdown", "english")
            markdown = result.report_paths[0].read_text(encoding="utf-8")
            self.assertIn("LLM target overview for HER2 mechanism.", markdown)
            self.assertIn("LLM pipeline overview with competitors and products.", markdown)
            self.assertIn("LLM research dynamics summary and interpretation.", markdown)
            self.assertIn("LLM competitive assessment with risks and opportunities.", markdown)
            self.assertEqual(result.bundle.metadata["analysis_source"], "llm")

    def test_report_can_render_english_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            pipeline = IntelligencePipeline(settings, [OfflineDemoSource()])
            bundle = pipeline.run("HER2", "markdown", "english").bundle
            markdown = ReportRenderer().render_markdown(bundle, "english")
            self.assertIn("Target Overview", markdown)
            self.assertIn("Pipeline Overview", markdown)
            self.assertIn("Recent Research Dynamics", markdown)
            self.assertIn("Competitive Landscape Assessment", markdown)

    def test_from_settings_offline_mode_does_not_use_llm(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            settings = Settings(
                cache_path=settings.cache_path,
                reports_dir=settings.reports_dir,
                timeout_seconds=settings.timeout_seconds,
                cache_ttl_hours=settings.cache_ttl_hours,
                pubmed_email=settings.pubmed_email,
                pubmed_tool=settings.pubmed_tool,
                max_trials=settings.max_trials,
                max_publications=settings.max_publications,
                llm_api_key="configured-key",
                llm_endpoint=settings.llm_endpoint,
                llm_model=settings.llm_model,
                llm_timeout_seconds=settings.llm_timeout_seconds,
            )
            pipeline = IntelligencePipeline.from_settings(settings, offline=True)
            result = pipeline.run("HER2", "markdown", "english")
            self.assertIsNone(pipeline.analyzer)
            self.assertNotIn("analysis_source", result.bundle.metadata)
            self.assertNotIn("llm_analysis", result.bundle.metadata)

    def test_html_converts_markdown_from_llm_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            pipeline = IntelligencePipeline(settings, [OfflineDemoSource()], MarkdownAnalyzer())
            result = pipeline.run("HER2", "html", "english")
            html = result.report_paths[0].read_text(encoding="utf-8")
            self.assertIn("<strong>HER2</strong>", html)
            self.assertIn('<a href="https://example.com">source</a>', html)
            self.assertIn("<ul>", html)
            self.assertIn("<li><strong>Company A</strong>: ADC program</li>", html)
            self.assertIn("<ol>", html)
            self.assertIn("<code>Study one</code>", html)
            self.assertIn("<h3>Assessment</h3>", html)
            self.assertNotIn("<p>- **Company A**: ADC program</p>", html)


if __name__ == "__main__":
    unittest.main()
