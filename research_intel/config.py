from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    cache_path: Path
    reports_dir: Path
    timeout_seconds: int
    cache_ttl_hours: int
    pubmed_email: str
    pubmed_tool: str
    max_trials: int
    max_publications: int
    llm_api_key: str
    llm_endpoint: str
    llm_model: str
    llm_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
        llm_api_key = os.getenv("RESEARCH_INTEL_LLM_API_KEY") or dashscope_key or os.getenv("OPENAI_API_KEY", "")
        default_llm_endpoint = (
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
            if dashscope_key and not os.getenv("OPENAI_API_KEY")
            else "https://api.openai.com/v1"
        )
        default_llm_model = "qwen-plus" if dashscope_key and not os.getenv("OPENAI_API_KEY") else "gpt-4o-mini"
        return cls(
            cache_path=Path(os.getenv("RESEARCH_INTEL_CACHE", ".cache/research_intel.sqlite3")),
            reports_dir=Path(os.getenv("RESEARCH_INTEL_REPORTS", "reports")),
            timeout_seconds=int(os.getenv("RESEARCH_INTEL_TIMEOUT", "20")),
            cache_ttl_hours=int(os.getenv("RESEARCH_INTEL_CACHE_TTL_HOURS", "24")),
            pubmed_email=os.getenv("PUBMED_EMAIL", ""),
            pubmed_tool=os.getenv("PUBMED_TOOL", "research-intel-prototype"),
            max_trials=int(os.getenv("RESEARCH_INTEL_MAX_TRIALS", "25")),
            max_publications=int(os.getenv("RESEARCH_INTEL_MAX_PUBLICATIONS", "25")),
            llm_api_key=llm_api_key,
            llm_endpoint=os.getenv("RESEARCH_INTEL_LLM_ENDPOINT", default_llm_endpoint),
            llm_model=os.getenv("RESEARCH_INTEL_LLM_MODEL", default_llm_model),
            llm_timeout_seconds=int(os.getenv("RESEARCH_INTEL_LLM_TIMEOUT", "60")),
        )
