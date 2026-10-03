from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "registry" / "study1_sg000027_candidate_inventory.json"
FRONTIER = ROOT / "registry" / "study1_sg000027_frontier_status.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_family_is_bounded_without_selecting_a_model() -> None:
    inv = _load(INVENTORY)
    candidates = inv["bounded_base_model_family"]
    assert [c["candidate_id"] for c in candidates] == [
        "phi4-mini-instruct",
        "qwen3-4b-instruct-2507",
        "smollm3-3b",
    ]
    assert all(c["parameter_count"] <= 4_100_000_000 for c in candidates)
    assert all(c["gated"] is False for c in candidates)
    assert {c["license"] for c in candidates} <= {"MIT", "Apache-2.0"}
    assert all(c["not_selected"] is True for c in candidates)
    assert inv["selection_performed"] is False
    assert inv["development_benchmark_outcomes_used"] is False


def test_contamination_proxy_is_applied_before_any_development_outcome() -> None:
    inv = _load(INVENTORY)
    boundary = inv["benchmark_public_boundary"]
    assert boundary["repository_created_at"] == "2025-09-12T05:06:56Z"
    assert boundary["earliest_verified_commit"] == "9467654e233af708f343c5f5cc786be76866d498"
    excluded = {c["candidate_id"]: c for c in inv["retained_negative_or_excluded_candidates"]}
    assert "qwen3.5-4b" in excluded
    reasons = " ".join(excluded["qwen3.5-4b"]["reason_excluded_from_bounded_family"])
    assert "contamination risk" in reasons


def test_agent_strategy_is_frozen_but_trace_producer_is_not() -> None:
    inv = _load(INVENTORY)
    strategy = inv["fhir_agent_strategy_family"]
    freeze = inv["freeze_state"]
    frontier = _load(FRONTIER)
    assert strategy["frozen_strategy"] == "single_turn_request"
    assert strategy["revision"] == "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    assert strategy["performance_outcomes_used"] is False
    assert freeze["fhir_agent_strategy_frozen"] is True
    assert freeze["base_model_frozen"] is False
    assert freeze["tokenizer_frozen"] is False
    assert freeze["trace_producing_system_frozen"] is False
    assert freeze["post_d3_pre_d4_query_trace_gate_may_run"] is False
    assert frontier["trace_producing_system_frozen"] is False
    assert frontier["query_trace_gate_status"] == (
        "blocked-until-trace-producer-identity-is-frozen"
    )


def test_assurance_candidates_are_structural_only_and_d4_remains_blocked() -> None:
    inv = _load(INVENTORY)
    family = inv["assurance_architecture_family"]
    assert [c["id"] for c in family["candidates"]] == ["dal-linear-v0", "dal-mlp32-v0"]
    assert all(c["trainable_before_D4"] is False for c in family["candidates"] )
    assert inv["training_performed"] is False
    assert inv["final_role_accessed"] is False
    assert inv["freeze_state"]["d4_allowed"] is False


def test_excluded_candidates_remain_visible_as_negative_evidence() -> None:
    inv = _load(INVENTORY)
    excluded = {c["candidate_id"] for c in inv["retained_negative_or_excluded_candidates"]}
    assert excluded == {"qwen3.5-4b", "gemma-3-4b-it", "llama-3.2-3b-instruct"}
