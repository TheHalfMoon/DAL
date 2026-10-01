from __future__ import annotations

import json
import math
import random
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from gaxbench.p08_final_test_authorization import (
    authorization_digest,
    load_final_test_authorization,
)
from gaxbench.schema import StrictModel

SG000022_ACTIVATION_SHA = "c7ea6fbc81a1dd7526a6c453d12c585db6841cb3"
AUTHORIZATION_DIGEST = "626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de"
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 1729
CI_LEVEL = 0.95
COVERAGE_TARGETS = [0.5, 0.8, 0.9]
MULTIPLICITY_POLICY = "holm-primary-family-v0.1"
HARDWARE_PROTOCOL = "p08-hardware-stratified-v0.1"
CALIBRATION_METHOD = "temperature-scaling-action+platt-sufficiency-v0.1"


class InterfaceBlock(StrictModel):
    detected_before_final_test_access: Literal[True] = True
    reason: str = Field(min_length=1)
    failure_category: Literal["interface"] = "interface"
    requested_count: Literal[173] = 173
    completed_count: Literal[0] = 0
    failed_count: Literal[173] = 173
    replacement_forbidden: Literal[True] = True


class BenchmarkPlan(StrictModel):
    id: Literal["pubmedqa-pqal", "gax-native-abstention-pqal", "fhir-agentbench"]
    final_test_count: int = Field(gt=0)
    primary_metric: Literal["action_accuracy", "risk_at_80"]
    metric_direction: Literal["higher-is-better", "lower-is-better"]
    primary_status: Literal["executable", "interface-blocked-preexecution"]
    secondary_systems: list[str] = Field(default_factory=list)
    must_report: list[str] = Field(default_factory=list)
    interface_block: InterfaceBlock | None = None

    @model_validator(mode="after")
    def validate_plan(self) -> BenchmarkPlan:
        counts = {
            "pubmedqa-pqal": 500,
            "gax-native-abstention-pqal": 1000,
            "fhir-agentbench": 173,
        }
        if self.final_test_count != counts[self.id]:
            raise ValueError(f"final-test count drift for {self.id}")
        if self.id == "fhir-agentbench":
            if self.primary_status != "interface-blocked-preexecution":
                raise ValueError(
                    "FHIR final evaluation must preserve the pre-execution interface block"
                )
            if self.interface_block is None:
                raise ValueError("FHIR interface block evidence is required")
        elif self.interface_block is not None:
            raise ValueError("only FHIR-AgentBench may carry the frozen interface block")
        return self


class StatisticsPlan(StrictModel):
    ci_level: float = Field(default=0.95, ge=0.95, le=0.95)
    bootstrap_replicates: Literal[10000] = 10000
    bootstrap_seed: Literal[1729] = 1729
    bootstrap_method: Literal["paired-percentile-mean-difference-v0.1"] = (
        "paired-percentile-mean-difference-v0.1"
    )
    multiplicity_policy: Literal["holm-primary-family-v0.1"] = "holm-primary-family-v0.1"


class PreExecutionAmendment(StrictModel):
    reason: str = Field(min_length=1)
    final_test_rows_used_before_freeze: Literal[0] = 0
    outcome_information_used: Literal[False] = False
    basis: str = Field(min_length=1)


class ExecutionPolicy(StrictModel):
    implementation_qualification_must_precede_final_test: Literal[True] = True
    final_execution_requires_canonical_main: Literal[True] = True
    raw_artifacts_persist_before_derived_metrics: Literal[True] = True
    no_post_test_tuning: Literal[True] = True
    no_architecture_reopening: Literal[True] = True
    no_checkpoint_reselection: Literal[True] = True
    no_calibration_refit: Literal[True] = True
    no_ecal_reselection: Literal[True] = True
    no_fhir_adapter_creation_after_authorization: Literal[True] = True
    null_negative_blocked_results_must_remain_visible: Literal[True] = True
    zero_founder_cost: Literal[True] = True


