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


if __name__ == "__main__":
    unittest.main()
