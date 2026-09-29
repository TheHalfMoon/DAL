from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "registry"


def load(name: str) -> dict[str, object]:
    return json.loads((REGISTRY / name).read_text(encoding="utf-8"))


def file_sha256(name: str) -> str:
    return hashlib.sha256((REGISTRY / name).read_bytes()).hexdigest()


def test_qualification_summary_is_bound_to_frozen_evidence() -> None:
    qualification = load("medqabstain_qualification.json")
    hub = load("medqabstain_hub_probe.json")
    parquet = load("medqabstain_parquet_probe.json")
    transform = load("medqabstain_transform_audit.json")
    leakage = load("medqabstain_leakage_audit.json")

    assert qualification["status"] == "blocked"
    assert qualification["paper_evaluation_authorized"] is False
    assert qualification["final_test_access"] == "sealed"
    assert qualification["dataset_revision"] == hub["dataset_revision"]
    assert qualification["dataset_revision"] == parquet["dataset_revision"]
    assert qualification["dataset_revision"] == transform["dataset_revision"]
    assert qualification["dataset_revision"] == leakage["dataset_revision"]
    assert qualification["card_license"] is None
    assert hub["card_license"] is None

    assert qualification["source_row_count"] == parquet["total_rows"]
    assert qualification["source_row_count"] == transform["row_count"]
    assert qualification["source_row_count"] == leakage["row_count"]
    assert qualification["construction_eligible_item_count"] == transform[
        "eligible_item_count"
    ]
    assert qualification["quarantined_item_count"] == transform[
        "quarantined_item_count"
    ]
    assert qualification["final_test_membership_sha256"] == transform[
        "eligible_membership_sha256"
    ]
    assert qualification["quarantine_membership_sha256"] == transform[
        "quarantine_membership_sha256"
    ]

    assert qualification["exact_duplicate_pair_count"] == leakage[
        "exact_duplicate_pair_count"
    ]
    assert qualification["near_duplicate_pair_count"] == leakage[
        "near_duplicate_pair_count"
    ]
    assert qualification["near_cross_component_pair_count"] == leakage[
        "near_cross_component_pair_count"
    ]

    assert qualification["hub_probe_sha256"] == file_sha256(
        "medqabstain_hub_probe.json"
    )
    assert qualification["parquet_probe_sha256"] == file_sha256(
        "medqabstain_parquet_probe.json"
    )
    assert qualification["transform_audit_sha256"] == file_sha256(
        "medqabstain_transform_audit.json"
    )
    assert qualification["leakage_audit_sha256"] == file_sha256(
        "medqabstain_leakage_audit.json"
    )


def test_all_component_outcomes_are_blocked() -> None:
    qualification = load("medqabstain_qualification.json")
    rights = load("medqabstain_component_rights.json")
    outcomes = qualification["component_outcomes"]
    assert isinstance(outcomes, dict)
    assert set(outcomes.values()) == {"blocked"}

    components = rights["components"]
    assert isinstance(components, list)
    by_id = {
        component["component_id"]: component["status"]
        for component in components
        if isinstance(component, dict)
    }
    assert by_id == outcomes
