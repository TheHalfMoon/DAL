from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.pubmedqa import qualify_pubmedqa_source


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Qualify the frozen PubMedQA PQA-L source without exposing final-test labels."
    )
    parser.add_argument("source", type=Path, help="Path to frozen data/ori_pqal.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expect-split-manifest-sha256")
    parser.add_argument("--expect-leakage-audit-sha256")
    args = parser.parse_args(argv)

    manifest, audit, report = qualify_pubmedqa_source(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "split_manifest.json", manifest.model_dump(mode="json"))
    _write_json(args.output_dir / "leakage_audit.json", audit.model_dump(mode="json"))
    _write_json(args.output_dir / "qualification.json", report.model_dump(mode="json"))

    print(json.dumps(report.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))

    if (
        args.expect_split_manifest_sha256 is not None
        and report.split_manifest_sha256 != args.expect_split_manifest_sha256
    ):
        print("expected split-manifest digest does not match real qualification output")
        return 2
    if (
        args.expect_leakage_audit_sha256 is not None
        and report.leakage_audit_sha256 != args.expect_leakage_audit_sha256
    ):
        print("expected leakage-audit digest does not match real qualification output")
        return 2
    if report.status != "qualified":
        print("PubMedQA PQA-L qualification is blocked by leakage findings")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
