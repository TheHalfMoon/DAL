from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from gaxbench.study1_query_trace_gate import (
    build_development_trace_inputs,
    exercise_observed_query,
    load_verified_gate_runtime,
)

_ALLOWED_REASON_CODES = frozenset(
    {
        "llm-call-error",
        "no-response",
        "no-tool-call",
        "unexpected-tool-name",
        "malformed-tool-arguments",
        "missing-query-string",
        "query-exercise-exception",
    }
)


def run_shard(
    *,
    source: Path,
    upstream_root: Path,
    runtime_root: Path,
    runtime_manifest: Path,
    output_dir: Path,
    model: str,
    base_url: str,
    shard_index: int,
    shard_count: int,
) -> dict[str, Any]:
    inputs, audit, development_patient_digests = build_development_trace_inputs(
        source,
        shard_index=shard_index,
        shard_count=shard_count,
    )
    runtime = load_verified_gate_runtime(
        runtime_root,
        runtime_manifest,
        development_patient_digests=development_patient_digests,
    )

    sys.path.insert(0, str(upstream_root))
    try:
        from agent.single_turn_request_agent import SingleTurnRequestAgent
        from utils import safe_llm_call
    finally:
        if sys.path and sys.path[0] == str(upstream_root):
            sys.path.pop(0)

    agent = SingleTurnRequestAgent(model=model, verbose=False, base_url=base_url)
    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()

    for item in inputs:
        messages = list(agent.system_msg)
        messages.append({"role": "user", "content": item.input_text})
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
            captured_stderr
        ):
            response, error, usage = safe_llm_call(
                model=model,
                messages=messages,
                tools=agent.tools,
                base_url=base_url,
            )

        reasons: list[str] = []
        patterns: list[str] = []
        calls = list(getattr(response, "tool_calls", None) or []) if response else []
        if error is not None:
            reasons.append("llm-call-error")
        if response is None:
            reasons.append("no-response")
        if not calls:
            reasons.append("no-tool-call")

        for call in calls:
            function = getattr(call, "function", None)
            tool_name = getattr(function, "name", None)
            if tool_name != "fhir_request_get":
                reasons.append("unexpected-tool-name")
                continue
            raw_arguments = getattr(function, "arguments", None)
            if not isinstance(raw_arguments, str):
                reasons.append("malformed-tool-arguments")
                continue
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                reasons.append("malformed-tool-arguments")
                continue
            if not isinstance(arguments, dict):
                reasons.append("malformed-tool-arguments")
                continue
            query_string = arguments.get("query_string")
            if not isinstance(query_string, str) or not query_string:
                reasons.append("missing-query-string")
                continue
            try:
                exercise = exercise_observed_query(
                    query_string,
                    role=item.role,
                    runtime=runtime,
                )
            except (TypeError, ValueError):
                reasons.append("query-exercise-exception")
                continue
            patterns.append(exercise.pattern)
            reasons.extend(exercise.reason_codes)

        reasons = sorted(set(reasons))
        patterns = sorted(patterns)
        row_status = "pass" if not reasons and calls else "behavior-changing-blocker"
        status_counts[row_status] += 1
        reason_counts.update(reasons)
        usage_map = usage if isinstance(usage, dict) else {}
        rows.append(
            {
                "schema_version": "0.1",
                "role": item.role,
                "question_id_sha256": item.question_id_sha256,
                "tool_call_count": len(calls),
                "normalized_patterns": patterns,
                "status": row_status,
                "reason_codes": reasons,
                "prompt_tokens": _safe_nonnegative_int(usage_map.get("prompt_tokens")),
                "completion_tokens": _safe_nonnegative_int(
                    usage_map.get("completion_tokens")
                ),
                "total_tokens": _safe_nonnegative_int(usage_map.get("total_tokens")),
                "cost": _safe_nonnegative_float(usage_map.get("cost")),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / f"shard-{shard_index}-rows.jsonl"
    payload = b"".join(
        (
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        for row in rows
    )
    rows_path.write_bytes(payload)

    audit_payload = audit.model_dump(mode="json")
    audit_payload.update(
        {
            "rows_sha256": hashlib.sha256(payload).hexdigest(),
            "status_counts": dict(sorted(status_counts.items())),
            "reason_counts": dict(sorted(reason_counts.items())),
            "raw_query_values_emitted": False,
            "raw_traces_emitted": False,
            "answer_correctness_scored": False,
            "second_turn_reasoning_executed": False,
        }
    )
    audit_path = output_dir / f"shard-{shard_index}-audit.json"
    audit_path.write_text(
        json.dumps(audit_payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return audit_payload


def _safe_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _safe_nonnegative_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return 0.0


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--upstream-root", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--shard-index", required=True, type=int)
    parser.add_argument("--shard-count", required=True, type=int)
    return parser.parse_args()


def main() -> None:
    args = _args()
    audit = run_shard(
        source=Path(args.source),
        upstream_root=Path(args.upstream_root),
        runtime_root=Path(args.runtime_root),
        runtime_manifest=Path(args.runtime_manifest),
        output_dir=Path(args.output_dir),
        model=args.model,
        base_url=args.base_url,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
    )
    print(
        json.dumps(
            {
                "shard_index": audit["shard_index"],
                "selected_rows": audit["selected_rows"],
                "status_counts": audit["status_counts"],
                "reason_counts": audit["reason_counts"],
                "final_rows_materialized": audit["final_rows_materialized"],
                "final_question_content_accessed": audit[
                    "final_question_content_accessed"
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
