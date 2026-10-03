from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT = ROOT / "registry/study1_sg000027_closeout.json"
FRONTIER = ROOT / "registry/study1_sg000027_frontier_status.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_d3_exit_criteria_are_proven() -> None:
    closeout = _load(CLOSEOUT)
    assert closeout["stage"] == "D3"
    criteria = closeout["d3_exit_criteria"]
    assert [item["id"] for item in criteria] == [f"D3-E{i}" for i in range(1, 9)]
    assert all(item["status"] == "proven" for item in criteria)


def test_closeout_binds_canonical_freeze_and_post_main() -> None:
    closeout = _load(CLOSEOUT)
    inputs = closeout["canonical_inputs"]
    assert inputs["freeze_merge"] == "01c28e582e7d3399581078b306a32369ab12a79c"
    assert inputs["freeze_post_main_gaxbench_run"] == 37144865657
    assert inputs["freeze_post_main_manuscript_run"] == 37144865687
    frozen = closeout["frozen_trace_producer_summary"]
    assert frozen["base_model"].startswith("Qwen/Qwen3-4B-Instruct-2507@")
    assert frozen["d7_model_selection"] is False


def test_query_trace_gate_is_preserved_and_not_activated_by_closeout() -> None:
    closeout = _load(CLOSEOUT)
    gate = closeout["mandatory_next_gate"]
    assert gate["authorization_issue"] == 126
    assert gate["stage_order_authorization_issue"] == 128
    assert gate["roles"] == ["calibration", "validation"]
    assert gate["d4_blocked_until_pass"] is True
    assert gate["activated_by_this_closeout"] is False
    assert set(gate["invalid_substitutes"]) == {
        "SQL proc_query", "expected resource IDs", "static source inspection", "invented traces"
    }


def test_final_role_remains_sealed_and_d4_inactive() -> None:
    closeout = _load(CLOSEOUT)
    sealed = closeout["sealed_final_boundary"]
    assert sealed["test_patient_count"] == 40
    assert sealed["test_row_count"] == 173
    assert sealed["test_gold_serialized"] is False
    assert sealed["accessed_in_D3"] is False
    frontier = _load(FRONTIER)
    assert frontier["state"] == "d3-closed-query-trace-gate-not-yet-activated"
    assert frontier["d3_closed"] is True
    assert frontier["d4_activation_allowed"] is False
    assert frontier["training_allowed"] is False
    assert frontier["final_role_accessed"] is False
    assert frontier["next_governed_action"] == (
        "activate-post-D3-pre-D4-query-trace-qualification-grain"
    )
