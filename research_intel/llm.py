from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from research_intel.models import IntelligenceBundle


class LLMReportAnalyzer:
    """Generate report section analysis with an OpenAI-compatible chat API."""

    required_keys = {
        "target_overview",
        "pipeline_overview",
        "research_dynamics",
        "competitive_assessment",
    }

    def __init__(
        self,
        api_key: str = "",
        endpoint: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 60,
    ):
        self.api_key = api_key
        self.base_url = self._normalize_base_url(endpoint)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def analyze(self, bundle: IntelligenceBundle, language: str) -> Optional[Dict[str, str]]:
        if not self.enabled:
            return None

        prompt = self._build_prompt(bundle, language)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a biomedical competitive intelligence analyst. "
                        "Use only the provided structured records. Do not invent trial IDs, products, sponsors, "
                        "publication facts, or regulatory conclusions. Return valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        try:
            completion = self._create_chat_completion(payload)
            content = completion.choices[0].message.content
            parsed = json.loads(content)
        except Exception as exc:
            self.logger.warning("LLM report analysis failed; deterministic fallback will be used: %s", exc)
            return None

        if not isinstance(parsed, dict) or not self.required_keys.issubset(parsed):
            self.logger.warning("LLM report analysis returned an unexpected shape; deterministic fallback will be used")
            return None
        return {key: str(parsed[key]).strip() for key in self.required_keys}

    def _create_chat_completion(self, payload: Dict[str, Any]) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("Install the openai package to enable LLM analysis") from exc

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )
        return client.chat.completions.create(**payload)

    def _normalize_base_url(self, endpoint: str) -> str:
        endpoint = (endpoint or "https://api.openai.com/v1").rstrip("/")
        parsed = urlparse(endpoint)
        if parsed.path.endswith("/chat/completions"):
            return endpoint[: -len("/chat/completions")]
        return endpoint

    def _build_prompt(self, bundle: IntelligenceBundle, language: str) -> str:
        output_language = "Chinese" if language == "chinese" else "English"
        section_names = (
            "靶点概述, 在研管线概览, 近期研究动态, 竞争格局判断"
            if language == "chinese"
            else "Target Overview, Pipeline Overview, Recent Research Dynamics, Competitive Landscape Assessment"
        )
        data = {
            "target": bundle.target,
            "trials": [trial.to_dict() for trial in bundle.trials[:25]],
            "publications": [pub.to_dict() for pub in bundle.publications[:25]],
            "warnings": bundle.warnings,
        }
        return (
            f"Analyze the collected biomedical competitive intelligence data and write concise report content in {output_language}.\n"
            f"The final report has these four sections: {section_names}.\n"
            "Return a JSON object with exactly these keys:\n"
            "- target_overview: basic target information and mechanism of action, grounded in the provided data and known high-level biology.\n"
            "- pipeline_overview: development-stage distribution, main competitors, and their products/interventions.\n"
            "- research_dynamics: summary and interpretation of recent key publication findings.\n"
            "- competitive_assessment: current competitive landscape, potential risks, and opportunities.\n"
            "Keep each value report-ready. Use bullet points only when they improve readability. Preserve source-specific uncertainty.\n\n"
            f"Structured input data:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        )
