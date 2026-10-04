from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from gaxbench.study1_query_trace_evidence import is_safe_pattern, is_safe_reason

_ALLOWED_ROW_KEYS = frozenset(
    {
        "schema_version",
        "role",
        "question_id_sha256",
        "tool_call_count",
        "normalized_patterns",
        "status",
        "reason_codes",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost",
    }
)
_ALLOWED_ROLES = frozenset({"calibration", "validation"})
_ALLOWED_STATUSES = frozenset({"pass", "behavior-changing-blocker"})
_EXPECTED_CALIBRATION_ROWS = 341
_EXPECTED_VALIDATION_ROWS = 1122
_EXPECTED_DEVELOPMENT_ROWS = 1463
_EXPECTED_FINAL_ROWS = 173
_EXPECTED_SHARDS = 8
_EXPECTED_MEMBERSHIP_SHA256 = (
    "b90e774067d0a0e4251e32584b3aeea9629a01df9201fc550988e70d17dbda15"
)
_EXPECTED_SOURCE_SHA256 = (
    "e2045692fef7f5f4f77496935160f5fc727e162d213e94feed61401948e512a0"
)


def aggregate(input_dir: Path, output_path: Path, receipt_path: Path) -> dict[str, Any]:
    row_files = sorted(input_dir.rglob("shard-*-rows.jsonl"))
    audit_files = sorted(input_dir.rglob("shard-*-audit.json"))
    if len(row_files) != _EXPECTED_SHARDS or len(audit_files) != _EXPECTED_SHARDS:
        raise ValueError("query-trace shard artifact count is incomplete")

    audits = [_load_json(path) for path in audit_files]
    shard_indices = {audit.get("shard_index") for audit in audits}
    if shard_indices != set(range(_EXPECTED_SHARDS)):
        raise ValueError("query-trace shard index coverage is incomplete")

    selected_audit_rows = 0
    for audit in audits:
        if audit.get("shard_count") != _EXPECTED_SHARDS:
            raise ValueError("query-trace shard count drift")
        if audit.get("source_sha256") != _EXPECTED_SOURCE_SHA256:
            raise ValueError("query-trace source SHA-256 drift")
        if audit.get("membership_sha256") != _EXPECTED_MEMBERSHIP_SHA256:
            raise ValueError("query-trace membership SHA-256 drift")
        if audit.get("calibration_rows") != _EXPECTED_CALIBRATION_ROWS:
            raise ValueError("query-trace calibration denominator drift")
        if audit.get("validation_rows") != _EXPECTED_VALIDATION_ROWS:
            raise ValueError("query-trace validation denominator drift")
        if audit.get("sealed_final_rows") != _EXPECTED_FINAL_ROWS:
            raise ValueError("query-trace sealed-final denominator drift")
        if audit.get("final_rows_materialized") != 0:
            raise ValueError("sealed-final row materialization detected")
        if audit.get("final_question_content_accessed") is not False:
            raise ValueError("sealed-final question access detected")
        if audit.get("raw_questions_emitted") is not False:
            raise ValueError("raw question emission detected")
        if audit.get("raw_patient_ids_emitted") is not False:
            raise ValueError("raw patient identifier emission detected")
        if audit.get("raw_query_values_emitted") is not False:
            raise ValueError("raw FHIR query value emission detected")
        if audit.get("raw_traces_emitted") is not False:
            raise ValueError("raw trace emission detected")
        if audit.get("answer_correctness_scored") is not False:
            raise ValueError("answer correctness scoring detected")
        if audit.get("second_turn_reasoning_executed") is not False:
            raise ValueError("second-turn benchmark reasoning detected")
        selected_audit_rows += _nonnegative_int(audit.get("selected_rows"))

    rows: list[dict[str, Any]] = []
    for path in row_files:
        raw_payload = path.read_bytes()
        expected_digest = next(
            (
                str(audit["rows_sha256"])
                for audit in audits
                if path.name == f"shard-{audit['shard_index']}-rows.jsonl"
            ),
            None,
        )
        if expected_digest is None:
            raise ValueError(f"missing audit for {path.name}")
        if hashlib.sha256(raw_payload).hexdigest() != expected_digest:
            raise ValueError(f"row artifact SHA-256 mismatch for {path.name}")
        for line_number, line in enumerate(raw_payload.decode("utf-8").splitlines(), start=1):
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict) or set(value) != _ALLOWED_ROW_KEYS:
                raise ValueError(f"row artifact field drift at {path.name}:{line_number}")
            rows.append(value)

    if len(rows) != _EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError("query-trace development denominator is incomplete")
    if selected_audit_rows != _EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError("query-trace audit denominator is incomplete")

    question_ids = [str(row["question_id_sha256"]) for row in rows]
    if len(set(question_ids)) != _EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError("query-trace question hashes must be unique")
    if any(len(value) != 64 or not _is_hex(value) for value in question_ids):
        raise ValueError("query-trace question hash format drift")

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    total_tool_calls = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cost = 0.0

    for row in rows:
        role = row["role"]
        status = row["status"]
        if role not in _ALLOWED_ROLES:
            raise ValueError("non-development role escaped query-trace gate")
        if status not in _ALLOWED_STATUSES:
            raise ValueError("query-trace row status drift")
        patterns = row["normalized_patterns"]
        reasons = row["reason_codes"]
        if not isinstance(patterns, list) or any(not isinstance(v, str) for v in patterns):
            raise ValueError("normalized_patterns must be strings")
        if not isinstance(reasons, list) or any(not isinstance(v, str) for v in reasons):
            raise ValueError("reason_codes must be strings")
        if any(not _is_normalized_pattern(pattern) for pattern in patterns):
            raise ValueError("non-normalized query pattern escaped artifact firewall")
        if any(not is_safe_reason(reason) for reason in reasons):
            raise ValueError("non-normalized reason escaped artifact firewall")
        if status == "pass" and reasons:
            raise ValueError("pass row retained blocker reasons")
        if status == "behavior-changing-blocker" and not reasons:
            raise ValueError("blocked row omitted reason codes")

        role_counts[role] += 1
        status_counts[status] += 1
        pattern_counts.update(patterns)
        reason_counts.update(reasons)
        total_tool_calls += _nonnegative_int(row["tool_call_count"])
        total_prompt_tokens += _nonnegative_int(row["prompt_tokens"])
        total_completion_tokens += _nonnegative_int(row["completion_tokens"])
        total_tokens += _nonnegative_int(row["total_tokens"])
        total_cost += _nonnegative_float(row["cost"])

    if role_counts["calibration"] != _EXPECTED_CALIBRATION_ROWS:
        raise ValueError("query-trace calibration row accounting is incomplete")
    if role_counts["validation"] != _EXPECTED_VALIDATION_ROWS:
        raise ValueError("query-trace validation row accounting is incomplete")

    blocker_rows = status_counts["behavior-changing-blocker"]
    gate_result = "pass" if blocker_rows == 0 else "blocked-behavior-changing"
    canonical_main_sha = os.environ.get("GITHUB_SHA", "")
    if len(canonical_main_sha) != 40 or not _is_hex(canonical_main_sha):
        raise ValueError("GITHUB_SHA is not a full commit SHA")

    report: dict[str, Any] = {
        "schema_version": "0.1",
        "study_id": "study1",
        "specgrain_id": "SG-000028",
        "stage": "post-D3-pre-D4",
        "canonical_main_sha": canonical_main_sha,
        "query_trace_gate_result": gate_result,
        "calibration_rows": role_counts["calibration"],
        "validation_rows": role_counts["validation"],
        "development_rows": len(rows),
        "sealed_final_rows": _EXPECTED_FINAL_ROWS,
        "unique_question_hashes": len(set(question_ids)),
        "total_tool_calls": total_tool_calls,
        "status_counts": dict(sorted(status_counts.items())),
        "normalized_pattern_counts": dict(sorted(pattern_counts.items())),
        "blocker_reason_counts": dict(sorted(reason_counts.items())),
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": total_cost,
        "membership_sha256": _EXPECTED_MEMBERSHIP_SHA256,
        "source_sha256": _EXPECTED_SOURCE_SHA256,
        "final_rows_materialized": 0,
        "final_question_content_accessed": False,
        "raw_questions_emitted": False,
        "raw_patient_ids_emitted": False,
        "raw_query_values_emitted": False,
        "raw_traces_emitted": False,
        "answer_correctness_scored": False,
        "second_turn_reasoning_executed": False,
        "training_performed": False,
        "d7_model_selection_performed": False,
        "sg000028_closeout_allowed": gate_result == "pass",
        "d4_activation_allowed": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
    receipt = {
        "schema_version": "0.1",
        "study_id": "study1",
        "specgrain_id": "SG-000028",
        "canonical_main_sha": canonical_main_sha,
        "query_trace_report_sha256": report_sha256,
        "query_trace_gate_result": gate_result,
        "shard_count": _EXPECTED_SHARDS,
        "zero_founder_cost": True,
        "sealed_final_role_accessed": False,
        "training_performed": False,
        "d4_activation_allowed": False,
    }
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _is_hex(value: str) -> bool:
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_normalized_pattern(pattern: str) -> bool:
    return is_safe_pattern(pattern)


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("expected non-negative integer accounting value")
    return value


def _nonnegative_float(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError("expected non-negative numeric accounting value")
    return float(value)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    return parser.parse_args()


def main() -> None:
    args = _args()
    report = aggregate(
        Path(args.input_dir),
        Path(args.output),
        Path(args.receipt),
    )
    print(
        json.dumps(
            {
                "query_trace_gate_result": report["query_trace_gate_result"],
                "development_rows": report["development_rows"],
                "total_tool_calls": report["total_tool_calls"],
                "status_counts": report["status_counts"],
                "blocker_reason_counts": report["blocker_reason_counts"],
                "sealed_final_rows": report["sealed_final_rows"],
                "d4_activation_allowed": report["d4_activation_allowed"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
