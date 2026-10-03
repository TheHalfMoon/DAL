from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "registry/study1_sg000027_trace_producer_freeze.json"
FRONTIER = ROOT / "registry/study1_sg000027_frontier_status.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_trace_producer_identity_is_exact_and_not_d7_selection() -> None:
    freeze = _load(FREEZE)
    identity = freeze["trace_producer_identity"]
    assert freeze["stage"] == "D3"
    assert freeze["freeze_basis"]["d7_model_selection_performed"] is False
    assert identity["base_model_repo"] == "Qwen/Qwen3-4B-Instruct-2507"
    assert identity["base_model_revision"] == "cdbee75f17c01a7cc42f958dc650907174af0554"
    assert identity["tokenizer_revision"] == identity["base_model_revision"]
    assert identity["quantized_runtime_artifact"]["sha256"] == (
        "ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1"
    )
    assert identity["fhir_agentbench"]["agent_strategy"] == "single_turn_request"


def test_freeze_depends_on_repaired_synthetic_transport_only() -> None:
    freeze = _load(FREEZE)
    evidence = freeze["synthetic_qualification"]
    assert evidence["run"] == 37143422780
    assert evidence["smoke_status"] == "pass"
    assert evidence["transport_status"] == "transport-compatible"
    assert evidence["tool_name"] == "fhir_request_get"
    assert evidence["query_string"] == "Patient/DAL-SMOKE-0001"
    assert evidence["benchmark_development_or_final_data_accessed"] is False
    assert freeze["freeze_basis"]["training_performed"] is False


def test_bounded_family_negative_evidence_is_retained() -> None:
    freeze = _load(FREEZE)
    disposition = {item["candidate_id"]: item for item in freeze["bounded_family_disposition"]}
    assert disposition["phi4-mini-instruct"]["disposition"].startswith("retained-negative")
    assert disposition["smollm3-3b"]["disposition"].startswith("retained-negative")
    assert disposition["qwen3-4b-instruct-2507"]["disposition"] == (
        "prospectively-frozen-trace-producer"
    )


def test_d4_stays_blocked_until_post_d3_query_trace_gate() -> None:
    freeze = _load(FREEZE)
    inv = freeze["governance_invariants"]
    assert inv["trace_producing_system_frozen"] is True
    assert inv["d7_model_selection_performed"] is False
    assert inv["development_query_trace_gate_executed"] is False
    assert inv["final_role_accessed"] is False
    assert inv["d4_allowed"] is False
    assert freeze["next_gate"]["name"] == "canonical-D3-closeout"


def test_frontier_allows_only_d3_closeout_next() -> None:
    frontier = _load(FRONTIER)
    assert frontier["state"] == "d3-closed-query-trace-gate-not-yet-activated"
    assert frontier["trace_producing_system_frozen"] is True
    assert frontier["base_model_frozen"] is True
    assert frontier["tokenizer_frozen"] is True
    assert frontier["d7_model_selection_performed"] is False
    assert frontier["d4_activation_allowed"] is False
    assert frontier["training_allowed"] is False
    assert frontier["final_role_accessed"] is False
    assert frontier["next_governed_action"] == (
        "activate-post-D3-pre-D4-query-trace-qualification-grain"
    )
