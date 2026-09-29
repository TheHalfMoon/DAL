from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_inventory import (
    SG000012_CLOSEOUT_MERGE_SHA,
    SG000012_CLOSEOUT_POST_MAIN_RUN_ID,
    DatasetInventoryEntry,
    P08RealInventory,
    ProtocolInventory,
    SystemInventoryEntry,
    audit_real_inventory,
    inventory_digest,
    load_real_inventory,
)

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "registry" / "p08_real_inventory.json"


def test_repository_inventory_is_valid_and_sealed() -> None:
    inventory = load_real_inventory(INVENTORY)
    assert inventory.final_test_access == "sealed"
    assert inventory.inventory_revision == "p08-real-inventory-v0.3-sg000019-laya"
    assert inventory.sg000012_closeout.merge_sha == SG000012_CLOSEOUT_MERGE_SHA
    assert inventory.sg000012_closeout.post_main_run_id == SG000012_CLOSEOUT_POST_MAIN_RUN_ID

    pubmedqa = next(entry for entry in inventory.datasets if entry.id == "pubmedqa-pqal")
    assert pubmedqa.status == "qualified"
    assert pubmedqa.required_for_authorization is True
    assert pubmedqa.split_manifest_sha256 == (
        "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    )
    assert pubmedqa.leakage_audit_sha256 == (
        "7a8a576c0485b351190b58a49ac6662e614470b5b414a0d437ca761da3e76443"
    )

    native = next(
        entry for entry in inventory.datasets if entry.id == "gax-native-abstention-pqal"
    )
    assert native.status == "qualified"
    assert native.required_for_authorization is True
    assert native.allowed_roles == ["calibration", "development", "final-test"]
    assert native.split_manifest_sha256 == (
        "d64bfdf057afeaae35fb4209a8513dfc48a6c52e2abd08260dbf111afec1474f"
    )
    assert native.leakage_audit_sha256 == (
        "e4c105bb1315138310f9b10432430fc753f5d0bfa87d8378dad97399a37cb8d8"
    )

    fhir = next(entry for entry in inventory.datasets if entry.id == "fhir-agentbench")
    assert fhir.status == "qualified"
    assert fhir.required_for_authorization is True
    assert fhir.test_labels_sealed is True
    assert fhir.split_manifest_sha256 == (
        "7065cede39bdfea3db33d025687210f30f26683a38063f7150a807cd89f5e76c"
    )
    assert fhir.leakage_audit_sha256 == (
        "1e45851f334cf5ab0522ac96766080566cb7609462d6917d625814a5612c6490"
    )

    medagentbench = next(
        entry for entry in inventory.datasets if entry.id == "medagentbench"
    )
    assert medagentbench.status == "blocked"
    assert medagentbench.required_for_authorization is False
    assert medagentbench.corpus_status == "qualified"
    assert medagentbench.official_runtime_status == "blocked"
    assert medagentbench.official_runtime_required_for_authorization is False
    assert medagentbench.allowed_roles == ["final-test"]
    assert medagentbench.split_manifest_sha256 == (
        "daf963c8f1c13e974a4608a1cf222505f0013ed81a15616e129a106cb9a6dcb1"
    )
    assert medagentbench.leakage_audit_sha256 == (
        "b1fa338c510b4787e33cb40c525d5e2ca00154eae97b86c93c5a419abf143356"
    )

    medqabstain = next(entry for entry in inventory.datasets if entry.id == "medqabstain")
    assert medqabstain.status == "blocked"
    assert medqabstain.source_kind == "huggingface"
    assert medqabstain.source_revision == "d215847217bb5f4124b9110379d33b9eb2f8d3f7"
    assert medqabstain.allowed_roles == ["final-test"]
    assert medqabstain.required_for_authorization is False
    assert medqabstain.split_manifest_sha256 == (
        "07056674a688d64468fd2fbeb815828605df1501f92ff0e31a255700bbf3d3f6"
    )
    assert medqabstain.leakage_audit_sha256 == (
        "af8ac0c084fa96195a179b405d7823d9d8d89ce4211d854addb461f635f078f4"
    )

    assert inventory.protocol.status == "qualified"
    assert inventory.protocol.pending_reason is None
    assert inventory.protocol.calibration_method == (
        "temperature-scaling-action+platt-sufficiency-v0.1"
    )
    assert inventory.protocol.hardware_protocol_revision == "p08-hardware-stratified-v0.1"
    assert inventory.protocol.multiplicity_policy == "holm-primary-family-v0.1"
    assert any(entry.id == "gax-paper-candidate" for entry in inventory.systems)

    laya = next(entry for entry in inventory.systems if entry.id == "laya")
    assert laya.status == "qualified"
    assert laya.required_for_authorization is True
    assert laya.source_revision == "3c68ca2ccf6a83640ab80c20379503fe72c772fd"
    assert laya.model_revision == "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
    assert laya.adapter_revision == "dal-p08-laya-pubmedqa-choice-v0.1"
    assert laya.training_seeds == []
    assert laya.real_execution_evidence_id == (
        "sha256:b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534"
    )


def test_repository_inventory_is_not_ready_for_authorization() -> None:
    report = audit_real_inventory(load_real_inventory(INVENTORY))
    assert report.ready_for_authorization is False
    assert report.final_test_access == "sealed"
    assert report.required_dataset_count == 3
    assert report.required_system_count == 3
    assert "protocol:status=pending" not in report.blockers
    assert not any(blocker.startswith("dataset:") for blocker in report.blockers)
    assert "system:gax-paper-candidate:status=pending" in report.blockers
    assert "system:gax-paper-candidate:missing-real-execution-evidence" in report.blockers
    assert "system:clinical-encoder:status=pending" in report.blockers
    assert "system:clinical-encoder:missing-real-execution-evidence" in report.blockers
    assert not any(blocker.startswith("system:laya:") for blocker in report.blockers)


def test_inventory_digest_is_deterministic() -> None:
    inventory = load_real_inventory(INVENTORY)
    assert inventory_digest(inventory) == inventory_digest(inventory)
    assert len(inventory_digest(inventory)) == 64


def test_inventory_rejects_noncanonical_sg000012_gate() -> None:
    inventory = load_real_inventory(INVENTORY)
    payload = inventory.model_dump(mode="json")
    payload["sg000012_closeout"]["merge_sha"] = "0" * 40
    with pytest.raises(ValidationError, match="must match canonical merge"):
        P08RealInventory.model_validate(payload)


def test_pending_dataset_requires_reason() -> None:
    with pytest.raises(ValidationError, match="pending entries require only pending_reason"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="revision",
            license="MIT",
            license_status="verified",
            redistribution="permitted",
            status="pending",
            required_for_authorization=False,
            task_family="unit",
            allowed_roles=["development"],
            acquisition_revision="unit-v1",
            notes="unit fixture",
        )


def test_qualified_dataset_requires_hashes() -> None:
    with pytest.raises(ValidationError, match="split and leakage audit hashes"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="revision",
            license="MIT",
            license_status="verified",
            redistribution="permitted",
            status="qualified",
            required_for_authorization=False,
            task_family="unit",
            allowed_roles=["development"],
            acquisition_revision="unit-v1",
            notes="unit fixture",
        )


def test_qualified_github_dataset_requires_commit_sha() -> None:
    with pytest.raises(ValidationError, match="qualified GitHub source_revision"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="mutable-main",
            license="MIT",
            license_status="verified",
            redistribution="permitted",
            status="qualified",
            required_for_authorization=False,
            task_family="unit",
            allowed_roles=["development"],
            split_manifest_sha256="1" * 64,
            leakage_audit_sha256="2" * 64,
            acquisition_revision="unit-v1",
            notes="unit fixture",
        )


def test_required_dataset_must_declare_final_test_role() -> None:
    with pytest.raises(ValidationError, match="required datasets must declare a final-test role"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="revision",
            license="MIT",
            license_status="verified",
            redistribution="permitted",
            status="pending",
            required_for_authorization=True,
            task_family="unit",
            allowed_roles=["development"],
            acquisition_revision="unit-v1",
            notes="unit fixture",
            pending_reason="not ready",
        )


def test_compound_dataset_requires_all_component_fields() -> None:
    with pytest.raises(ValidationError, match="compound dataset qualification requires"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="0" * 40,
            license="MIT",
            license_status="verified",
            redistribution="restricted",
            status="blocked",
            required_for_authorization=True,
            task_family="unit",
            allowed_roles=["final-test"],
            split_manifest_sha256="1" * 64,
            leakage_audit_sha256="2" * 64,
            acquisition_revision="unit-v1",
            notes="qualified corpus with blocked runtime",
            blocked_reason="runtime unavailable",
            corpus_status="qualified",
        )


def test_required_blocked_runtime_prevents_aggregate_qualification() -> None:
    with pytest.raises(ValidationError, match="required official runtime"):
        DatasetInventoryEntry(
            id="x",
            source_kind="github",
            source_url="https://github.com/example/example",
            source_revision="0" * 40,
            license="MIT",
            license_status="verified",
            redistribution="restricted",
            status="qualified",
            required_for_authorization=True,
            task_family="unit",
            allowed_roles=["final-test"],
            split_manifest_sha256="1" * 64,
            leakage_audit_sha256="2" * 64,
            acquisition_revision="unit-v1",
            notes="unit fixture",
            corpus_status="qualified",
            official_runtime_status="blocked",
            official_runtime_required_for_authorization=True,
            official_runtime_blocked_reason="runtime unavailable",
        )


def test_qualified_system_requires_real_execution_evidence() -> None:
    with pytest.raises(ValidationError, match="real_execution_evidence_id"):
        SystemInventoryEntry(
            id="x",
            role="baseline",
            status="qualified",
            required_for_authorization=True,
            source_revision="revision",
            adapter_revision="adapter",
        )


def test_qualified_gax_requires_checkpoint_revision() -> None:
    with pytest.raises(ValidationError, match="qualified GAX systems require model_revision"):
        SystemInventoryEntry(
            id="gax",
            role="gax",
            status="qualified",
            required_for_authorization=True,
            source_revision="source",
            adapter_revision="adapter",
            training_seeds=[1],
            real_execution_evidence_id="run-1",
        )


def test_qualified_gax_requires_training_seeds() -> None:
    with pytest.raises(ValidationError, match="qualified GAX systems require training_seeds"):
        SystemInventoryEntry(
            id="gax",
            role="gax",
            status="qualified",
            required_for_authorization=True,
            source_revision="source",
            model_revision="checkpoint",
            adapter_revision="adapter",
            real_execution_evidence_id="run-1",
        )


def test_pending_protocol_requires_reason() -> None:
    with pytest.raises(ValidationError, match="pending protocol requires pending_reason"):
        ProtocolInventory(
            status="pending",
            coverage_targets=[0.8],
            ecal_candidate_components=["evidence"],
            fhir_representation_candidates=["canonical-structured"],
        )


def test_candidate_lists_must_be_sorted() -> None:
    with pytest.raises(ValidationError, match="candidate lists must be unique and sorted"):
        ProtocolInventory(
            status="pending",
            coverage_targets=[0.8],
            ecal_candidate_components=["z", "a"],
            fhir_representation_candidates=["canonical-structured"],
            pending_reason="not frozen",
        )


def test_duplicate_inventory_ids_are_rejected() -> None:
    inventory = load_real_inventory(INVENTORY)
    payload = inventory.model_dump(mode="json")
    payload["datasets"].append(payload["datasets"][0])
    with pytest.raises(ValidationError, match="dataset ids must be unique"):
        P08RealInventory.model_validate(payload)
