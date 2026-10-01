from __future__ import annotations

from pathlib import Path

import pytest

from gaxbench.p08_final_evaluation import (
    AUTHORIZATION_DIGEST,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    aurc,
    calibration_threshold,
    load_final_evaluation_contract,
    paired_bootstrap_difference,
    risk_at_coverage,
    softmax,
    validate_final_evaluation_preflight,
)

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "registry" / "p08_final_evaluation_contract_sg000022.json"


def test_final_evaluation_contract_is_prospective_and_authorization_bound() -> None:
    contract = load_final_evaluation_contract(CONTRACT)
    assert contract.authorization_digest == AUTHORIZATION_DIGEST
    assert contract.pre_execution_amendment.final_test_rows_used_before_freeze == 0
    assert contract.pre_execution_amendment.outcome_information_used is False
    assert contract.final_test_inference_executed is False
    assert contract.final_test_rows_used == 0
    assert contract.statistics.ci_level == CI_LEVEL
    assert contract.statistics.bootstrap_replicates == BOOTSTRAP_REPLICATES
    assert contract.statistics.bootstrap_seed == BOOTSTRAP_SEED


def test_primary_family_and_fhir_interface_block_are_frozen() -> None:
    contract = load_final_evaluation_contract(CONTRACT)
    plans = {row.id: row for row in contract.benchmarks}
    assert plans["pubmedqa-pqal"].primary_metric == "action_accuracy"
    assert plans["gax-native-abstention-pqal"].primary_metric == "risk_at_80"
    fhir = plans["fhir-agentbench"]
    assert fhir.primary_status == "interface-blocked-preexecution"
    assert fhir.interface_block is not None
    assert fhir.interface_block.detected_before_final_test_access is True
    assert fhir.interface_block.failure_category == "interface"
    assert fhir.interface_block.requested_count == 173
    assert fhir.interface_block.completed_count == 0
    assert fhir.interface_block.failed_count == 173
    assert fhir.interface_block.replacement_forbidden is True


def test_authorization_chain_preflight_is_valid_without_test_access() -> None:
    contract = validate_final_evaluation_preflight(ROOT)
    assert contract.grain_id == "SG-000022"
    assert contract.execution_policy.no_post_test_tuning is True


def test_softmax_is_temperature_scaled_and_normalized() -> None:
    probabilities = softmax([0.0, 1.0, 2.0], temperature=2.0)
    assert sum(probabilities) == pytest.approx(1.0)
    assert probabilities[2] > probabilities[1] > probabilities[0]


def test_selective_risk_and_aurc_are_deterministic() -> None:
    correctness = [True, False, True, False]
    scores = [0.9, 0.8, 0.7, 0.6]
    assert risk_at_coverage(correctness, scores, 0.5) == pytest.approx(0.5)
    assert risk_at_coverage(correctness, scores, 0.75) == pytest.approx(1.0 / 3.0)
    assert aurc(correctness, scores) == pytest.approx((0.0 + 0.5 + 1.0 / 3.0 + 0.5) / 4)


def test_calibration_threshold_uses_preregistered_prefix_rule() -> None:
    assert calibration_threshold([0.9, 0.8, 0.7, 0.6], 0.5) == pytest.approx(0.8)
    assert calibration_threshold([0.9, 0.8, 0.7, 0.6], 0.8) == pytest.approx(0.6)


def test_paired_bootstrap_is_seeded_and_paired() -> None:
    rows = [
        {"a": 1.0, "b": 0.0},
        {"a": 0.0, "b": 0.0},
        {"a": 1.0, "b": 1.0},
        {"a": 1.0, "b": 0.0},
    ]

    def mean_a(values: list[dict[str, float]]) -> float:
        return sum(row["a"] for row in values) / len(values)

    def mean_b(values: list[dict[str, float]]) -> float:
        return sum(row["b"] for row in values) / len(values)

    first = paired_bootstrap_difference(rows, mean_a, mean_b, replicates=1000, seed=1729)
    second = paired_bootstrap_difference(rows, mean_a, mean_b, replicates=1000, seed=1729)
    assert first == second
    assert first["estimate"] == pytest.approx(0.5)
    assert first["replicates"] == 1000
