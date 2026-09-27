from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, HttpUrl, field_validator, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

SG000012_CLOSEOUT_MERGE_SHA = "4ef48a894481abe9100f89a81970cd299138e98d"
SG000012_CLOSEOUT_POST_MAIN_RUN_ID = 36294381495

InventoryStatus = Literal["qualified", "pending", "blocked"]
LicenseStatus = Literal["verified", "ambiguous", "restricted", "unknown"]
Redistribution = Literal["permitted", "restricted", "prohibited", "unknown"]
SourceKind = Literal["github", "huggingface", "other"]
DatasetRole = Literal["development", "calibration", "final-test", "external-validation"]
SystemRole = Literal["gax", "baseline", "control"]
ProtocolStatus = Literal["qualified", "pending"]


class _HasID(Protocol):
    id: str


class SG000012CloseoutGate(StrictModel):
    merge_sha: str
    post_main_run_id: int = Field(gt=0)
    conclusion: Literal["success"]

    @field_validator("merge_sha")
    @classmethod
    def validate_merge_sha(cls, value: str) -> str:
        _require_git_sha(value, "sg000012_closeout.merge_sha")
        return value

    @model_validator(mode="after")
    def validate_canonical_gate(self) -> SG000012CloseoutGate:
        if self.merge_sha != SG000012_CLOSEOUT_MERGE_SHA:
            raise ValueError("SG-000012 closeout merge must match canonical merge")
        if self.post_main_run_id != SG000012_CLOSEOUT_POST_MAIN_RUN_ID:
            raise ValueError("SG-000012 closeout CI run must match canonical post-main run")
        return self


class DatasetInventoryEntry(StrictModel):
    id: str = Field(min_length=1)
    source_kind: SourceKind
    source_url: HttpUrl
    source_revision: str = Field(min_length=1)
    data_revision: str | None = None
    license: str = Field(min_length=1)
    license_status: LicenseStatus
    redistribution: Redistribution
    status: InventoryStatus
    required_for_authorization: bool
    task_family: str = Field(min_length=1)
    allowed_roles: list[DatasetRole] = Field(min_length=1)
    test_labels_sealed: Literal[True] = True
    split_manifest_sha256: str | None = None
    leakage_audit_sha256: str | None = None
    acquisition_revision: str = Field(min_length=1)
    notes: str = Field(min_length=1)
    pending_reason: str | None = None
    blocked_reason: str | None = None

    @field_validator("allowed_roles")
    @classmethod
    def validate_roles(cls, value: list[DatasetRole]) -> list[DatasetRole]:
        if value != sorted(set(value)):
            raise ValueError("allowed_roles must be unique and sorted")
        return value

    @field_validator("split_manifest_sha256", "leakage_audit_sha256")
    @classmethod
    def validate_optional_sha256(cls, value: str | None) -> str | None:
        if value is not None:
            _require_sha256(value, "dataset audit hash")
        return value

    @model_validator(mode="after")
    def validate_status(self) -> DatasetInventoryEntry:
        _validate_status_reasons(self.status, self.pending_reason, self.blocked_reason)
        if self.status == "qualified":
            if self.license_status != "verified":
                raise ValueError("qualified datasets require verified license status")
            if self.split_manifest_sha256 is None or self.leakage_audit_sha256 is None:
                raise ValueError("qualified datasets require split and leakage audit hashes")
            if self.source_kind == "github":
                _require_git_sha(self.source_revision, "qualified GitHub source_revision")
        if self.required_for_authorization and "final-test" not in self.allowed_roles:
            raise ValueError("required datasets must declare a final-test role")
        return self


class SystemInventoryEntry(StrictModel):
    id: str = Field(min_length=1)
    role: SystemRole
    status: InventoryStatus
    required_for_authorization: bool
    source_revision: str | None = None
    model_revision: str | None = None
    tokenizer_revision: str | None = None
    adapter_revision: str = Field(min_length=1)
    training_seeds: list[int] = Field(default_factory=list)
    real_execution_evidence_id: str | None = None
    pending_reason: str | None = None
    blocked_reason: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> SystemInventoryEntry:
        _validate_status_reasons(self.status, self.pending_reason, self.blocked_reason)
        if self.status == "qualified":
            if self.source_revision is None and self.model_revision is None:
                raise ValueError("qualified systems require a source or model revision")
            if self.real_execution_evidence_id is None:
                raise ValueError("qualified systems require real_execution_evidence_id")
            if self.role == "gax":
                if self.model_revision is None:
                    raise ValueError("qualified GAX systems require model_revision")
                if not self.training_seeds:
                    raise ValueError("qualified GAX systems require training_seeds")
        return self


