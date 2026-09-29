from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.p08_inventory import P08RealInventory

NATIVE_SPLIT_SHA = "d64bfdf057afeaae35fb4209a8513dfc48a6c52e2abd08260dbf111afec1474f"
NATIVE_LEAKAGE_SHA = "e4c105bb1315138310f9b10432430fc753f5d0bfa87d8378dad97399a37cb8d8"
NATIVE_MEMBERSHIP_SHA = "7ce6787ef0d9c936cf11b39a13e8d73b8e740e1555ec5167ff6badb1a8b8bdc0"
CALIBRATION_MANIFEST_SHA = "11d347a4763475749e9f8e63532f1b26023d9d8c16c077b5005961c314f9c291"


def transform(payload: dict[str, object]) -> dict[str, object]:
    data = json.loads(json.dumps(payload))
    datasets = data["datasets"]
    assert isinstance(datasets, list)
    if any(isinstance(entry, dict) and entry.get("id") == "gax-native-abstention-pqal" for entry in datasets):
        raise ValueError("native abstention dataset already exists")

    native = {
        "id": "gax-native-abstention-pqal",
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
    insert_at = next(
        index + 1
        for index, entry in enumerate(datasets)
        if isinstance(entry, dict) and entry.get("id") == "pubmedqa-pqal"
    )
    datasets.insert(insert_at, native)

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
            entry["pending_reason"] = (
                reason
                + " SG-000018 prospectively classifies this system as secondary/optional because "
                "its reproducible zero-founder-cost execution is not required for the primary "
                "matched comparison; this decision predates final-test model results."
            ).strip()

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
    data["inventory_revision"] = "p08-real-inventory-v0.2-sg000018"
    data["repo_revision"] = "a97bd6b637be2d98ef98758749edf5f197cc97f8"
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
