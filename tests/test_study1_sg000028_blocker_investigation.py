from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_investigation_covers_all_canonical_blocker_reasons() -> None:
    evidence = json.loads(
        (ROOT / "registry/study1_sg000028_execution_37156028113.json").read_text()
    )
    investigation = json.loads(
        (ROOT / "registry/study1_sg000028_blocker_investigation.json").read_text()
    )
    receipts = investigation["reason_investigation"]
    assert investigation["development_rows_investigated"] == 1463
    assert investigation["blocked_rows_retained"] == 1239
    assert investigation["all_observed_reason_keys_classified"] is True
    assert investigation["unique_reason_keys"] == len(receipts) == 106
    assert {r["safe_reason"]: r["affected_row_occurrences"] for r in receipts} == (
        evidence["blocker_reason_counts"]
    )
    assert investigation["immutable_malformed_or_invalid_modifier_row_count"] == 102
    assert investigation["blocker_class_row_counts"]["malformed-fhir-search-parameter-name"] == 61
    assert (
        investigation["blocker_class_row_counts"]["comparison-prefix-used-as-search-modifier"] == 41
    )
    assert investigation["missing_tool_call_rows_with_inference_error"] == 2
    assert investigation["malformed_name_rows_with_empty_parameter"] == 24
    assert investigation["empty_parameter_semantic_repair_candidate"] is True
    assert all(r["governed_action"] and r["certainty"] for r in receipts)


def test_governance_record_never_activates_a_replacement_experiment() -> None:
    investigation = json.loads(
        (ROOT / "registry/study1_sg000028_blocker_investigation.json").read_text()
    )
    gate = investigation["governance_gate"]
    assert gate["state"] == "BLOCKED_REQUIRES_FOUNDER_DECISION"
    assert gate["authorization_received"] is False
    assert {option["id"] for option in gate["options"]} == {"A", "B"}
    for key in (
        "final_role_content_accessed",
        "producer_changed",
        "gate_criteria_changed",
        "d4_activation_allowed",
        "training_performed",
        "answer_correctness_scored",
        "model_selection_performed",
    ):
        assert investigation[key] is False
