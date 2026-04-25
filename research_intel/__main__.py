from __future__ import annotations

import argparse
import logging
import sys

from research_intel.app import IntelligencePipeline
from research_intel.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate biomedical competitive intelligence reports.")
    parser.add_argument("--target", required=True, help="Target or biomarker name, for example HER2 or PD-L1.")
    parser.add_argument(
        "--format",
        choices=["markdown", "html", "both"],
        default="markdown",
        help="Report output format.",
    )
    parser.add_argument(
        "--language",
        choices=["chinese", "english"],
        default="chinese",
        help="Report language. Defaults to Chinese; use english to generate the report in English.",
    )
    parser.add_argument("--offline", action="store_true", help="Use built-in demo fixtures instead of public APIs.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    try:
        pipeline = IntelligencePipeline.from_settings(Settings.from_env(), offline=args.offline)
        result = pipeline.run(args.target, args.format, args.language)
    except Exception as exc:
        logging.exception("Report generation failed")
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(result.report_paths)} report file(s) for {result.bundle.target}:")
    for path in result.report_paths:
        print(f"- {path}")
    if result.bundle.warnings:
        print("Warnings:")
        for warning in result.bundle.warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