class ProtocolInventory(StrictModel):
    status: ProtocolStatus
    calibration_method: str | None = None
    calibration_split_sha256: str | None = None
    coverage_targets: list[float] = Field(min_length=1)
    ecal_candidate_components: list[str] = Field(min_length=1)
    fhir_representation_candidates: list[str] = Field(min_length=1)
    hardware_protocol_revision: str | None = None
    multiplicity_policy: str | None = None
    pending_reason: str | None = None
    test_tuning_forbidden: Literal[True] = True

    @field_validator("calibration_split_sha256")
    @classmethod
    def validate_optional_sha256(cls, value: str | None) -> str | None:
        if value is not None:
            _require_sha256(value, "calibration split hash")
        return value

    @field_validator("coverage_targets")
    @classmethod
    def validate_coverage_targets(cls, value: list[float]) -> list[float]:
        if value != sorted(set(value)):
            raise ValueError("coverage_targets must be unique and sorted")
        if any(target <= 0.0 or target > 1.0 for target in value):
            raise ValueError("coverage_targets must be in (0, 1]")
        return value

    @field_validator("ecal_candidate_components", "fhir_representation_candidates")
    @classmethod
    def validate_unique_sorted(cls, value: list[str]) -> list[str]:
        if value != sorted(set(value)):
            raise ValueError("candidate lists must be unique and sorted")
        if any(not entry for entry in value):
            raise ValueError("candidate entries must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_status(self) -> ProtocolInventory:
        if self.status == "pending":
            if not self.pending_reason:
                raise ValueError("pending protocol requires pending_reason")
            return self
        if self.pending_reason is not None:
            raise ValueError("qualified protocol must not carry pending_reason")
        required = (
            self.calibration_method,
            self.calibration_split_sha256,
            self.hardware_protocol_revision,
            self.multiplicity_policy,
        )
        if any(value is None for value in required):
            raise ValueError("qualified protocol requires all frozen protocol fields")
        return self


class P08RealInventory(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    inventory_revision: str = Field(min_length=1)
    repo_revision: str
    final_test_access: Literal["sealed"] = "sealed"
    sg000012_closeout: SG000012CloseoutGate
    datasets: list[DatasetInventoryEntry] = Field(min_length=1)
    systems: list[SystemInventoryEntry] = Field(min_length=2)
    protocol: ProtocolInventory

    @field_validator("repo_revision")
    @classmethod
    def validate_repo_revision(cls, value: str) -> str:
        _require_git_sha(value, "repo_revision")
        return value

    @model_validator(mode="after")
    def validate_inventory(self) -> P08RealInventory:
        _require_unique_ids(self.datasets, "dataset")
        _require_unique_ids(self.systems, "system")
        if not any(system.role == "gax" for system in self.systems):
            raise ValueError("inventory requires at least one GAX system")
        if not any(system.role in {"baseline", "control"} for system in self.systems):
            raise ValueError("inventory requires at least one comparison system")
        return self


class InventoryAudit(StrictModel):
    inventory_digest: str
    final_test_access: Literal["sealed"]
    required_dataset_count: int = Field(ge=0)
    required_system_count: int = Field(ge=0)
    blockers: list[str]
    ready_for_authorization: bool

    @field_validator("inventory_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _require_sha256(value, "inventory_digest")
        return value


def load_real_inventory(path: str | Path) -> P08RealInventory:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return P08RealInventory.model_validate(payload)


def inventory_digest(inventory: P08RealInventory) -> str:
    return canonical_json_sha256(inventory.model_dump(mode="json"))


def audit_real_inventory(inventory: P08RealInventory) -> InventoryAudit:
    blockers: list[str] = []
    required_datasets = [entry for entry in inventory.datasets if entry.required_for_authorization]
    required_systems = [entry for entry in inventory.systems if entry.required_for_authorization]

    for entry in required_datasets:
        if entry.status != "qualified":
            blockers.append(f"dataset:{entry.id}:status={entry.status}")
        if entry.license_status != "verified":
            blockers.append(f"dataset:{entry.id}:license={entry.license_status}")
        if entry.split_manifest_sha256 is None:
            blockers.append(f"dataset:{entry.id}:missing-split-manifest")
        if entry.leakage_audit_sha256 is None:
            blockers.append(f"dataset:{entry.id}:missing-leakage-audit")

    for entry in required_systems:
        if entry.status != "qualified":
            blockers.append(f"system:{entry.id}:status={entry.status}")
        if entry.real_execution_evidence_id is None:
            blockers.append(f"system:{entry.id}:missing-real-execution-evidence")

    if inventory.protocol.status != "qualified":
        blockers.append("protocol:status=pending")

    blockers = sorted(set(blockers))
    return InventoryAudit(
        inventory_digest=inventory_digest(inventory),
        final_test_access=inventory.final_test_access,
        required_dataset_count=len(required_datasets),
        required_system_count=len(required_systems),
        blockers=blockers,
        ready_for_authorization=not blockers,
    )


def _validate_status_reasons(
    status: InventoryStatus,
    pending_reason: str | None,
    blocked_reason: str | None,
) -> None:
    if status == "pending":
        if not pending_reason or blocked_reason is not None:
            raise ValueError("pending entries require only pending_reason")
    elif status == "blocked":
        if not blocked_reason or pending_reason is not None:
            raise ValueError("blocked entries require only blocked_reason")
    elif pending_reason is not None or blocked_reason is not None:
        raise ValueError("qualified entries must not carry pending or blocked reasons")


def _require_unique_ids(entries: Sequence[_HasID], kind: str) -> None:
    ids = [entry.id for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{kind} ids must be unique")


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _require_git_sha(value: str, field: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a 40-character lowercase hexadecimal git SHA")
