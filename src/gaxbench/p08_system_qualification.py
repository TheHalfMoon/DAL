from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.p08_inventory import P08RealInventory, SystemInventoryEntry
from gaxbench.p08_paper_models import (
    BACKBONE_MODEL_ID,
    BACKBONE_REVISION,
    canonical_training_contract,
    training_contract_digest,
)
from gaxbench.p08_real_systems import (
    SG000019_TRAINING_SEEDS,
    CheckpointProvenance,
    SystemExecutionEvidence,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

SG000019_DEVELOPMENT_MANIFEST_SHA256 = (
    "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
)
SG000019_DEVELOPMENT_LEAKAGE_SHA256 = (
    "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
)
SG000019_PAPER_TRAINING_CONTRACT_SHA256 = training_contract_digest(
    canonical_training_contract()
)
PAPER_MODEL_REVISION = f"contract-sha256:{SG000019_PAPER_TRAINING_CONTRACT_SHA256}"
PAPER_ADAPTER_REVISION = "dal-p08-paper-head-v0.1"
CONTROL_ADAPTER_REVISION = "dal-p08-clinical-control-head-v0.1"
LAYA_SOURCE_REVISION = "3c68ca2ccf6a83640ab80c20379503fe72c772fd"
LAYA_MODEL_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
CLINICAL_MODEL_REVISION = BACKBONE_REVISION

RequiredSystemID = Literal["gax-paper-candidate", "clinical-encoder", "laya"]
ExternalRequiredSystemID = Literal["clinical-encoder", "laya"]


class RequiredModelIdentity(StrictModel):
    system_id: ExternalRequiredSystemID
    role: Literal["baseline", "control"]
    source_revision: str
    model_id: str = Field(min_length=1)
    model_revision: str
    tokenizer_revision: str | None = None
    license: str = Field(min_length=1)
    identity_status: Literal["frozen-not-executed"] = "frozen-not-executed"

    @model_validator(mode="after")
    def validate_identity(self) -> RequiredModelIdentity:
        if self.system_id == "laya":
            expected = {
                "role": "baseline",
                "source_revision": LAYA_SOURCE_REVISION,
                "model_id": "convaiinnovations/laya",
                "model_revision": LAYA_MODEL_REVISION,
                "license": "Apache-2.0",
                "tokenizer_revision": None,
            }
        else:
            expected = {
                "role": "control",
                "source_revision": CLINICAL_MODEL_REVISION,
                "model_id": BACKBONE_MODEL_ID,
                "model_revision": CLINICAL_MODEL_REVISION,
                "license": "MIT",
                "tokenizer_revision": CLINICAL_MODEL_REVISION,
            }
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise ValueError(
                    f"{self.system_id} {field_name} drift: expected {expected_value!r}"
                )
        _require_git_sha(self.model_revision, f"{self.system_id}.model_revision")
        _require_git_sha(self.source_revision, f"{self.system_id}.source_revision")
        return self


class RequiredModelRevisionRegistry(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    identity_policy: Literal["immutable-huggingface-commit-v0.1"] = (
        "immutable-huggingface-commit-v0.1"
    )
    final_test_access: Literal["sealed"] = "sealed"
    systems: list[RequiredModelIdentity]

    @model_validator(mode="after")
    def validate_systems(self) -> RequiredModelRevisionRegistry:
        ids = [system.system_id for system in self.systems]
        if ids != ["laya", "clinical-encoder"]:
            raise ValueError(
                "required model registry must contain laya then clinical-encoder exactly"
            )
        return self

    def by_id(self, system_id: ExternalRequiredSystemID) -> RequiredModelIdentity:
        return next(system for system in self.systems if system.system_id == system_id)


class SystemQualificationBundle(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    system_id: RequiredSystemID
    development_manifest_sha256: Literal[
        "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
    ] = "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
    development_leakage_audit_sha256: Literal[
        "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
    ] = "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
    checkpoints: list[CheckpointProvenance] = Field(default_factory=list)
    executions: list[SystemExecutionEvidence] = Field(min_length=1)
    final_test_access: Literal["sealed"] = "sealed"
    qualification_status: Literal["qualified"] = "qualified"

    @model_validator(mode="after")
    def validate_bundle(self) -> SystemQualificationBundle:
        if self.development_manifest_sha256 != SG000019_DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError("development manifest digest drift")
        if self.development_leakage_audit_sha256 != SG000019_DEVELOPMENT_LEAKAGE_SHA256:
            raise ValueError("development leakage audit digest drift")
        for execution in self.executions:
            if execution.system_id != self.system_id:
                raise ValueError("all executions must belong to the bundle system")
            if execution.dataset_manifest_sha256 != self.development_manifest_sha256:
                raise ValueError("execution dataset digest must match frozen development manifest")
            if execution.evaluation_role != "development-selection":
                raise ValueError("SG-000019 qualification uses development-selection only")
            if execution.status != "complete":
                raise ValueError("qualified systems require complete real execution")
            if execution.requested_count != 90 or execution.completed_count != 90:
                raise ValueError("qualified development-selection execution must be exactly 90/90")
            if execution.failures.total() != 0:
                raise ValueError("qualified execution cannot hide failures")

        if self.system_id == "laya":
            if self.checkpoints:
                raise ValueError(
                    "zero-shot Laya qualification must not invent training checkpoints"
                )
            if len(self.executions) != 1:
                raise ValueError("Laya requires exactly one complete frozen-model execution")
            execution = self.executions[0]
            if execution.role != "baseline":
                raise ValueError("Laya execution must use baseline role")
            if execution.source_revision != LAYA_SOURCE_REVISION:
                raise ValueError("Laya execution source revision drift")
            if execution.model_revision != LAYA_MODEL_REVISION:
                raise ValueError("Laya execution model revision drift")
            if execution.training_seed is not None or execution.checkpoint_sha256 is not None:
                raise ValueError("Laya zero-shot execution must not carry training provenance")
            return self

        required_seeds = list(SG000019_TRAINING_SEEDS)
        checkpoint_seeds = sorted(checkpoint.training_seed for checkpoint in self.checkpoints)
        execution_seeds = sorted(
            execution.training_seed
            for execution in self.executions
            if execution.training_seed is not None
        )
        if checkpoint_seeds != required_seeds:
            raise ValueError("trainable qualification requires checkpoint seeds [0, 1, 2]")
        if execution_seeds != required_seeds or len(self.executions) != 3:
            raise ValueError("trainable qualification requires one complete execution per seed")

        checkpoint_by_seed = {
            checkpoint.training_seed: checkpoint for checkpoint in self.checkpoints
        }
        checkpoint_sources = {checkpoint.source_revision for checkpoint in self.checkpoints}
        execution_sources = {execution.source_revision for execution in self.executions}
        if len(checkpoint_sources) != 1 or checkpoint_sources != execution_sources:
            raise ValueError("trainable checkpoint/execution source revision drift")

        for checkpoint in self.checkpoints:
            if checkpoint.base_model_id != BACKBONE_MODEL_ID:
                raise ValueError("trainable checkpoint base model id drift")
            if checkpoint.base_model_revision != BACKBONE_REVISION:
                raise ValueError("trainable checkpoint base model revision drift")
            if checkpoint.tokenizer_revision != BACKBONE_REVISION:
                raise ValueError("trainable checkpoint tokenizer revision drift")
            if checkpoint.training_recipe_sha256 != SG000019_PAPER_TRAINING_CONTRACT_SHA256:
                raise ValueError("trainable checkpoint training contract digest drift")

        for execution in self.executions:
            if execution.training_seed is None:
                raise ValueError("trainable execution requires training_seed")
            checkpoint = checkpoint_by_seed[execution.training_seed]
            if execution.checkpoint_sha256 != checkpoint.checkpoint_sha256:
                raise ValueError("execution checkpoint digest must match checkpoint provenance")
            if execution.tokenizer_revision != BACKBONE_REVISION:
                raise ValueError("trainable execution tokenizer revision drift")
            if execution.source_revision != checkpoint.source_revision:
                raise ValueError("execution source revision must match checkpoint provenance")

        if self.system_id == "clinical-encoder":
            for checkpoint in self.checkpoints:
                if checkpoint.system_id != "clinical-encoder":
                    raise ValueError("clinical-encoder bundle contains foreign checkpoint")
            for execution in self.executions:
                if execution.role != "control":
                    raise ValueError("clinical-encoder execution must use control role")
                if execution.model_revision != CLINICAL_MODEL_REVISION:
                    raise ValueError("clinical-encoder execution model revision drift")
                if execution.adapter_revision != CONTROL_ADAPTER_REVISION:
                    raise ValueError("clinical-encoder adapter revision drift")
        else:
            for checkpoint in self.checkpoints:
                if checkpoint.system_id != "gax-paper-candidate":
                    raise ValueError("paper-candidate bundle contains foreign checkpoint")
            for execution in self.executions:
                if execution.role != "gax":
                    raise ValueError("paper-candidate execution must use gax role")
                if execution.model_revision != PAPER_MODEL_REVISION:
                    raise ValueError("paper-candidate model revision drift")
                if execution.adapter_revision != PAPER_ADAPTER_REVISION:
                    raise ValueError("paper-candidate adapter revision drift")
        return self


def load_required_model_registry(path: str | Path) -> RequiredModelRevisionRegistry:
    return RequiredModelRevisionRegistry.model_validate(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def load_qualification_bundle(path: str | Path) -> SystemQualificationBundle:
    return SystemQualificationBundle.model_validate(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def qualification_bundle_digest(bundle: SystemQualificationBundle) -> str:
    return canonical_json_sha256(bundle.model_dump(mode="json"))


def validate_inventory_qualification(
    inventory: P08RealInventory,
    registry: RequiredModelRevisionRegistry,
    bundles: dict[RequiredSystemID, SystemQualificationBundle],
) -> None:
    required_entries = {
        entry.id: entry for entry in inventory.systems if entry.required_for_authorization
    }
    expected_ids = {"gax-paper-candidate", "clinical-encoder", "laya"}
    if set(required_entries) != expected_ids:
        raise ValueError(
            "SG-000019 requires exactly gax-paper-candidate, clinical-encoder, and laya"
        )

    for raw_system_id, entry in required_entries.items():
        system_id: RequiredSystemID
        if raw_system_id == "gax-paper-candidate":
            system_id = "gax-paper-candidate"
        elif raw_system_id == "clinical-encoder":
            system_id = "clinical-encoder"
        elif raw_system_id == "laya":
            system_id = "laya"
        else:  # pragma: no cover - guarded by set equality above
            raise ValueError(f"unexpected required system {raw_system_id!r}")

        bundle = bundles.get(system_id)
        if entry.status == "qualified":
            if bundle is None:
                raise ValueError(
                    f"system {system_id} cannot be qualified without a qualification bundle"
                )
            _validate_qualified_entry(entry, bundle, registry)
        elif entry.real_execution_evidence_id is not None:
            raise ValueError(
                f"unqualified required system {system_id} must not carry promotion evidence id"
            )


def _validate_qualified_entry(
    entry: SystemInventoryEntry,
    bundle: SystemQualificationBundle,
    registry: RequiredModelRevisionRegistry,
) -> None:
    if entry.id != bundle.system_id:
        raise ValueError("inventory system and qualification bundle id mismatch")
    expected_evidence_id = f"sha256:{qualification_bundle_digest(bundle)}"
    if entry.real_execution_evidence_id != expected_evidence_id:
        raise ValueError("inventory real_execution_evidence_id does not bind the bundle digest")

    if entry.id in {"gax-paper-candidate", "clinical-encoder"}:
        if entry.training_seeds != list(SG000019_TRAINING_SEEDS):
            raise ValueError("qualified trainable systems must bind seeds [0, 1, 2]")
    elif entry.training_seeds:
        raise ValueError("qualified Laya must not invent training seeds")

    execution_revisions = {execution.model_revision for execution in bundle.executions}
    if len(execution_revisions) != 1 or entry.model_revision not in execution_revisions:
        raise ValueError("inventory model_revision must match all qualified executions")
    execution_adapters = {execution.adapter_revision for execution in bundle.executions}
    if len(execution_adapters) != 1 or entry.adapter_revision not in execution_adapters:
        raise ValueError("inventory adapter_revision must match all qualified executions")
    execution_sources = {execution.source_revision for execution in bundle.executions}
    if len(execution_sources) != 1 or entry.source_revision not in execution_sources:
        raise ValueError("inventory source_revision must match all qualified executions")

    if entry.id == "laya":
        identity = registry.by_id("laya")
        if entry.source_revision != identity.source_revision:
            raise ValueError("Laya inventory source revision drift")
        if entry.model_revision != identity.model_revision:
            raise ValueError("Laya inventory model revision drift")
    elif entry.id == "clinical-encoder":
        identity = registry.by_id("clinical-encoder")
        if entry.model_revision != identity.model_revision:
            raise ValueError("clinical-encoder inventory model revision drift")
        if entry.tokenizer_revision != identity.tokenizer_revision:
            raise ValueError("clinical-encoder inventory tokenizer revision drift")
    elif entry.model_revision != PAPER_MODEL_REVISION:
        raise ValueError("paper-candidate inventory model revision drift")


def _require_git_sha(value: str, field_name: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 40-character lowercase hexadecimal git SHA")
