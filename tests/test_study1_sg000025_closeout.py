from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT = ROOT / "registry" / "study1_sg000025_closeout.json"
PROTOCOL = ROOT / "registry" / "study1_preregistered_protocol_2026-10-02.json"
ROLE_MANIFEST = ROOT / "registry" / "fhir_agentbench_role_manifest.json"
QUALIFICATION = ROOT / "registry" / "fhir_agentbench_qualification.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sg000025_closeout_preserves_sealed_final_boundary() -> None:
    closeout = _load(CLOSEOUT)
    boundary = closeout["sealed_final_boundary"]

    assert closeout["status"] == "closed-canonical"
    assert closeout["training_performed"] is False
    assert closeout["study1_evaluation_performed"] is False
    assert closeout["sealed_final_labels_inspected"] is False
    assert boundary["test_patient_count"] == 40
    assert boundary["test_row_count"] == 173
    assert boundary["test_gold_serialized"] is False
    assert boundary["access"] == "sealed"


def test_sg000025_closeout_binds_protocol_and_role_manifests() -> None:
    closeout = _load(CLOSEOUT)
    protocol_record = closeout["deliverables"][-1]
    boundary = closeout["sealed_final_boundary"]
    role_manifest = _load(ROLE_MANIFEST)
    qualification = _load(QUALIFICATION)

    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == protocol_record["artifact_sha256"]
    assert boundary["role_manifest_sha256"] == qualification["role_manifest_sha256"]
    assert boundary["membership_sha256"] == role_manifest["membership_sha256"]
    assert boundary["test_patient_count"] == role_manifest["test_patient_count"]
    assert boundary["test_row_count"] == role_manifest["test_row_count"]
    assert role_manifest["test_gold_serialized"] is False


def test_sg000025_closeout_chain_is_complete() -> None:
    closeout = _load(CLOSEOUT)
    deliverables = closeout["deliverables"]

    assert [item["pr"] for item in deliverables] == [108, 109, 110, 111, 112, 113]
    assert all(item["merge_sha"] for item in deliverables)
    assert all(item["post_main_gaxbench_run"] > 0 for item in deliverables)
    assert all(item["post_main_manuscript_run"] > 0 for item in deliverables)
    decisions = closeout["frozen_protocol_decisions"]
    assert decisions["primary_comparator"] == "qa-plus-confidence-abstention"
    assert decisions["primary_endpoint"] == "failure-aware-answer-correctness-aurc"
    assert decisions["dal_r_revision_cap"] == 1
