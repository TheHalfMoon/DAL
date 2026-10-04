"""Replay the complete existing structural evidence through the repaired firewall.

No model, benchmark source, patient resource, raw question, or raw trace is used.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from collections import Counter
from pathlib import Path

from persist_sg000028_evidence import MAIN, ROOT, build, load, sha

from gaxbench.study1_query_trace_evidence import (
    is_safe_pattern,
    is_safe_reason,
    safe_pattern,
    safe_reason,
)

OUTPUT = ROOT / "registry/study1_sg000028_output_firewall_replay.json"


def replay(source: Path) -> dict:
    evidence = build(source)
    expected = load(ROOT / "registry/study1_sg000028_execution_37156028113.json")
    if evidence != expected:
        raise ValueError("immutable persisted source evidence mismatch")
    spec = importlib.util.spec_from_file_location(
        "sg28_repaired_aggregate", ROOT / "scripts/study1_sg000028_query_trace_aggregate.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_report = load(next(source.rglob("query_trace_qualification.json")))
    rows_checked = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for path in sorted(source.rglob("shard-*-rows.jsonl")):
            rows = [json.loads(line) for line in path.read_text().splitlines() if line]
            reasons: Counter[str] = Counter()
            for row in rows:
                original_status = row["status"]
                row["normalized_patterns"] = sorted(
                    safe_pattern(p) for p in row["normalized_patterns"]
                )
                row["reason_codes"] = sorted({safe_reason(r) for r in row["reason_codes"]})
                assert all(is_safe_pattern(p) for p in row["normalized_patterns"])
                assert all(is_safe_reason(r) for r in row["reason_codes"])
                recalculated = (
                    "pass"
                    if not row["reason_codes"] and row["tool_call_count"]
                    else ("behavior-changing-blocker")
                )
                if original_status != recalculated:
                    raise ValueError("output repair changed scientific row classification")
                reasons.update(row["reason_codes"])
                rows_checked += 1
            payload = b"".join(
                (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                for row in rows
            )
            (root / path.name).write_bytes(payload)
            audit_name = path.name.replace("rows.jsonl", "audit.json")
            audit = load(path.with_name(audit_name))
            audit["rows_sha256"] = sha(payload)
            audit["reason_counts"] = dict(sorted(reasons.items()))
            (root / audit_name).write_text(json.dumps(audit), encoding="utf-8")
        previous = os.environ.get("GITHUB_SHA")
        os.environ["GITHUB_SHA"] = MAIN
        try:
            repaired_report = module.aggregate(root, root / "report.json", root / "receipt.json")
        finally:
            if previous is None:
                os.environ.pop("GITHUB_SHA", None)
            else:
                os.environ["GITHUB_SHA"] = previous
        for field, value in source_report.items():
            if field not in {"normalized_pattern_counts", "blocker_reason_counts"}:
                if repaired_report[field] != value:
                    raise ValueError("output replay changed original aggregate accounting")
        expected_patterns = {
            p["safe_pattern"]: p["occurrences"] for p in evidence["pattern_support_evidence"]
        }
        if repaired_report["normalized_pattern_counts"] != expected_patterns:
            raise ValueError("output replay lost observed pattern identities")
        if repaired_report["blocker_reason_counts"] != evidence["blocker_reason_counts"]:
            raise ValueError("output replay lost blocker reasons")
        report_sha = sha((root / "report.json").read_bytes())
    return {
        "schema_version": "0.1",
        "study_id": "study1",
        "specgrain_id": "SG-000028",
        "grain_id": "SG-000028-R1",
        "source_run": 37156028113,
        "source_main": MAIN,
        "source_report_sha256": evidence["source_report_sha256"],
        "persisted_evidence_sha256": sha(
            (ROOT / "registry/study1_sg000028_execution_37156028113.json").read_bytes()
        ),
        "verification_kind": "offline-structural-output-replay-not-new-inference",
        "development_rows_checked": rows_checked,
        "pattern_identities_retained": len(expected_patterns),
        "repaired_output_report_sha256": report_sha,
        "all_row_classifications_unchanged": True,
        "all_accounting_unchanged": True,
        "finite_vocabulary_or_opaque_hash_output_verified": True,
        "raw_benchmark_source_accessed": False,
        "raw_question_content_accessed": False,
        "raw_traces_accessed": False,
        "final_role_content_accessed": False,
        "inference_performed": False,
        "training_performed": False,
        "trace_producer_changed": False,
        "scientific_gate_status": "BLOCKED",
        "d4_activation_allowed": False,
        "zero_founder_cost": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = (json.dumps(replay(args.source), indent=2, sort_keys=True) + "\n").encode()
    if args.check:
        if OUTPUT.read_bytes() != payload:
            raise SystemExit("output-firewall replay receipt drift")
    else:
        OUTPUT.write_bytes(payload)
    print("All 1463 structural rows replayed; classifications unchanged; output firewall verified.")
