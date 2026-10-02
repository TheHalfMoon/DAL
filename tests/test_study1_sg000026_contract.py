from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry" / "study1_sg000026_contract.json"
PROTOCOL = ROOT / "registry" / "study1_preregistered_protocol_2026-10-02.json"
ROLE_MANIFEST = ROOT / "registry" / "fhir_agentbench_role_manifest.json"
QUALIFICATION = ROOT / "registry" / "fhir_agentbench_qualification.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repository_text_sha256(path: Path) -> str:
    canonical_lf = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(canonical_lf.encode("utf-8")).hexdigest()


def test_sg000026_binds_canonical_protocol_and_dependency() -> None:
    contract = _load(CONTRACT)
    dependency = contract["canonical_dependency"]

    assert contract["grain"] == "SG-000026"
    assert contract["study_stage"] == "D2"
    assert contract["status"] == "active-governance-only"
    assert dependency["sg000025_closeout_merge"] == "16682ea9dff2f3ccfb0ed818b352eaaa0ccdc167"
    assert dependency["post_main_gaxbench_run"] == 37073433197
    assert dependency["post_main_manuscript_run"] == 37073433188
    assert _repository_text_sha256(PROTOCOL) == dependency["protocol_sha256"]


def test_sg000026_preserves_sealed_final_firewall() -> None:
    contract = _load(CONTRACT)
    firewall = contract["sealed_final_firewall"]
    role_manifest = _load(ROLE_MANIFEST)
    qualification = _load(QUALIFICATION)

    assert firewall["test_patients"] == role_manifest["test_patient_count"] == 40
    assert firewall["test_rows"] == role_manifest["test_row_count"] == 173
    assert firewall["membership_sha256"] == role_manifest["membership_sha256"]
    assert firewall["role_manifest_sha256"] == qualification["role_manifest_sha256"]
    assert firewall["test_gold_serialized"] is False
    assert firewall["access"] == "sealed"
    assert firewall["d2_use"] == "forbidden"


def test_sg000026_limits_d2_to_b0_b1_b2_and_development_roles() -> None:
    contract = _load(CONTRACT)
    baselines = contract["mandatory_baselines"]
    roles = contract["fhir_development_roles"]
    forbidden = set(contract["scope"]["forbidden"])

    assert [item["id"] for item in baselines] == ["B0-QA", "B1-QA-CAL", "B2-QA-CONF-ABSTAIN"]
    assert {item["base_answer_identity"] for item in baselines} == {"shared"}
    assert roles["calibration_rows"] == 341
    assert roles["validation_rows"] == 1122
    assert "final base-model selection" in forbidden
    assert "training or fine-tuning" in forbidden
    assert "final calibration-function fitting" in forbidden
    assert "sealed-final access or inference" in forbidden


def test_sg000026_required_review_evidence_excludes_disallowed_services() -> None:
    contract = _load(CONTRACT)
    qualification = contract["qualification"]

    assert qualification["alibaba_opencodereview"] == "required"
    assert qualification["typesafe_jev"] == "required"
    assert qualification["manuscript"] == "required"
    assert set(qualification["not_evidence"]) == {"Cubic", "Qodo", "CodeRabbit"}
