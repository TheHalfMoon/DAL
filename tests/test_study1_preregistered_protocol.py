from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "registry" / "study1_preregistered_protocol_2026-10-02.json"
FHIR_QUALIFICATION = ROOT / "registry" / "fhir_agentbench_qualification.json"
FHIR_ROLE_MANIFEST = ROOT / "registry" / "fhir_agentbench_role_manifest.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_study1_protocol_keeps_fhir_final_split_sealed() -> None:
    protocol = _load(PROTOCOL)
    qualification = _load(FHIR_QUALIFICATION)
    role_manifest = _load(FHIR_ROLE_MANIFEST)

    final_split = protocol["final_split"]
    assert isinstance(final_split, dict)
    assert protocol["final_test_access"] == "sealed"
    assert final_split["access"] == "sealed"
    assert final_split["test_gold_serialized"] is False
    assert final_split["test_patient_count"] == 40
    assert final_split["test_row_count"] == 173
    assert final_split["role_manifest_sha256"] == qualification["role_manifest_sha256"]
    assert final_split["membership_sha256"] == role_manifest["membership_sha256"]


def test_study1_protocol_freezes_required_baseline_classes() -> None:
    protocol = _load(PROTOCOL)
    baselines = protocol["mandatory_baselines"]
    assert isinstance(baselines, list)
    baseline_ids = {item["id"] for item in baselines}
    assert baseline_ids == {
        "B0-QA",
        "B1-QA-CAL",
        "B2-QA-CONF-ABSTAIN",
        "B3-QA-DAL",
        "B4-QA-DAL-R",
    }
    dal_r = next(item for item in baselines if item["id"] == "B4-QA-DAL-R")
    assert dal_r["revision_cap"] == 1


def test_study1_protocol_freezes_primary_analysis() -> None:
    protocol = _load(PROTOCOL)
    endpoint = protocol["primary_endpoint"]
    statistics = protocol["statistical_plan"]
    assert endpoint["name"] == "answer-correctness AURC"
    assert endpoint["fixed_final_denominator"] == 173
    assert statistics["independence_unit"] == "patient"
    assert statistics["bootstrap_replications"] == 10_000
    assert statistics["bootstrap_seed"] == 20261002


def test_study1_protocol_freezes_stage_order_and_revision_budget() -> None:
    protocol = _load(PROTOCOL)
    stages = protocol["development_stages"]
    assert [stage["id"] for stage in stages] == [
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
    ]
    action_semantics = protocol["action_semantics"]
    assert action_semantics["revision_cap"] == 1
    assert protocol["final_access_authorization"]["default"] == "sealed"


def test_study1_protocol_keeps_primary_comparator_difficult() -> None:
    protocol = _load(PROTOCOL)
    baselines = protocol["mandatory_baselines"]
    primary = [item for item in baselines if item.get("primary_comparator")]
    assert [item["id"] for item in primary] == ["B2-QA-CONF-ABSTAIN"]
    assert "B2-QA-CONF-ABSTAIN" in protocol["primary_endpoint"]["comparison"]