class FinalEvaluationContract(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    grain_id: Literal["SG-000022"] = "SG-000022"
    contract_revision: Literal["dal-p08-final-evaluation-v0.1"] = (
        "dal-p08-final-evaluation-v0.1"
    )
    canonical_activation_sha: Literal[
        "c7ea6fbc81a1dd7526a6c453d12c585db6841cb3"
    ] = "c7ea6fbc81a1dd7526a6c453d12c585db6841cb3"
    authorization_artifact: Literal["registry/p08_final_test_authorization_sg000021.json"] = (
        "registry/p08_final_test_authorization_sg000021.json"
    )
    authorization_digest: Literal[
        "626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de"
    ] = "626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de"
    pre_execution_amendment: PreExecutionAmendment
    statistics: StatisticsPlan
    coverage_targets: list[float]
    calibration_method: Literal["temperature-scaling-action+platt-sufficiency-v0.1"] = (
        "temperature-scaling-action+platt-sufficiency-v0.1"
    )
    hardware_protocol_revision: Literal["p08-hardware-stratified-v0.1"] = (
        "p08-hardware-stratified-v0.1"
    )
    required_systems: list[str]
    primary_comparison: Literal["gax-paper-candidate-vs-clinical-encoder"] = (
        "gax-paper-candidate-vs-clinical-encoder"
    )
    benchmarks: list[BenchmarkPlan]
    failure_accounting: list[str]
    execution_policy: ExecutionPolicy
    final_test_access: Literal["authorized-only-after-canonical-implementation"] = (
        "authorized-only-after-canonical-implementation"
    )
    final_test_inference_executed: Literal[False] = False
    final_test_rows_used: Literal[0] = 0

    @model_validator(mode="after")
    def validate_frozen_contract(self) -> FinalEvaluationContract:
        if self.statistics.ci_level != CI_LEVEL:
            raise ValueError("CI-level drift")
        if self.coverage_targets != COVERAGE_TARGETS:
            raise ValueError("coverage-target drift")
        if self.required_systems != ["gax-paper-candidate", "clinical-encoder", "laya"]:
            raise ValueError("required-system ordering or identity drift")
        if self.failure_accounting != [
            "requested",
            "completed",
            "timeout",
            "oom",
            "transport",
            "interface",
            "parse",
        ]:
            raise ValueError("failure-accounting drift")
        expected = {
            "pubmedqa-pqal": ("action_accuracy", "higher-is-better"),
            "gax-native-abstention-pqal": ("risk_at_80", "lower-is-better"),
            "fhir-agentbench": ("action_accuracy", "higher-is-better"),
        }
        if [row.id for row in self.benchmarks] != list(expected):
            raise ValueError("benchmark ordering or identity drift")
        for row in self.benchmarks:
            metric, direction = expected[row.id]
            if row.primary_metric != metric or row.metric_direction != direction:
                raise ValueError(f"primary metric drift for {row.id}")
        return self


def load_final_evaluation_contract(path: str | Path) -> FinalEvaluationContract:
    return FinalEvaluationContract.model_validate_json(Path(path).read_text(encoding="utf-8"))


def validate_final_evaluation_preflight(root: str | Path) -> FinalEvaluationContract:
    root_path = Path(root)
    contract = load_final_evaluation_contract(
        root_path / "registry" / "p08_final_evaluation_contract_sg000022.json"
    )
    authorization = load_final_test_authorization(
        root_path / "registry" / "p08_final_test_authorization_sg000021.json"
    )
    if authorization_digest(authorization) != AUTHORIZATION_DIGEST:
        raise ValueError("SG-000021 authorization digest drift")
    if authorization.authorized_grain != "SG-000022":
        raise ValueError("authorization is not scoped to SG-000022")
    if authorization.final_test_inference_executed is not False:
        raise ValueError("authorization artifact already records final-test inference")
    if authorization.final_test_rows_used != 0:
        raise ValueError("authorization artifact already records final-test rows")
    return contract


def softmax(logits: Sequence[float], *, temperature: float = 1.0) -> list[float]:
    if not logits:
        raise ValueError("logits must not be empty")
    if not math.isfinite(temperature) or temperature <= 0.0:
        raise ValueError("temperature must be finite and positive")
    scaled = [float(value) / temperature for value in logits]
    if any(not math.isfinite(value) for value in scaled):
        raise ValueError("logits must be finite")
    maximum = max(scaled)
    weights = [math.exp(value - maximum) for value in scaled]
    total = math.fsum(weights)
    return [value / total for value in weights]


def sigmoid(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("logit must be finite")
    if value >= 0.0:
        factor = math.exp(-value)
        return 1.0 / (1.0 + factor)
    factor = math.exp(value)
    return factor / (1.0 + factor)


def risk_at_coverage(
    correctness: Sequence[bool],
    scores: Sequence[float],
    target_coverage: float,
) -> float:
    if len(correctness) != len(scores) or not correctness:
        raise ValueError("correctness and scores must be non-empty and aligned")
    if not 0.0 < target_coverage <= 1.0:
        raise ValueError("target coverage must be in (0, 1]")
    if any(not math.isfinite(float(score)) for score in scores):
        raise ValueError("scores must be finite")
    ordered = sorted(range(len(scores)), key=lambda index: (-float(scores[index]), index))
    selected = max(1, math.ceil(target_coverage * len(ordered)))
    prefix = ordered[:selected]
    return 1.0 - math.fsum(1.0 if correctness[index] else 0.0 for index in prefix) / selected


def aurc(correctness: Sequence[bool], scores: Sequence[float]) -> float:
    if len(correctness) != len(scores) or not correctness:
        raise ValueError("correctness and scores must be non-empty and aligned")
    ordered = sorted(range(len(scores)), key=lambda index: (-float(scores[index]), index))
    correct = 0
    risks: list[float] = []
    for rank, index in enumerate(ordered, start=1):
        correct += int(bool(correctness[index]))
        risks.append(1.0 - correct / rank)
    return math.fsum(risks) / len(risks)


def calibration_threshold(scores: Sequence[float], target_coverage: float) -> float:
    if not scores:
        raise ValueError("calibration scores must not be empty")
    if not 0.0 < target_coverage <= 1.0:
        raise ValueError("target coverage must be in (0, 1]")
    ordered = sorted((float(score) for score in scores), reverse=True)
    if any(not math.isfinite(score) for score in ordered):
        raise ValueError("calibration scores must be finite")
    selected = max(1, math.ceil(target_coverage * len(ordered)))
    return ordered[selected - 1]


def paired_bootstrap_difference(
    rows: Sequence[Any],
    metric_a: Callable[[Sequence[Any]], float],
    metric_b: Callable[[Sequence[Any]], float],
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    ci_level: float = CI_LEVEL,
) -> dict[str, float | int]:
    if not rows:
        raise ValueError("paired bootstrap requires rows")
    if replicates < 1000:
        raise ValueError("paired bootstrap requires at least 1000 replicates")
    if not 0.0 < ci_level < 1.0:
        raise ValueError("CI level must be in (0, 1)")
    observed = metric_a(rows) - metric_b(rows)
    rng = random.Random(seed)
    size = len(rows)
    samples: list[float] = []
    for _ in range(replicates):
        resampled = [rows[rng.randrange(size)] for _ in range(size)]
        samples.append(metric_a(resampled) - metric_b(resampled))
    samples.sort()
    alpha = (1.0 - ci_level) / 2.0
    low_index = max(0, min(replicates - 1, math.floor(alpha * replicates)))
    high_index = max(
        0,
        min(replicates - 1, math.ceil((1.0 - alpha) * replicates) - 1),
    )
    return {
        "estimate": observed,
        "ci_low": samples[low_index],
        "ci_high": samples[high_index],
        "ci_level": ci_level,
        "replicates": replicates,
        "seed": seed,
    }


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
