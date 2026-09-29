from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gaxbench.provenance import canonical_json_sha256
from scripts.update_sg000018_inventory import transform

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "registry" / "p08_real_inventory.json"
CALIBRATION_MANIFEST = ROOT / "registry" / "p08_calibration_manifest_sg000018.json"
ROLE_MANIFESTS = {
    "pubmedqa-pqal": ROOT / "registry" / "pubmedqa_pqal_split_manifest.json",
    "gax-native-abstention-pqal": ROOT / "registry" / "gax_native_abstention_role_manifest.json",
    "fhir-agentbench": ROOT / "registry" / "fhir_agentbench_role_manifest.json",
}


def _payload() -> dict[str, object]:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_sg000018_inventory_transform_is_idempotent() -> None:
    payload = _payload()
    assert transform(payload) == payload
    assert transform(transform(payload)) == payload


def test_sg000018_inventory_transform_fails_closed_on_native_conflict() -> None:
    payload = _payload()
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    native = next(
        entry
        for entry in datasets
        if isinstance(entry, dict) and entry.get("id") == "gax-native-abstention-pqal"
    )
    native["source_revision"] = "tampered"

    with pytest.raises(ValueError, match="conflicts with frozen SG-000018 definition"):
        transform(payload)


def test_sg000018_inventory_transform_rejects_duplicate_native_dataset() -> None:
    payload = _payload()
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    native = next(
        entry
        for entry in datasets
        if isinstance(entry, dict) and entry.get("id") == "gax-native-abstention-pqal"
    )
    datasets.append(copy.deepcopy(native))

    with pytest.raises(ValueError, match="appears more than once"):
        transform(payload)


def test_sg000018_calibration_manifest_is_reproducibly_bound() -> None:
    inventory = _payload()
    protocol = inventory["protocol"]
    datasets = inventory["datasets"]
    assert isinstance(protocol, dict)
    assert isinstance(datasets, list)

    manifest = json.loads(CALIBRATION_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["final_test_access"] == "sealed"
    assert manifest["test_tuning_forbidden"] is True
    assert canonical_json_sha256(manifest) == protocol["calibration_split_sha256"]

    dataset_by_id = {
        entry["id"]: entry
        for entry in datasets
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    assert [source["dataset_id"] for source in manifest["sources"]] == [
        "pubmedqa-pqal",
        "gax-native-abstention-pqal",
        "fhir-agentbench",
    ]
    assert sum(source["calibration_item_count"] for source in manifest["sources"]) == 491

    for source in manifest["sources"]:
        dataset_id = source["dataset_id"]
        role_manifest_sha = source["role_manifest_sha256"]
        assert role_manifest_sha == dataset_by_id[dataset_id]["split_manifest_sha256"]
        role_manifest = json.loads(ROLE_MANIFESTS[dataset_id].read_text(encoding="utf-8"))
        assert canonical_json_sha256(role_manifest) == role_manifest_sha
