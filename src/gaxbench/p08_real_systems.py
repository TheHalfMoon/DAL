from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.pubmedqa import (
    Decision,
    PubMedQARecord,
    PubMedQASplitManifest,
    RecordEntry,
)
from gaxbench.schema import StrictModel

SG000018_CLOSEOUT_SHA = "54ffad6005e3848058be59870f1fee408073ef55"
PUBMEDQA_PARENT_ROLE_MANIFEST_SHA256 = (
    "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
)
SG000019_TRANSFORM_REVISION = "dal-p08-nested-dev-v0.1"
SG000019_SELECTION_METHOD = "sha256-stratified-largest-remainder-v0.1"
SG000019_TRAIN_COUNT = 360
SG000019_SELECTION_COUNT = 90
SG000019_TRAINING_SEEDS = (0, 1, 2)

_REQUIRED_DECISIONS: tuple[Decision, ...] = ("yes", "no", "maybe")
RequiredSystemID = Literal["gax-paper-candidate", "clinical-encoder", "laya"]
SystemRole = Literal["gax", "baseline", "control"]
ExecutionStatus = Literal["complete", "partial", "blocked"]
EvaluationRole = Literal["development-selection", "calibration"]


class DevelopmentTrainingManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    source_repository: Literal["pubmedqa/pubmedqa"] = "pubmedqa/pubmedqa"
    source_commit: Literal["1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"] = (
        "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"
    )
    source_blob_sha1: Literal["38db7750761c78950ed32303e7545bdaa513390c"] = (
        "38db7750761c78950ed32303e7545bdaa513390c"
    )
    parent_transform_revision: Literal["gax-pqal-v0.1"] = "gax-pqal-v0.1"
    parent_role_manifest_sha256: Literal[
        "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    ] = "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    transform_revision: Literal["dal-p08-nested-dev-v0.1"] = "dal-p08-nested-dev-v0.1"
    selection_method: Literal["sha256-stratified-largest-remainder-v0.1"] = (
        "sha256-stratified-largest-remainder-v0.1"
    )
    train_ids: list[str]
    selection_ids: list[str]
    train_action_counts: dict[Decision, int]
    selection_action_counts: dict[Decision, int]
    training_seeds: list[int] = Field(default_factory=lambda: list(SG000019_TRAINING_SEEDS))
    calibration_training_forbidden: Literal[True] = True
    final_test_training_forbidden: Literal[True] = True
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_manifest(self) -> DevelopmentTrainingManifest:
        if self.train_ids != sorted(set(self.train_ids)):
            raise ValueError("train_ids must be unique and sorted")
        if self.selection_ids != sorted(set(self.selection_ids)):
            raise ValueError("selection_ids must be unique and sorted")
        if len(self.train_ids) != SG000019_TRAIN_COUNT:
            raise ValueError(f"train_ids must contain exactly {SG000019_TRAIN_COUNT} items")
        if len(self.selection_ids) != SG000019_SELECTION_COUNT:
            raise ValueError(
                f"selection_ids must contain exactly {SG000019_SELECTION_COUNT} items"
            )
        if set(self.train_ids) & set(self.selection_ids):
            raise ValueError("train_ids and selection_ids must be disjoint")
        if self.training_seeds != list(SG000019_TRAINING_SEEDS):
            raise ValueError("training_seeds must remain preregistered as [0, 1, 2]")
        _validate_action_counts(self.train_action_counts, SG000019_TRAIN_COUNT, "train")
        _validate_action_counts(
            self.selection_action_counts,
            SG000019_SELECTION_COUNT,
            "selection",
        )
        return self


class ExecutionFailureCounts(StrictModel):
    oom: int = Field(default=0, ge=0)
    timeout: int = Field(default=0, ge=0)
    transport: int = Field(default=0, ge=0)
    interface: int = Field(default=0, ge=0)
    other: int = Field(default=0, ge=0)

    def total(self) -> int:
        return self.oom + self.timeout + self.transport + self.interface + self.other


class RuntimeIdentity(StrictModel):
    os: str = Field(min_length=1)
    python: str = Field(min_length=1)
    processor: str = Field(min_length=1)
    accelerator: str = Field(min_length=1)
    packages: dict[str, str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_packages(self) -> RuntimeIdentity:
        if any(not name or not version for name, version in self.packages.items()):
            raise ValueError("runtime package names and versions must be non-empty")
        return self


class SystemExecutionEvidence(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    system_id: RequiredSystemID
    role: SystemRole
    source_revision: str | None = None
    model_revision: str = Field(min_length=1)
    tokenizer_revision: str | None = None
    adapter_revision: str = Field(min_length=1)
    checkpoint_sha256: str | None = None
    training_seed: int | None = None
    dataset_manifest_sha256: str
    evaluation_role: EvaluationRole
    requested_count: int = Field(gt=0)
    completed_count: int = Field(ge=0)
    failures: ExecutionFailureCounts
    runtime: RuntimeIdentity
    predictions_sha256: str | None = None
    status: ExecutionStatus
    zero_founder_cost: Literal[True] = True
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_evidence(self) -> SystemExecutionEvidence:
        for field_name, value in (
            ("dataset_manifest_sha256", self.dataset_manifest_sha256),
            ("checkpoint_sha256", self.checkpoint_sha256),
            ("predictions_sha256", self.predictions_sha256),
        ):
            if value is not None:
                _require_sha256(value, field_name)

        failed = self.failures.total()
        if self.requested_count != self.completed_count + failed:
            raise ValueError(
                "requested_count must equal completed_count plus all preserved failures"
            )
        if self.status == "complete":
            if failed != 0 or self.completed_count != self.requested_count:
                raise ValueError("complete execution cannot contain failed requests")
            if self.predictions_sha256 is None:
                raise ValueError("complete execution requires predictions_sha256")
        elif self.status == "partial":
            if self.completed_count <= 0 or failed <= 0:
                raise ValueError("partial execution requires both completed and failed requests")
            if self.predictions_sha256 is None:
                raise ValueError("partial execution requires predictions_sha256")
        elif self.completed_count != 0 or failed != self.requested_count:
            raise ValueError("blocked execution must preserve every request as a failure")

        if self.system_id == "gax-paper-candidate":
            if self.role != "gax":
                raise ValueError("gax-paper-candidate must use role='gax'")
            if self.checkpoint_sha256 is None:
                raise ValueError("gax-paper-candidate evidence requires checkpoint_sha256")
            if self.training_seed not in SG000019_TRAINING_SEEDS:
                raise ValueError("gax-paper-candidate must bind a preregistered training seed")
        elif self.role == "gax":
            raise ValueError("only gax-paper-candidate may use the gax role in SG-000019")
        return self


class CheckpointProvenance(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    system_id: Literal["gax-paper-candidate", "clinical-encoder"]
    base_model_id: str = Field(min_length=1)
    base_model_revision: str = Field(min_length=1)
    tokenizer_revision: str = Field(min_length=1)
    development_manifest_sha256: str
    training_recipe_sha256: str
    training_seed: int
    checkpoint_sha256: str
    source_revision: str = Field(min_length=1)
    zero_founder_cost: Literal[True] = True
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_checkpoint(self) -> CheckpointProvenance:
        if self.training_seed not in SG000019_TRAINING_SEEDS:
            raise ValueError("checkpoint seed must be one of the preregistered SG-000019 seeds")
        for field_name, value in (
            ("development_manifest_sha256", self.development_manifest_sha256),
            ("training_recipe_sha256", self.training_recipe_sha256),
            ("checkpoint_sha256", self.checkpoint_sha256),
        ):
            _require_sha256(value, field_name)
        return self


def build_development_training_manifest(
    records: Sequence[RecordEntry],
    parent: PubMedQASplitManifest,
) -> DevelopmentTrainingManifest:
    parent_digest = canonical_json_sha256(parent.model_dump(mode="json"))
    if parent_digest != PUBMEDQA_PARENT_ROLE_MANIFEST_SHA256:
        raise ValueError(
            "parent PubMedQA role manifest does not match the SG-000018 frozen digest"
        )

    by_pmid: dict[str, PubMedQARecord] = {}
    for pmid, record in records:
        if pmid in by_pmid:
            raise ValueError(f"duplicate source PMID {pmid!r}")
        by_pmid[pmid] = record

    development_ids = set(parent.validation_ids)
    missing = sorted(development_ids - set(by_pmid))
    if missing:
        raise ValueError(f"source records are missing development PMIDs: {missing[:5]}")

    groups: dict[Decision, list[str]] = {decision: [] for decision in _REQUIRED_DECISIONS}
    for pmid in parent.validation_ids:
        groups[by_pmid[pmid].final_decision].append(pmid)

    quotas = _selection_quotas({decision: len(ids) for decision, ids in groups.items()})
    selection_ids: list[str] = []
    train_ids: list[str] = []
    train_counts: dict[Decision, int] = {}
    selection_counts: dict[Decision, int] = {}

    for decision in _REQUIRED_DECISIONS:
        ranked = sorted(groups[decision], key=lambda pmid: _rank_key(decision, pmid))
        selection_quota = quotas[decision]
        selected = ranked[:selection_quota]
        trained = ranked[selection_quota:]
        selection_ids.extend(selected)
        train_ids.extend(trained)
        selection_counts[decision] = len(selected)
        train_counts[decision] = len(trained)

    train_set = set(train_ids)
    selection_set = set(selection_ids)
    if train_set | selection_set != development_ids:
        raise ValueError("nested train/selection membership must exactly cover parent development")
    forbidden_ids = set(parent.calibration_ids) | set(parent.test_ids)
    if (train_set | selection_set) & forbidden_ids:
        raise ValueError("nested development split overlaps calibration or sealed final-test rows")

    return DevelopmentTrainingManifest(
        train_ids=sorted(train_ids),
        selection_ids=sorted(selection_ids),
        train_action_counts=train_counts,
        selection_action_counts=selection_counts,
    )


def development_manifest_digest(manifest: DevelopmentTrainingManifest) -> str:
    return canonical_json_sha256(manifest.model_dump(mode="json"))


def execution_evidence_digest(evidence: SystemExecutionEvidence) -> str:
    return canonical_json_sha256(evidence.model_dump(mode="json"))


def checkpoint_provenance_digest(provenance: CheckpointProvenance) -> str:
    return canonical_json_sha256(provenance.model_dump(mode="json"))


def _selection_quotas(counts: dict[Decision, int]) -> dict[Decision, int]:
    if set(counts) != set(_REQUIRED_DECISIONS):
        raise ValueError("action counts must contain exactly yes/no/maybe")
    total = sum(counts.values())
    if total != SG000019_TRAIN_COUNT + SG000019_SELECTION_COUNT:
        raise ValueError("parent development role must contain exactly 450 rows")

    floors: dict[Decision, int] = {}
    remainders: list[tuple[int, int, Decision]] = []
    for tie_break, decision in enumerate(_REQUIRED_DECISIONS):
        numerator = counts[decision] * SG000019_SELECTION_COUNT
        floors[decision] = numerator // total
        remainders.append((numerator % total, -tie_break, decision))

    remaining = SG000019_SELECTION_COUNT - sum(floors.values())
    for _, _, decision in sorted(remainders, reverse=True)[:remaining]:
        floors[decision] += 1
    return floors


def _rank_key(decision: Decision, pmid: str) -> tuple[str, str]:
    material = f"{SG000019_TRANSFORM_REVISION}|{decision}|{pmid}".encode()
    return hashlib.sha256(material).hexdigest(), pmid


def _validate_action_counts(
    counts: dict[Decision, int],
    expected_total: int,
    label: str,
) -> None:
    if set(counts) != set(_REQUIRED_DECISIONS):
        raise ValueError(f"{label}_action_counts must contain exactly yes/no/maybe")
    if any(value < 0 for value in counts.values()):
        raise ValueError(f"{label}_action_counts must be non-negative")
    if sum(counts.values()) != expected_total:
        raise ValueError(f"{label}_action_counts must sum to {expected_total}")


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
