from __future__ import annotations

import pytest

from gaxbench.schema import Prediction
from gaxbench.study1_baselines import (
    D2BaselineDecision,
    D2ExecutionAccounting,
    assert_matched_base_identity,
    base_prediction_sha256,
    build_b0,
    build_b1,
    build_b2,
)


def _base() -> Prediction:
    return Prediction(item_id="case-1", probabilities={"no": 0.2, "yes": 0.8})


def test_b0_b1_b2_preserve_exact_base_answer_identity() -> None:
    base = _base()
    b0 = build_b0(base)
    b1 = build_b1(base, correctness_score=0.65)
    b2 = build_b2(base, correctness_score=0.65, threshold=0.70)

    digest = assert_matched_base_identity([b0, b1, b2])
    assert digest == base_prediction_sha256(base)
    assert b0.probabilities == b1.probabilities == b2.probabilities == base.probabilities
    assert b0.predicted_action == b1.predicted_action == b2.predicted_action == "yes"
    assert b0.abstain is False
    assert b1.abstain is False
    assert b2.abstain is True


def test_b2_threshold_tie_commits_deterministically() -> None:
    decision = build_b2(_base(), correctness_score=0.70, threshold=0.70)
    assert decision.abstain is False


def test_base_action_tie_matches_existing_probability_then_action_id_rule() -> None:
    base = Prediction(item_id="tie", probabilities={"a": 0.5, "b": 0.5})
    decisions = [
        build_b0(base),
        build_b1(base, correctness_score=0.5),
        build_b2(base, correctness_score=0.5, threshold=0.4),
    ]
    assert {decision.predicted_action for decision in decisions} == {"b"}
    assert_matched_base_identity(decisions)


def test_d2_wrappers_reject_preexisting_base_abstention() -> None:
    base = Prediction(item_id="case-1", probabilities={"no": 0.2, "yes": 0.8}, abstain=True)
    with pytest.raises(ValueError, match="shared base QA prediction"):
        build_b0(base)
    with pytest.raises(ValueError, match="shared base QA prediction"):
        build_b1(base, correctness_score=0.5)
    with pytest.raises(ValueError, match="shared base QA prediction"):
        build_b2(base, correctness_score=0.5, threshold=0.5)


def test_matched_identity_rejects_probability_or_item_drift() -> None:
    left = build_b0(_base())
    right = D2BaselineDecision(
        baseline_id="B1-QA-CAL",
        item_id="case-2",
        base_prediction_sha256="0" * 64,
        probabilities={"no": 0.2, "yes": 0.8},
        predicted_action="yes",
        correctness_score=0.65,
    )
    with pytest.raises(ValueError, match="matched base-answer identity"):
        assert_matched_base_identity([left, right])


def test_execution_accounting_is_failure_aware_and_exact() -> None:
    accounting = D2ExecutionAccounting(
        requested=10,
        completed=6,
        completed_abstentions=2,
        interface_failures=1,
        parse_failures=2,
        missing_outputs=1,
    )
    assert accounting.requested == 10

    with pytest.raises(ValueError, match="denominator accounting"):
        D2ExecutionAccounting(
            requested=10,
            completed=6,
            completed_abstentions=2,
            interface_failures=1,
            parse_failures=1,
            missing_outputs=1,
        )

    with pytest.raises(ValueError, match="cannot exceed completed"):
        D2ExecutionAccounting(
            requested=10,
            completed=6,
            completed_abstentions=7,
            interface_failures=1,
            parse_failures=2,
            missing_outputs=1,
        )


def test_wrapper_scores_and_thresholds_must_be_unit_interval() -> None:
    for value in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError, match=r"finite and in \[0, 1\]"):
            build_b1(_base(), correctness_score=value)
        with pytest.raises(ValueError, match=r"finite and in \[0, 1\]"):
            build_b2(_base(), correctness_score=0.5, threshold=value)
