from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gaxbench.p08_calibration_execution import (
    AuthorizationCandidate,
    CalibrationEvidence,
    EcalDecisionLedger,
    FhirSelectionEvidence,
)
from gaxbench.provenance import canonical_json_sha256, sha256_file

_MANIFEST = Path("registry/p08_sg000020_execution_manifest.json")
_CALIBRATION = Path("registry/p08_calibration_evidence_sg000020.json")
_ECAL = Path("registry/p08_ecal_selection_ledger_sg000020.json")
_FHIR = Path("registry/p08_fhir_selection_ledger_sg000020.json")
_AUTH = Path("registry/p08_final_test_authorization_candidate_sg000020.json")


def _manifest() -> dict[str, Any]:
    payload = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sg000020_promoted_files_match_post_main_byte_digests() -> None:
    manifest = _manifest()
    assert manifest["grain_id"] == "SG-000020"
    assert manifest["canonical_main"] == (
        "f69eb3ee5b0c0313b10cf8a628f298229b1082ca"
    )
    assert manifest["source_workflow_run_id"] == 36829717808
    assert manifest["source_artifact_id"] == 11147281389
    assert manifest["final_test_access"] == "sealed"
    assert manifest["final_test_rows_used"] == 0
    assert manifest["authorization_can_authorize_inference"] is False
    assert manifest["max_abs_live_calibration_logit_drift"] < manifest[
        "live_drift_fail_closed_ceiling"
    ]

    for entry in manifest["artifacts"].values():
        path = Path(entry["path"])
        assert sha256_file(path) == entry["byte_sha256"]


def test_sg000020_promoted_semantics_are_frozen_and_sealed() -> None:
    manifest = _manifest()
    artifacts = manifest["artifacts"]

    calibration = CalibrationEvidence.model_validate_json(
        _CALIBRATION.read_text(encoding="utf-8")
    )
    calibration_sha = canonical_json_sha256(calibration.model_dump(mode="json"))
    assert calibration_sha == artifacts["calibration_evidence"]["semantic_sha256"]

    ecal = EcalDecisionLedger.model_validate_json(_ECAL.read_text(encoding="utf-8"))
    ecal_sha = canonical_json_sha256(ecal.model_dump(mode="json"))
    assert ecal_sha == artifacts["ecal_selection_ledger"]["semantic_sha256"]

    fhir_payload: dict[str, Any] = json.loads(_FHIR.read_text(encoding="utf-8"))
    assert fhir_payload.pop("fhir_representation_revision") == "gax-fhir-v0.1"
    assert fhir_payload.pop("missing_reference_sha256s") == []
    fhir = FhirSelectionEvidence.model_validate(fhir_payload)
    fhir_sha = canonical_json_sha256(fhir.model_dump(mode="json"))
    assert fhir_sha == artifacts["fhir_selection_ledger"]["semantic_sha256"]
    assert fhir.selected_representation == "canonical-structured"

    authorization = AuthorizationCandidate.model_validate_json(
        _AUTH.read_text(encoding="utf-8")
    )
    auth_sha = canonical_json_sha256(authorization.model_dump(mode="json"))
    assert auth_sha == artifacts["final_test_authorization_candidate"][
        "semantic_sha256"
    ]
    assert authorization.calibration_evidence_sha256 == calibration_sha
    assert authorization.selected_ecal_configuration_sha256 == ecal_sha
    assert authorization.selected_fhir_representation_sha256 == artifacts[
        "fhir_selection_ledger"
    ]["selected_representation_semantic_sha256"]
    assert authorization.final_test_access == "sealed"
    assert authorization.can_authorize_inference is False
    assert authorization.separate_authorization_grain_required is True
