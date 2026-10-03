from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry" / "study1_sg000027_contract.json"
FRONTIER = ROOT / "registry" / "study1_sg000027_frontier_status.json"
D2_CLOSEOUT = ROOT / "registry" / "study1_sg000026_closeout.json"
PROTOCOL = ROOT / "registry" / "study1_preregistered_protocol_2026-10-02.json"
AMENDMENT = ROOT / "registry" / "study1_sg000026_stage_order_amendment.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _lf_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_d3_activation_binds_canonical_d2_closeout_and_protocol() -> None:
    contract = _load(CONTRACT)
    dep = contract["canonical_dependency"]
    assert contract["grain"] == "SG-000027"
    assert contract["study_stage"] == "D3"
    assert contract["research_contract_issue"] == 132
    assert dep["sg000026_closeout_merge"] == "07ad6a3f0af0f5a460cd469e029b26274f1a7416"
    assert dep["sg000026_closeout_lf_sha256"] == _lf_sha(D2_CLOSEOUT)
    assert dep["post_main_gaxbench_run"] == 37135893667
    assert dep["post_main_manuscript_run"] == 37135893641
    assert dep["protocol_sha256"] == _lf_sha(PROTOCOL)
    assert dep["stage_order_amendment_sha256"] == _lf_sha(AMENDMENT)
    assert dep["stage_order_authorization_comment_id"] == 5970595978


def test_activation_grain_does_not_select_model_or_activate_training() -> None:
    contract = _load(CONTRACT)
    effects = contract["activation_grain_effects"]
    boundary = contract["activation_grain_boundary"]
    assert effects["d3_activated"] is True
    assert effects["candidate_family_defined"] is False
    assert effects["base_model_selected"] is False
    assert effects["tokenizer_selected"] is False
    assert effects["fhir_agent_strategy_selected"] is False
    assert effects["d4_activated"] is False
    assert effects["training_performed"] is False
    assert effects["final_role_accessed"] is False
    assert set(boundary.values()) == {False}


def test_d3_candidate_and_compute_requirements_remain_bounded() -> None:
    contract = _load(CONTRACT)
    requirements = set(contract["candidate_requirements"])
    assert "open-weight or otherwise fully zero-cost locally runnable" in requirements
    assert "exact model and tokenizer revisions can be frozen" in requirements
    assert "release date and known benchmark exposure are recorded" in requirements
    compute = contract["compute_policy"]
    assert compute["default_dense_parameter_envelope"] == "approximately <=4B"
    assert compute["closed_paid_models"] == "ineligible as mandatory Study 1 systems"


def test_post_d3_query_trace_gate_blocks_d4_and_final_remains_sealed() -> None:
    contract = _load(CONTRACT)
    gate = contract["mandatory_post_d3_pre_d4_gate"]
    sealed = contract["sealed_final_firewall"]
    assert gate["status"] == "required-not-yet-executed"
    assert gate["roles"] == ["calibration", "validation"]
    assert gate["d4_blocked_until_pass"] is True
    assert set(gate["invalid_substitutes"]) == {
        "SQL proc_query", "expected resource IDs", "static source inspection", "invented traces"
    }
    assert sealed["test_patients"] == 40
    assert sealed["test_rows"] == 173
    assert sealed["test_gold_serialized"] is False
    assert sealed["access"] == "sealed"
    assert sealed["d3_use"] == "forbidden"


def test_d3_frontier_is_active_but_has_not_frozen_trace_producer() -> None:
    frontier = _load(FRONTIER)
    assert frontier["state"] == "d3-closed-query-trace-gate-not-yet-activated"
    assert frontier["candidate_family_defined"] is True
    assert frontier["fhir_agent_strategy_frozen"] is True
    assert frontier["trace_producing_system_frozen"] is True
    assert frontier["d4_activation_allowed"] is False
    assert frontier["training_allowed"] is False
    assert frontier["later_stages_activated"] is False
    assert frontier["model_selection_performed"] is False
    assert frontier["final_role_accessed"] is False
    assert frontier["zero_founder_cost"] is True
