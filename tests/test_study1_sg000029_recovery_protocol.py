import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "registry/study1_sg000029_recovery_protocol.json"
CONTRACT = ROOT / "registry/study1_sg000029_contract.json"
FRONTIER = ROOT / "registry/study1_sg000029_frontier_status.json"
PARENT_FRONTIER = ROOT / "registry/study1_sg000028_frontier_status.json"
PARENT_CLOSEOUT = ROOT / "registry/study1_sg000028_governance_gate_closeout.json"
PROVENANCE_CORRECTION = (
    ROOT / "registry/study1_sg000028_trace_producer_provenance_correction.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_protocol_preserves_immutable_negative_parent() -> None:
    protocol = _load(PROTOCOL)
    parent = _load(PARENT_FRONTIER)
    closeout = _load(PARENT_CLOSEOUT)

    result = protocol["immutable_original_result"]
    assert result["scientific_state"] == "BLOCKED"
    assert result["development_rows"] == 1463
    assert result["pass_rows"] == 224
    assert result["behavior_changing_blocker_rows"] == 1239
    assert result["may_be_relabelled_pass"] is False

    assert parent["query_trace_gate_status"] == "blocked-behavior-changing"
    assert parent["observed_result"]["total_rows"] == 1463
    assert parent["observed_result"]["pass_rows"] == 224
    assert parent["observed_result"]["behavior_changing_blocker_rows"] == 1239
    assert closeout["sg000028_scientific_state"] == "BLOCKED"


def test_recovery_protocol_discloses_development_outcome_exposure() -> None:
    protocol = _load(PROTOCOL)
    exposure = protocol["development_exposure_disclosure"]

    assert exposure["calibration_and_validation_are_now_exposed_development"] is True
    assert exposure["rows"] == 1463
    assert exposure["blind_development_claim_permitted"] is False
    assert exposure["independent_confirmation_claim_permitted"] is False


def test_recovery_protocol_keeps_final_role_sealed() -> None:
    protocol = _load(PROTOCOL)
    final_role = protocol["sealed_final_role"]

    assert final_role["patients"] == 40
    assert final_role["rows"] == 173
    assert final_role["question_text_access_allowed"] is False
    assert final_role["trace_access_allowed"] is False
    assert final_role["labels_or_true_answer_access_allowed"] is False
    assert final_role["proc_query_access_allowed"] is False
    assert final_role["true_fhir_ids_access_allowed"] is False
    assert final_role["outputs_or_supervision_access_allowed"] is False


def test_sg000029_does_not_authorize_execution_or_d4() -> None:
    protocol = _load(PROTOCOL)
    contract = _load(CONTRACT)
    frontier = _load(FRONTIER)

    forbidden = protocol["non_authorizations"]
    assert all(value is False for value in forbidden.values())

    execution = contract["execution_boundary"]
    assert execution["new_inference_allowed"] is False
    assert execution["rerun_sg000028_allowed"] is False
    assert execution["training_allowed"] is False
    assert execution["d4_activation_allowed"] is False
    assert execution["final_role_access_allowed"] is False

    assert frontier["new_inference_authorized"] is False
    assert frontier["r2_execution_authorized"] is False
    assert frontier["d4_activation_allowed"] is False
    assert frontier["final_role_access_allowed"] is False


def test_r1_is_non_inference_and_r2_requires_new_authorization() -> None:
    protocol = _load(PROTOCOL)
    stages = {stage["stage"]: stage for stage in protocol["stage_order"]}

    assert stages["R0"]["new_inference_allowed"] is False
    assert stages["R1"]["new_inference_allowed"] is False
    assert stages["R2"]["requires_new_founder_execution_authorization"] is True
    assert stages["R2"]["authorized_by_sg000029"] is False
    assert stages["D4"]["requires_r2_canonical_pass"] is True
    assert stages["D4"]["requires_separate_governed_activation"] is True
    assert stages["D4"]["authorized_by_sg000029"] is False


def test_recovery_rules_forbid_role_rewrite_and_silent_substitution() -> None:
    protocol = _load(PROTOCOL)
    boundary = protocol["recovery_system_boundary"]
    policy = protocol["prospective_compatibility_policy"]

    assert boundary["no_silent_reinterpretation"] is True
    assert boundary["no_favorable_row_omission"] is True
    assert boundary["no_retry_until_favorable"] is True
    assert boundary["no_sql_proc_query_substitution"] is True
    assert boundary["no_expected_resource_id_substitution"] is True
    assert policy["patient_identity_rewrite_allowed"] is False
    assert policy["sealed_final_role_expansion_allowed"] is False
    assert policy["unknown_semantics_guessing_allowed"] is False


def test_recovery_identity_uses_canonical_provenance_correction() -> None:
    protocol = _load(PROTOCOL)
    correction = _load(PROVENANCE_CORRECTION)
    identity = protocol["recovery_trace_producer_identity"]

    assert identity["base_model_revision"] == (
        "cdbee75f17c01a7cc42f958dc650907174af0554"
    )
    assert identity["fhir_agentbench_revision"] == (
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    )
    assert identity["transport_provenance_source"] == (
        "registry/study1_sg000028_trace_producer_provenance_correction.json"
    )
    assert correction["semantic_invariants"]["behavior_changed"] is False
    assert correction["semantic_invariants"]["post_outcome_trace_producer_switching"] is False


def test_parent_frontier_records_authorized_protocol_only() -> None:
    parent = _load(PARENT_FRONTIER)

    assert parent["state"] == "blocked-prospective-recovery-protocol-authorized"
    assert parent["governance_decision_authorization_received"] is True
    assert parent["governance_decision_authorization_comment"] == 5981658161
    assert parent["prospective_recovery_protocol_issue"] == 150
    assert parent["prospective_recovery_protocol_specgrain"] == "SG-000029"
    assert parent["prospective_recovery_execution_authorized"] is False
    assert parent["d4_activation_allowed"] is False
    assert parent["training_allowed"] is False
    assert parent["final_role_accessed"] is False
