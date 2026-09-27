from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.fhir_agentbench_qualification import (
    probe_frozen_source,
    qualify_frozen_source,
    report_exposes_sensitive_content,
)
from gaxbench.schema import StrictModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe or qualify the frozen FHIR-AgentBench CSV with metadata-only evidence."
    )
    parser.add_argument("source", type=Path, help="Path to the frozen upstream CSV")
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument("--output", type=Path, help="Write only the metadata source probe JSON")
    outputs.add_argument(
        "--output-dir",
        type=Path,
        help="Write source probe, role manifest, leakage audit, and qualification report",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.output is not None:
        report = probe_frozen_source(args.source)
        _require_metadata_only(report)
        _write_json(args.output, report)
        _print_compact(report)
        return 0

    output_dir: Path = args.output_dir
    probe, manifest, audit, report = qualify_frozen_source(args.source)
    for artifact in (probe, manifest, audit, report):
        _require_metadata_only(artifact)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "source_probe.json", probe)
    _write_json(output_dir / "role_manifest.json", manifest)
    _write_json(output_dir / "leakage_audit.json", audit)
    _write_json(output_dir / "qualification.json", report)
    _print_compact(report)
    return 0 if report.status == "qualified" else 2


def _require_metadata_only(value: StrictModel) -> None:
    if report_exposes_sensitive_content(value):
        raise ValueError("FHIR-AgentBench qualification artifact exposes sensitive/raw content")


def _write_json(path: Path, value: StrictModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def _print_compact(value: StrictModel) -> None:
    print(
        json.dumps(
            value.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
