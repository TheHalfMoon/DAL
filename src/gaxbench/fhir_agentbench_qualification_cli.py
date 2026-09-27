from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.fhir_agentbench_qualification import (
    probe_frozen_source,
    report_exposes_sensitive_content,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe the frozen FHIR-AgentBench CSV and emit metadata-only evidence."
    )
    parser.add_argument("source", type=Path, help="Path to the frozen upstream CSV")
    parser.add_argument("--output", type=Path, required=True, help="Metadata-only JSON output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = probe_frozen_source(args.source)
    if report_exposes_sensitive_content(report):
        raise ValueError("FHIR-AgentBench qualification report exposes sensitive/raw content")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    args.output.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
