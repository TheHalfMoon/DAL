from __future__ import annotations

import math
import statistics
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.p08_protocol_selection import (
    COVERAGE_TARGETS,
    ECAL_CANDIDATES,
    FHIR_CANDIDATES,
    PAPER_CHECKPOINT_SHA256,
    SG000020_CONTRACT_SHA256,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel


class TemperatureFit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    method: Literal["golden-section-log-temperature-v0.1"] = (
        "golden-section-log-temperature-v0.1"
    )
    count: Literal[50] = 50
    log_temperature: float
    temperature: float = Field(gt=0.0)
    nll_before: float = Field(ge=0.0)
    nll_after: float = Field(ge=0.0)


class PlattFit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    method: Literal["damped-newton-platt-v0.1"] = "damped-newton-platt-v0.1"
    count: Literal[100] = 100
    coefficient: float
    intercept: float
    bce_before: float = Field(ge=0.0)
    bce_after: float = Field(ge=0.0)
    iterations_used: int = Field(ge=0, le=100)


class CalibrationEvidence(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    method: Literal["temperature-scaling-action+platt-sufficiency-v0.1"] = (
        "temperature-scaling-action+platt-sufficiency-v0.1"
    )
    contract_sha256: Literal[
        "13f05f806ced6a4f2aa67543e1e4236ec0c6208a19905de7158fd96ce6bde637"
    ] = SG000020_CONTRACT_SHA256
    paper_checkpoint_sha256: Literal[
        "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
    ] = PAPER_CHECKPOINT_SHA256
    checkpoint_reconstruction_verified: Literal[True] = True
    action: TemperatureFit
    sufficiency: PlattFit
    coverage_targets: list[float] = Field(default_factory=lambda: list(COVERAGE_TARGETS))
    calibration_rows_used: Literal[150] = 150
    fhir_rows_used_for_parameter_fitting: Literal[0] = 0
    final_test_rows_used: Literal[0] = 0
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_targets(self) -> CalibrationEvidence:
        if self.coverage_targets != list(COVERAGE_TARGETS):
            raise ValueError("coverage target drift")
        return self


EcalDecisionValue = Literal["keep", "reject"]


class EcalDecision(StrictModel):
    component: Literal[
        "evidence",
        "hard-negative",
        "proper-scoring",
        "replay-retention",
        "state-action-contrastive",
    ]
    decision: EcalDecisionValue
    canonical_mapping: str = Field(min_length=1)
    requires_retraining_or_checkpoint_mutation: bool
    exact_frozen_d03_mapping: bool
    rationale: str = Field(min_length=1)


class EcalDecisionLedger(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    selection_scope: Literal[
        "paper-mechanism-reporting-freeze-not-paper-checkpoint-mutation"
    ] = "paper-mechanism-reporting-freeze-not-paper-checkpoint-mutation"
    decisions: list[EcalDecision]
    paper_checkpoint_sha256: Literal[
        "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
    ] = PAPER_CHECKPOINT_SHA256
    checkpoint_mutated: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_decisions(self) -> EcalDecisionLedger:
        if [row.component for row in self.decisions] != list(ECAL_CANDIDATES):
            raise ValueError("ECAL decision order drift")
        return self


class FhirRepresentationEvidence(StrictModel):
    representation: Literal[
        "canonical-structured",
        "canonical-with-narrative",
        "flat-text",
        "source-order-json",
    ]
    requested_reference_count: int = Field(ge=0)
    resolved_reference_count: int = Field(ge=0)
    unique_resource_count: int = Field(ge=0)
    missing_resource_count: int = Field(ge=0)
    parse_failure_count: int = Field(ge=0)
    deterministic_repeat: bool
    key_order_invariant: bool
    source_order_sensitivity_recorded: bool
    narrative_exposure_count: int = Field(ge=0)
    median_rendered_bytes: float = Field(ge=0.0)
    min_rendered_bytes: int = Field(ge=0)
    max_rendered_bytes: int = Field(ge=0)
    eligible: bool


class FhirSelectionEvidence(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    fhir_agentbench_revision: Literal[
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    ] = "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    calibration_row_count: Literal[341] = 341
    physionet_project: Literal["mimic-iv-fhir-demo"] = "mimic-iv-fhir-demo"
    physionet_version: Literal["2.1.0"] = "2.1.0"
    physionet_sha256s_sha256: str
    checksum_entry_count: int = Field(ge=1)
    checksum_verified_file_count: int = Field(ge=1)
    representations: list[FhirRepresentationEvidence]
    selected_representation: Literal[
        "canonical-structured",
        "canonical-with-narrative",
        "flat-text",
        "source-order-json",
    ]
    selection_objective: Literal[
        "minimum-median-rendered-bytes-among-eligible-representations"
    ] = "minimum-median-rendered-bytes-among-eligible-representations"
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_candidate_order(self) -> FhirSelectionEvidence:
        if [row.representation for row in self.representations] != list(FHIR_CANDIDATES):
            raise ValueError("FHIR representation evidence order drift")
        eligible = [row for row in self.representations if row.eligible]
        if not eligible:
            raise ValueError("no eligible FHIR representation")
        expected = min(
            eligible,
            key=lambda row: (
                row.median_rendered_bytes,
                list(FHIR_CANDIDATES).index(row.representation),
            ),
        ).representation
        if self.selected_representation != expected:
            raise ValueError("FHIR selected representation violates frozen objective")
        return self


class AuthorizationCandidate(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    state: Literal["candidate-only"] = "candidate-only"
    canonical_dependency: Literal[
        "3ca0dd2aae85a68473849108764a45a538de1019"
    ] = "3ca0dd2aae85a68473849108764a45a538de1019"
    paper_checkpoint_sha256: Literal[
        "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
    ] = PAPER_CHECKPOINT_SHA256
    required_system_bundle_digests: dict[str, str]
    calibration_contract_sha256: Literal[
        "13f05f806ced6a4f2aa67543e1e4236ec0c6208a19905de7158fd96ce6bde637"
    ] = SG000020_CONTRACT_SHA256
    calibration_evidence_sha256: str
    selected_ecal_configuration_sha256: str
    selected_fhir_representation_sha256: str
    coverage_targets: list[float] = Field(default_factory=lambda: list(COVERAGE_TARGETS))
    hardware_protocol_revision: Literal["p08-hardware-stratified-v0.1"] = (
        "p08-hardware-stratified-v0.1"
    )
    multiplicity_policy: Literal["holm-primary-family-v0.1"] = (
        "holm-primary-family-v0.1"
    )
    final_test_access: Literal["sealed"] = "sealed"
    can_authorize_inference: Literal[False] = False
    separate_authorization_grain_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_hashes(self) -> AuthorizationCandidate:
        expected_systems = {
            "gax-paper-candidate": "0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b",
            "clinical-encoder": "b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388",
            "laya": "b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534",
        }
        if self.required_system_bundle_digests != expected_systems:
            raise ValueError("required system bundle digest drift")
        for name, value in (
            ("calibration_evidence_sha256", self.calibration_evidence_sha256),
            ("selected_ecal_configuration_sha256", self.selected_ecal_configuration_sha256),
            ("selected_fhir_representation_sha256", self.selected_fhir_representation_sha256),
        ):
            _require_sha256(value, name)
        if self.coverage_targets != list(COVERAGE_TARGETS):
            raise ValueError("authorization coverage targets drift")
        return self


def multiclass_nll(
    logits: list[list[float]], labels: list[int], *, log_temperature: float = 0.0
) -> float:
    if not logits or len(logits) != len(labels):
        raise ValueError("logits and labels must be non-empty and aligned")
    temperature = math.exp(log_temperature)
    losses: list[float] = []
    for row, label in zip(logits, labels, strict=True):
        if not row or label < 0 or label >= len(row):
            raise ValueError("invalid multiclass calibration row")
        scaled = [float(value) / temperature for value in row]
        maximum = max(scaled)
        log_denom = maximum + math.log(sum(math.exp(value - maximum) for value in scaled))
        losses.append(log_denom - scaled[label])
    return sum(losses) / len(losses)


def fit_temperature(logits: list[list[float]], labels: list[int]) -> TemperatureFit:
    if len(logits) != 50 or len(labels) != 50:
        raise ValueError("action temperature fit requires exactly 50 PubMedQA rows")
    left, right = -5.0, 5.0
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    c = right - ratio * (right - left)
    d = left + ratio * (right - left)
    fc = multiclass_nll(logits, labels, log_temperature=c)
    fd = multiclass_nll(logits, labels, log_temperature=d)
    for _ in range(128):
        if fc <= fd:
            right, d, fd = d, c, fc
            c = right - ratio * (right - left)
            fc = multiclass_nll(logits, labels, log_temperature=c)
        else:
            left, c, fc = c, d, fd
            d = left + ratio * (right - left)
            fd = multiclass_nll(logits, labels, log_temperature=d)
    candidates = [
        (multiclass_nll(logits, labels, log_temperature=value), value)
        for value in (left, c, d, right)
    ]
    loss, best = min(candidates, key=lambda pair: (pair[0], pair[1]))
    return TemperatureFit(
        log_temperature=best,
        temperature=math.exp(best),
        nll_before=multiclass_nll(logits, labels),
        nll_after=loss,
    )


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def binary_cross_entropy(raw_logits: list[float], labels: list[int], a: float, b: float) -> float:
    if not raw_logits or len(raw_logits) != len(labels):
        raise ValueError("binary logits and labels must be non-empty and aligned")
    total = 0.0
    for raw, label in zip(raw_logits, labels, strict=True):
        if label not in {0, 1}:
            raise ValueError("binary label must be 0 or 1")
        value = a * float(raw) + b
        total += max(value, 0.0) - label * value + math.log1p(math.exp(-abs(value)))
    return total / len(raw_logits)


def fit_platt(raw_logits: list[float], labels: list[int]) -> PlattFit:
    if len(raw_logits) != 100 or len(labels) != 100:
        raise ValueError("sufficiency Platt fit requires exactly 100 paired rows")
    a, b = 1.0, 0.0
    l2, damping, tolerance = 1e-6, 1e-8, 1e-12
    used = 0
    count = float(len(raw_logits))
    for iteration in range(1, 101):
        grad_a = l2 * a
        grad_b = l2 * b
        h_aa = l2 + damping
        h_ab = 0.0
        h_bb = l2 + damping
        for raw, label in zip(raw_logits, labels, strict=True):
            x = float(raw)
            probability = _sigmoid(a * x + b)
            residual = probability - label
            weight = probability * (1.0 - probability)
            grad_a += residual * x / count
            grad_b += residual / count
            h_aa += weight * x * x / count
            h_ab += weight * x / count
            h_bb += weight / count
        used = iteration
        if math.hypot(grad_a, grad_b) <= tolerance:
            break
        determinant = h_aa * h_bb - h_ab * h_ab
        if determinant <= 0.0 or not math.isfinite(determinant):
            raise ValueError("Platt Hessian is not positive definite")
        step_a = (h_bb * grad_a - h_ab * grad_b) / determinant
        step_b = (-h_ab * grad_a + h_aa * grad_b) / determinant
        a -= step_a
        b -= step_b
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("Platt optimization became non-finite")
    return PlattFit(
        coefficient=a,
        intercept=b,
        bce_before=binary_cross_entropy(raw_logits, labels, 1.0, 0.0),
        bce_after=binary_cross_entropy(raw_logits, labels, a, b),
        iterations_used=used,
    )


def frozen_ecal_ledger() -> EcalDecisionLedger:
    rows = [
        EcalDecision(
            component="evidence",
            decision="keep",
            canonical_mapping="P04 evidence intervention + D03 evidence-delta assurance path",
            requires_retraining_or_checkpoint_mutation=False,
            exact_frozen_d03_mapping=True,
            rationale=(
                "D03 already contains the frozen evidence-delta assurance mechanism; keeping "
                "evidence changes reporting scope only and does not mutate the checkpoint."
            ),
        ),
        EcalDecision(
            component="hard-negative",
            decision="reject",
            canonical_mapping="P04 hard-negative training objective",
            requires_retraining_or_checkpoint_mutation=True,
            exact_frozen_d03_mapping=False,
            rationale="Applying the P04 hard-negative objective would require reopening training.",
        ),
        EcalDecision(
            component="proper-scoring",
            decision="reject",
            canonical_mapping="P04 Brier/proper-scoring training objective",
            requires_retraining_or_checkpoint_mutation=True,
            exact_frozen_d03_mapping=False,
            rationale="Applying the P04 proper-scoring objective would require reopening training.",
        ),
        EcalDecision(
            component="replay-retention",
            decision="reject",
            canonical_mapping="P04 replay sampling policy",
            requires_retraining_or_checkpoint_mutation=True,
            exact_frozen_d03_mapping=False,
            rationale="Replay changes the training schedule and is incompatible with the frozen D03 checkpoint.",
        ),
        EcalDecision(
            component="state-action-contrastive",
            decision="reject",
            canonical_mapping="No exact same-name canonical component; P04 bidirectional alignment is related",
            requires_retraining_or_checkpoint_mutation=True,
            exact_frozen_d03_mapping=False,
            rationale=(
                "The candidate lacks an exact canonical D03 mapping and the related P04 alignment "
                "objective would require retraining; silent renaming is forbidden."
            ),
        ),
    ]
    return EcalDecisionLedger(decisions=rows)


def select_fhir_representation(
    rows: list[FhirRepresentationEvidence],
    *,
    physionet_sha256s_sha256: str,
    checksum_entry_count: int,
    checksum_verified_file_count: int,
) -> FhirSelectionEvidence:
    _require_sha256(physionet_sha256s_sha256, "physionet_sha256s_sha256")
    if [row.representation for row in rows] != list(FHIR_CANDIDATES):
        raise ValueError("FHIR candidate order drift")
    eligible = [row for row in rows if row.eligible]
    if not eligible:
        raise ValueError("no eligible FHIR representation")
    selected = min(
        eligible,
        key=lambda row: (
            row.median_rendered_bytes,
            list(FHIR_CANDIDATES).index(row.representation),
        ),
    ).representation
    return FhirSelectionEvidence(
        physionet_sha256s_sha256=physionet_sha256s_sha256,
        checksum_entry_count=checksum_entry_count,
        checksum_verified_file_count=checksum_verified_file_count,
        representations=rows,
        selected_representation=selected,
    )


def artifact_digest(model: StrictModel) -> str:
    return canonical_json_sha256(model.model_dump(mode="json"))


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
