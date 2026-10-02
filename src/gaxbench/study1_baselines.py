from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import Prediction, StrictModel

D2BaselineId = Literal["B0-QA", "B1-QA-CAL", "B2-QA-CONF-ABSTAIN"]


class D2BaselineDecision(StrictModel):
    """One D2 baseline view over a shared, already-produced base prediction."""

    schema_version: Literal["0.1"] = "0.1"
    baseline_id: D2BaselineId
    item_id: str = Field(min_length=1)
    base_prediction_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    probabilities: dict[str, float]
    predicted_action: str = Field(min_length=1)
    correctness_score: float | None = None
    threshold: float | None = None
    abstain: bool = False

    @model_validator(mode="after")
    def validate_semantics(self) -> D2BaselineDecision:
        # Reuse the canonical prediction distribution validation rather than
        # silently introducing a second probability contract for Study 1.
        Prediction(item_id=self.item_id, probabilities=self.probabilities)
        if self.predicted_action != _predicted_action(self.probabilities):
            raise ValueError("predicted_action must match the shared base probability vector")

        _validate_optional_unit_interval(self.correctness_score, "correctness_score")
        _validate_optional_unit_interval(self.threshold, "threshold")

        if self.baseline_id == "B0-QA":
            if self.correctness_score is not None or self.threshold is not None or self.abstain:
                raise ValueError("B0-QA must commit the base answer without score or threshold")
        elif self.baseline_id == "B1-QA-CAL":
            if self.correctness_score is None or self.threshold is not None or self.abstain:
                raise ValueError("B1-QA-CAL requires a score and must still commit the base answer")
        else:
            if self.correctness_score is None or self.threshold is None:
                raise ValueError("B2-QA-CONF-ABSTAIN requires score and threshold mechanics")
            expected_abstain = self.correctness_score < self.threshold
            if self.abstain != expected_abstain:
                raise ValueError("B2 abstention must be exactly correctness_score < threshold")
        return self


class D2ExecutionAccounting(StrictModel):
    """Failure-aware denominator accounting for one D2 baseline execution surface."""

    schema_version: Literal["0.1"] = "0.1"
    requested: int = Field(ge=0)
    completed: int = Field(ge=0)
    completed_abstentions: int = Field(ge=0)
    interface_failures: int = Field(ge=0)
    parse_failures: int = Field(ge=0)
    missing_outputs: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_accounting(self) -> D2ExecutionAccounting:
        if self.completed_abstentions > self.completed:
            raise ValueError("completed_abstentions cannot exceed completed")
        accounted = (
            self.completed
            + self.interface_failures
            + self.parse_failures
            + self.missing_outputs
        )
        if accounted != self.requested:
            raise ValueError(
                "D2 denominator accounting must satisfy requested = completed + "
                "interface_failures + parse_failures + missing_outputs"
            )
        return self


def build_b0(base_prediction: Prediction) -> D2BaselineDecision:
    return _build_decision("B0-QA", base_prediction)


def build_b1(
    base_prediction: Prediction,
    *,
    correctness_score: float,
) -> D2BaselineDecision:
    return _build_decision(
        "B1-QA-CAL",
        base_prediction,
        correctness_score=correctness_score,
    )


def build_b2(
    base_prediction: Prediction,
    *,
    correctness_score: float,
    threshold: float,
) -> D2BaselineDecision:
    _validate_optional_unit_interval(correctness_score, "correctness_score")
    _validate_optional_unit_interval(threshold, "threshold")
    return _build_decision(
        "B2-QA-CONF-ABSTAIN",
        base_prediction,
        correctness_score=correctness_score,
        threshold=threshold,
        abstain=correctness_score < threshold,
    )


def assert_matched_base_identity(decisions: Sequence[D2BaselineDecision]) -> str:
    """Fail unless all wrappers preserve the exact same base answer identity."""

    if not decisions:
        raise ValueError("at least one D2 baseline decision is required")
    first = decisions[0]
    expected = (
        first.item_id,
        first.base_prediction_sha256,
        first.probabilities,
        first.predicted_action,
    )
    for decision in decisions[1:]:
        observed = (
            decision.item_id,
            decision.base_prediction_sha256,
            decision.probabilities,
            decision.predicted_action,
        )
        if observed != expected:
            raise ValueError("D2 baseline wrappers do not preserve matched base-answer identity")
    return first.base_prediction_sha256


def base_prediction_sha256(prediction: Prediction) -> str:
    """Hash only the base-answer identity, excluding D2 wrapper policy fields."""

    _require_non_abstaining_base(prediction)
    return canonical_json_sha256(
        {
            "item_id": prediction.item_id,
            "probabilities": prediction.probabilities,
        }
    )


def _build_decision(
    baseline_id: D2BaselineId,
    base_prediction: Prediction,
    *,
    correctness_score: float | None = None,
    threshold: float | None = None,
    abstain: bool = False,
) -> D2BaselineDecision:
    _require_non_abstaining_base(base_prediction)
    return D2BaselineDecision(
        baseline_id=baseline_id,
        item_id=base_prediction.item_id,
        base_prediction_sha256=base_prediction_sha256(base_prediction),
        probabilities=dict(base_prediction.probabilities),
        predicted_action=_predicted_action(base_prediction.probabilities),
        correctness_score=correctness_score,
        threshold=threshold,
        abstain=abstain,
    )


def _predicted_action(probabilities: dict[str, float]) -> str:
    return max(probabilities.items(), key=lambda pair: (pair[1], pair[0]))[0]


def _require_non_abstaining_base(prediction: Prediction) -> None:
    if prediction.abstain:
        raise ValueError("D2 B0/B1/B2 require a shared base QA prediction that does not abstain")


def _validate_optional_unit_interval(value: float | None, name: str) -> None:
    if value is None:
        return
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
