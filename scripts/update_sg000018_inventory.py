from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.p08_inventory import P08RealInventory

NATIVE_SPLIT_SHA = "d64bfdf057afeaae35fb4209a8513dfc48a6c52e2abd08260dbf111afec1474f"
NATIVE_LEAKAGE_SHA = "e4c105bb1315138310f9b10432430fc753f5d0bfa87d8378dad97399a37cb8d8"
NATIVE_MEMBERSHIP_SHA = "7ce6787ef0d9c936cf11b39a13e8d73b8e740e1555ec5167ff6badb1a8b8bdc0"
CALIBRATION_MANIFEST_SHA = "89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230"
NATIVE_DATASET_ID = "gax-native-abstention-pqal"
SG000018_INVENTORY_REVISION = "p08-real-inventory-v0.2-sg000018"
SG000018_REPO_REVISION = "a97bd6b637be2d98ef98758749edf5f197cc97f8"
OPTIONAL_SYSTEM_POLICY_NOTE = (
    "SG-000018 prospectively classifies this system as secondary/optional because its "
    "reproducible zero-founder-cost execution is not required for the primary matched "
    "comparison; this decision predates final-test model results."
)


def _native_dataset() -> dict[str, object]:
    return {
        "id": NATIVE_DATASET_ID,
        "source_kind": "github",
        "source_url": "https://github.com/pubmedqa/pubmedqa",
        "source_revision": "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997",
        "data_revision": f"sha256:{NATIVE_MEMBERSHIP_SHA}",
        "license": "MIT; deterministic paired transform of already-qualified PubMedQA PQA-L",
        "license_status": "verified",
        "redistribution": "permitted",
        "status": "qualified",
        "required_for_authorization": True,
        "task_family": "biomedical-evidence-availability",
        "allowed_roles": ["calibration", "development", "final-test"],
        "test_labels_sealed": True,
        "split_manifest_sha256": NATIVE_SPLIT_SHA,
        "leakage_audit_sha256": NATIVE_LEAKAGE_SHA,
        "acquisition_revision": "gax-native-abstention-pqal-v0.1",
        "notes": (
            "Deterministic evidence-present/evidence-withheld pairs over the canonical PubMedQA "
            "roles. 1000 source items yield 2000 variants: 900 validation, 100 calibration, "
            "1000 sealed test. Abstention is a separate policy output, never a candidate action. "
            "The task measures evidence-availability insufficiency, not generic clinical safety."
        ),
        "pending_reason": None,
        "blocked_reason": None,
    }


def _require_sg000018_semantics(data: dict[str, object]) -> None:
    datasets = data.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("inventory datasets must be a list")

    native_indexes = [
        index
        for index, entry in enumerate(datasets)
        if isinstance(entry, dict) and entry.get("id") == NATIVE_DATASET_ID
    ]
    if len(native_indexes) != 1:
        if len(native_indexes) > 1:
            raise ValueError("native abstention dataset appears more than once")
        raise ValueError("post-SG-000018 inventory is missing the native abstention dataset")

    parent_indexes = [
        index
        for index, entry in enumerate(datasets)
        if isinstance(entry, dict) and entry.get("id") == "pubmedqa-pqal"
    ]
    if len(parent_indexes) != 1:
        raise ValueError("expected exactly one canonical PubMedQA PQA-L dataset")

    native_index = native_indexes[0]
    if datasets[native_index] != _native_dataset():
        raise ValueError("native abstention dataset conflicts with frozen SG-000018 definition")
    if native_index != parent_indexes[0] + 1:
        raise ValueError("native abstention dataset is not adjacent to its PubMedQA parent")

    dataset_by_id = {
        entry.get("id"): entry for entry in datasets if isinstance(entry, dict)
    }
    medagentbench = dataset_by_id.get("medagentbench")
    if not isinstance(medagentbench, dict):
        raise ValueError("post-SG-000018 inventory is missing MedAgentBench")
    if medagentbench.get("required_for_authorization") is not False:
        raise ValueError("MedAgentBench must remain non-authorization-critical after SG-000018")
    if medagentbench.get("official_runtime_required_for_authorization") is not False:
        raise ValueError("MedAgentBench runtime must remain optional after SG-000018")

    medqabstain = dataset_by_id.get("medqabstain")
    if not isinstance(medqabstain, dict):
        raise ValueError("post-SG-000018 inventory is missing MedQAbstain")
    if medqabstain.get("required_for_authorization") is not False:
        raise ValueError("MedQAbstain must remain non-authorization-critical after SG-000018")

    systems = data.get("systems")
    if not isinstance(systems, list):
        raise ValueError("inventory systems must be a list")
    system_by_id = {
        entry.get("id"): entry for entry in systems if isinstance(entry, dict)
    }
    for system_id in ("gax-paper-candidate", "clinical-encoder", "laya"):
        entry = system_by_id.get(system_id)
        if not isinstance(entry, dict) or entry.get("required_for_authorization") is not True:
            raise ValueError(f"{system_id} must remain authorization-critical after SG-000018")
    for system_id in ("clm", "decider", "restricted-logit", "structured-output-llm"):
        entry = system_by_id.get(system_id)
        if not isinstance(entry, dict):
            raise ValueError(f"post-SG-000018 inventory is missing {system_id}")
        if entry.get("required_for_authorization") is not False:
            raise ValueError(f"{system_id} must remain optional after SG-000018")
        pending_reason = str(entry.get("pending_reason") or "")
        if OPTIONAL_SYSTEM_POLICY_NOTE not in pending_reason:
            raise ValueError(f"{system_id} is missing the frozen SG-000018 optional-system policy")

    protocol = data.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("inventory protocol must be an object")
    expected_protocol = {
        "status": "qualified",
        "calibration_method": "temperature-scaling-action+platt-sufficiency-v0.1",
        "calibration_split_sha256": CALIBRATION_MANIFEST_SHA,
        "coverage_targets": [0.5, 0.8, 0.9],
        "hardware_protocol_revision": "p08-hardware-stratified-v0.1",
        "multiplicity_policy": "holm-primary-family-v0.1",
        "pending_reason": None,
        "test_tuning_forbidden": True,
    }
    for field, expected in expected_protocol.items():
        if protocol.get(field) != expected:
            raise ValueError(
                f"post-SG-000018 protocol field {field!r} drifted: expected {expected!r}"
            )


