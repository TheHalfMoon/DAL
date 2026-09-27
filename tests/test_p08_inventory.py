from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_inventory import (
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
    assert any(entry.id == "pubmedqa-pqal" for entry in inventory.datasets)
    assert any(entry.id == "gax-paper-candidate" for entry in inventory.systems)


def test_repository_inventory_is_not_ready_for_authorization() -> None:
    report = audit_real_inventory(load_real_inventory(INVENTORY))
    assert report.ready_for_authorization is False
    assert report.final_test_access == "sealed"
    assert "protocol:status=pending" in report.blockers
    assert "dataset:pubmedqa-pqal:status=pending" in report.blockers
    assert "system:gax-paper-candidate:status=pending" in report.blockers


def test_inventory_digest_is_deterministic() -> None:
    inventory = load_real_inventory(INVENTORY)
    assert inventory_digest(inventory) == inventory_digest(inventory)
    assert len(inventory_digest(inventory)) == 64


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
