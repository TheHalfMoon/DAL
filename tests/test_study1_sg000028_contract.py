from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry/study1_sg000028_contract.json"
FRONTIER = ROOT / "registry/study1_sg000028_frontier_status.json"
WORKFLOW = ROOT / ".github/workflows/study1-sg000028-query-trace-gate.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sg000028_binds_canonical_d3_and_founder_authorizations() -> None:
    contract = _load(CONTRACT)
    dependency = contract["activation_dependency"]
    assert contract["specgrain_id"] == "SG-000028"
    assert contract["research_contract_issue"] == 141
    assert dependency["d3_closeout_merge"] == (
        "13ac5bc7412fe38cdd575c3e621ad4c09ebd776a"
    )
    assert dependency["d3_post_main_gaxbench_run"] == 37145288600
    assert dependency["d3_post_main_manuscript_run"] == 37145288944
    assert dependency["query_trace_authorization_issue"] == 126
    assert dependency["query_trace_authorization_comment_id"] == 5970310150
    assert dependency["stage_order_authorization_issue"] == 128
    assert dependency["stage_order_authorization_comment_id"] == 5970595978


def test_gate_binds_exact_frozen_trace_producer() -> None:
    producer = _load(CONTRACT)["trace_producer"]
    assert producer["base_model"] == "Qwen/Qwen3-4B-Instruct-2507"
    assert producer["base_model_revision"] == (
        "cdbee75f17c01a7cc42f958dc650907174af0554"
    )
    assert producer["tokenizer_revision"] == producer["base_model_revision"]
    assert producer["quantized_sha256"] == (
        "ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1"
    )
    assert producer["llama_cpp_revision"] == (
        "d2e54583c7452353eb35d40431281f6ee984332f"
    )
    assert producer["fhir_agentbench_revision"] == (
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    )
    assert producer["agent_strategy"] == "single_turn_request"
    assert producer["temperature"] == 0.0


def test_development_denominator_and_final_firewall_are_frozen() -> None:
    contract = _load(CONTRACT)
    development = contract["development_roles"]
    final = contract["sealed_final_firewall"]
    assert development["calibration_rows"] == 341
    assert development["validation_rows"] == 1122
    assert development["development_rows"] == 1463
    assert development["membership_sha256"] == (
        "b90e774067d0a0e4251e32584b3aeea9629a01df9201fc550988e70d17dbda15"
    )
    assert final["patients"] == 40
    assert final["rows"] == 173
    assert final["test_gold_serialized"] is False
    assert final["question_content_access"] == "forbidden"
    assert final["trace_generation"] == "forbidden"
    assert final["model_output_access"] == "forbidden"


def test_gate_is_first_turn_only_and_emits_normalized_evidence_only() -> None:
    contract = _load(CONTRACT)
    execution = contract["execution"]
    normalization = contract["normalization"]
    assert execution["main_only"] is True
    assert execution["trace_shards"] == 8
    assert execution["first_turn_only"] is True
    assert execution["second_turn_reasoning"] is False
    assert execution["answer_correctness_scored"] is False
    assert normalization["raw_question_text_emitted"] is False
    assert normalization["raw_patient_ids_emitted"] is False
    assert normalization["raw_query_values_emitted"] is False
    assert normalization["raw_traces_emitted"] is False
    assert normalization["question_id_sha256_allowed"] is True
    assert normalization["normalized_pattern_classes_allowed"] is True


def test_gate_cannot_activate_training_or_final_access() -> None:
    contract = _load(CONTRACT)
    governance = contract["governance"]
    assert governance["d4_activated"] is False
    assert governance["training_allowed"] is False
    assert governance["fine_tuning_allowed"] is False
    assert governance["objective_fitting_allowed"] is False
    assert governance["calibration_or_threshold_fitting_allowed"] is False
    assert governance["d7_model_selection_performed"] is False
    assert governance["final_role_access_allowed"] is False
    assert governance["trace_producer_switching_after_gate_outcomes"] is False


def test_frontier_records_canonical_dependency_blocker_without_stage_progression() -> None:
    frontier = _load(FRONTIER)
    dependency = frontier["canonical_dependency"]
    failure = frontier["dependency_failure"]
    assert frontier["specgrain_id"] == "SG-000028"
    assert frontier["state"] == "blocked-prospective-recovery-protocol-authorized"
    assert frontier["query_trace_gate_status"] == "blocked-behavior-changing"
    assert frontier["governance_decision_authorization_received"] is True
    assert frontier["governance_decision_authorization_comment"] == 5981658161
    assert frontier["prospective_recovery_protocol_issue"] == 150
    assert frontier["prospective_recovery_protocol_specgrain"] == "SG-000029"
    assert frontier["prospective_recovery_execution_authorized"] is False
    assert dependency["provenance_repair_merge"] == (
        "d01f6eaf22ae11b44cff7a979526596c36e6ac03"
    )
    assert dependency["provenance_repair_post_main_gaxbench_run"] == 37153192785
    assert dependency["provenance_repair_post_main_manuscript_run"] == 37153192731
    assert dependency["blocked_dependency_run"] == 37153192763
    assert failure["exception"] == "ModuleNotFoundError: No module named 'sqlglot'"
    assert failure["trace_generation_started"] is False
    assert failure["development_question_content_accessed"] is False
    assert failure["final_question_content_accessed"] is False
    assert failure["raw_benchmark_source_downloaded_to_ephemeral_runner"] is True
    assert failure["raw_benchmark_source_cleanup_step_executed"] is False
    assert frontier["query_trace_evidence_generated"] is True
    historical = _load(ROOT / frontier["historical_pre_execution_frontier_path"])
    assert historical["state"] == "blocked-pre-trace-frozen-upstream-dependency-missing"
    assert historical["query_trace_evidence_generated"] is False
    assert frontier["main_only_execution_required"] is True
    assert frontier["d4_activation_allowed"] is False
    assert frontier["training_allowed"] is False
    assert frontier["final_role_accessed"] is False


def test_workflow_is_main_only_and_uses_exact_eight_shard_denominator() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" not in text
    assert "branches:\n      - main" in text
    assert "shard: [0, 1, 2, 3, 4, 5, 6, 7]" in text
    assert "study1_sg000028_query_trace_runner.py" in text
    assert "study1_sg000028_query_trace_aggregate.py" in text
    assert "raw gate run cannot itself activate D4" in text


def test_workflow_pins_required_frozen_upstream_import_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "sqlglot==26.9.0" in text
    assert "sqlparse==0.5.3" in text
    assert "tqdm==4.66.5" in text


def test_raw_benchmark_source_cleanup_runs_even_after_shard_failure() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    marker = "- name: Delete raw benchmark source before artifact upload"
    cleanup = text.split(marker, maxsplit=1)[1].split(
        "- name: Upload normalized shard evidence only", maxsplit=1
    )[0]
    assert "if: always()" in cleanup
    assert "source.unlink(missing_ok=True)" in cleanup