def transform(payload: dict[str, object]) -> dict[str, object]:
    data = json.loads(json.dumps(payload))
    inventory_revision = data.get("inventory_revision")
    if not isinstance(inventory_revision, str):
        raise ValueError("inventory_revision must be a string")

    # Historical migration scripts must never roll a later canonical frontier backwards.
    # If SG-000018 semantics are already frozen and the inventory has advanced, validate those
    # semantics fail-closed and preserve every later field byte-for-byte at the JSON value level.
    if inventory_revision != SG000018_INVENTORY_REVISION:
        datasets = data.get("datasets")
        if isinstance(datasets, list) and any(
            isinstance(entry, dict) and entry.get("id") == NATIVE_DATASET_ID
            for entry in datasets
        ):
            _require_sg000018_semantics(data)
            P08RealInventory.model_validate(data)
            return data

    datasets = data["datasets"]
    assert isinstance(datasets, list)

    native = _native_dataset()
    native_indexes = [
        index
        for index, entry in enumerate(datasets)
        if isinstance(entry, dict) and entry.get("id") == NATIVE_DATASET_ID
    ]
    if len(native_indexes) > 1:
        raise ValueError("native abstention dataset appears more than once")

    parent_indexes = [
        index
        for index, entry in enumerate(datasets)
        if isinstance(entry, dict) and entry.get("id") == "pubmedqa-pqal"
    ]
    if len(parent_indexes) != 1:
        raise ValueError("expected exactly one canonical PubMedQA PQA-L dataset")
    parent_index = parent_indexes[0]

    if native_indexes:
        native_index = native_indexes[0]
        existing = datasets[native_index]
        if existing != native:
            raise ValueError("native abstention dataset conflicts with frozen SG-000018 definition")
        if native_index != parent_index + 1:
            raise ValueError("native abstention dataset is not adjacent to its PubMedQA parent")
    else:
        datasets.insert(parent_index + 1, native)

    for entry in datasets:
        if not isinstance(entry, dict):
            continue
        if entry.get("id") == "medagentbench":
            entry["required_for_authorization"] = False
            entry["official_runtime_required_for_authorization"] = False
            entry["blocked_reason"] = (
                "Public corpus remains qualified but the official external runtime/scorer is "
                "blocked. SG-000018 prospectively makes this benchmark secondary rather than "
                "authorization-critical because its immutable runtime identity/terms are not "
                "reproducible at zero founder cost; no model result informed this decision."
            )
        elif entry.get("id") == "medqabstain":
            entry["required_for_authorization"] = False
            entry["blocked_reason"] = (
                "External MedQAbstain remains blocked because the immutable derived dataset card "
                "exposes no license grant. SG-000018 prospectively replaces it as a paper-required "
                "dependency with gax-native-abstention-pqal; MedQAbstain stays visible as blocked "
                "related evaluation and no model result informed this decision."
            )

    systems = data["systems"]
    assert isinstance(systems, list)
    required_systems = {"gax-paper-candidate", "clinical-encoder", "laya"}
    optional_systems = {"clm", "decider", "restricted-logit", "structured-output-llm"}
    for entry in systems:
        if not isinstance(entry, dict):
            continue
        system_id = entry.get("id")
        if system_id in required_systems:
            entry["required_for_authorization"] = True
        elif system_id in optional_systems:
            entry["required_for_authorization"] = False
            reason = str(entry.get("pending_reason") or "")
            if OPTIONAL_SYSTEM_POLICY_NOTE not in reason:
                entry["pending_reason"] = f"{reason} {OPTIONAL_SYSTEM_POLICY_NOTE}".strip()

    protocol = data["protocol"]
    assert isinstance(protocol, dict)
    protocol.update(
        {
            "status": "qualified",
            "calibration_method": "temperature-scaling-action+platt-sufficiency-v0.1",
            "calibration_split_sha256": CALIBRATION_MANIFEST_SHA,
            "coverage_targets": [0.5, 0.8, 0.9],
            "hardware_protocol_revision": "p08-hardware-stratified-v0.1",
            "multiplicity_policy": "holm-primary-family-v0.1",
            "pending_reason": None,
            "test_tuning_forbidden": True,
        }
    )
    data["inventory_revision"] = SG000018_INVENTORY_REVISION
    data["repo_revision"] = SG000018_REPO_REVISION
    P08RealInventory.model_validate(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = transform(payload)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=False, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
