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
    assert inventory.inventory_revision == "p08-real-inventory-v0.1"
    assert inventory.sg000012_closeout.merge_sha == SG000012_CLOSEOUT_MERGE_SHA
    assert inventory.sg000012_closeout.post_main_run_id == SG000012_CLOSEOUT_POST_MAIN_RUN_ID
    pubmedqa = next(entry for entry in inventory.datasets if entry.id == "pubmedqa-pqal")
    assert pubmedqa.status == "qualified"
    assert pubmedqa.split_manifest_sha256 == (
        "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    )
    assert pubmedqa.leakage_audit_sha256 == (
        "7a8a576c0485b351190b58a49ac6662e614470b5b414a0d437ca761da3e76443"
    )
    assert any(entry.id == "gax-paper-candidate" for entry in inventory.systems)


def test_repository_inventory_is_not_ready_for_authorization() -> None:
    report = audit_real_inventory(load_real_inventory(INVENTORY))
    assert report.ready_for_authorization is False
    assert report.final_test_access == "sealed"
    assert "protocol:status=pending" in report.blockers
    assert "dataset:pubmedqa-pqal:status=pending" not in report.blockers
    assert "dataset:fhir-agentbench:status=pending" in report.blockers
    assert "system:gax-paper-candidate:status=pending" in report.blockers


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
