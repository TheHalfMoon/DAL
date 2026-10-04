from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "registry/study1_sg000028_execution_37156028113.json"


def _builder():
    spec = importlib.util.spec_from_file_location(
        "sg28_persistence", ROOT / "tools/persist_sg000028_evidence.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_names_cannot_escape_safe_persistence() -> None:
    builder = _builder()
    for name in ("patient-private-id", "date>'2099-12-31'", "free form content", "gt;42.5"):
        pattern = f"search:Observation?{name}=<empty>&patient=<patient-id>"
        reason = f"unsupported-parameter:{name}"
        assert builder.safe_pattern(pattern).startswith("opaque-pattern-sha256:")
        assert builder.safe_reason(reason).startswith("opaque-reason-sha256:")
        assert name not in builder.safe_pattern(pattern)
        assert name not in builder.safe_reason(reason)
    assert builder.safe_reason("unsupported-parameter:date") == "unsupported-parameter:date"


def test_complete_negative_result_retains_all_shards_and_firewall() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    assert evidence["workflow_run_id"] == 37156028113
    assert evidence["canonical_main_sha"] == "f8f5c1c8ebfbe2e044ad9beae55e56b94f1f449d"
    assert evidence["original_aggregate_recomputed_exactly"] is True
    assert evidence["all_nine_zip_digests_verified"] is True
    assert evidence["calibration_rows"] == 341
    assert evidence["validation_rows"] == 1122
    assert evidence["development_rows"] == evidence["unique_question_hashes"] == 1463
    assert evidence["status_counts"] == {"pass": 224, "behavior-changing-blocker": 1239}
    assert evidence["scientific_gate_status"] == "BLOCKED"
    assert evidence["normalized_unique_pattern_count"] == 248
    assert len(evidence["pattern_support_evidence"]) == 248
    assert evidence["total_tool_calls"] == 1623
    shards = evidence["shards"]
    assert {s["shard_index"] for s in shards} == set(range(8))
    assert sum(s["selected_rows"] for s in shards) == 1463
    assert sum(s["status_counts"]["pass"] for s in shards) == 224
    for shard in shards:
        assert shard["raw_benchmark_source_cleanup_step"] == "success"
        assert shard["final_rows_materialized"] == 0
        assert shard["final_question_content_accessed"] is False
    for field in (
        "d4_activation_allowed",
        "sg000028_closeout_allowed",
        "training_performed",
        "model_selection_performed",
        "answer_correctness_scored",
        "second_turn_reasoning_executed",
        "final_question_content_accessed",
    ):
        assert evidence[field] is False
    assert evidence["cost_usd"] == 0
    assert evidence["final_rows_materialized"] == 0


def test_pattern_receipts_retain_identities_without_overclaiming_call_support() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    builder = _builder()
    receipts = evidence["pattern_support_evidence"]
    assert len({r["source_pattern_sha256"] for r in receipts}) == 248
    assert sum(r["occurrences"] for r in receipts) == 1623
    for receipt in receipts:
        pattern = receipt["safe_pattern"]
        assert (
            pattern.startswith("opaque-pattern-sha256:") or builder.safe_pattern(pattern) == pattern
        )
        assert receipt["call_level_support_attribution_available"] is False
        assert receipt["occurrences"] == sum(receipt["row_status_associations"].values())
        if receipt["row_status_associations"].get("behavior-changing-blocker", 0):
            assert receipt["support_status"] == "blocked-row-associated-not-qualified"
    firewall = evidence["artifact_firewall"]
    assert firewall["legacy_source_masking_assertions_verified"] is False
    assert firewall["source_literal_keys_republished"] is False
    assert firewall["opaque_pattern_count"] == 39
    assert firewall["opaque_reason_count"] == 34
