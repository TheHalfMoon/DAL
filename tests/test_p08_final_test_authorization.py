from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_final_test_authorization import (
    FinalTestAuthorizationArtifact,
    build_final_test_authorization,
    load_final_test_authorization,
)

ROOT = Path(__file__).parents[1]
AUTHORIZATION = ROOT / "registry" / "p08_final_test_authorization_sg000021.json"


def test_canonical_authorization_rebuilds_from_frozen_evidence() -> None:
    canonical = load_final_test_authorization(AUTHORIZATION)
    rebuilt = build_final_test_authorization(ROOT)

    assert rebuilt == canonical
    assert rebuilt.authorization_digest == (
        "626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de"
    )
    assert rebuilt.state == "authorized-for-next-grain"
    assert rebuilt.authorized_grain == "SG-000022"
    assert rebuilt.final_test_access == "authorized"
    assert rebuilt.final_test_inference_executed is False
    assert rebuilt.final_test_rows_used == 0
    assert sum(row.final_test_count for row in rebuilt.required_datasets) == 1673


def test_authorization_is_not_an_evaluation_result() -> None:
    artifact = load_final_test_authorization(AUTHORIZATION)

    assert artifact.no_post_test_tuning is True
    assert artifact.architecture_reopening_forbidden is True
    assert artifact.calibration_refit_forbidden is True
    assert artifact.ecal_reselection_forbidden is True
    assert artifact.fhir_reselection_forbidden is True
    assert artifact.failure_accounting == [
        "requested",
        "completed",
        "timeout",
        "oom",
        "transport",
        "interface",
        "parse",
    ]


def test_authorization_rejects_forged_system_bundle_digest() -> None:
    payload = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    payload["required_system_bundle_digests"]["laya"] = "0" * 64

    with pytest.raises(ValidationError, match="required system bundle digest drift"):
        FinalTestAuthorizationArtifact.model_validate(payload)


def test_authorization_rejects_forged_dataset_binding() -> None:
    payload = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    payload["required_datasets"][0]["split_manifest_sha256"] = "0" * 64

    with pytest.raises(ValidationError, match="required dataset authorization binding drift"):
        FinalTestAuthorizationArtifact.model_validate(payload)


def test_authorization_rejects_forged_authorization_digest() -> None:
    payload = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    payload["authorization_digest"] = "0" * 64

    with pytest.raises(ValidationError, match="authorization digest does not match frozen payload"):
        FinalTestAuthorizationArtifact.model_validate(payload)


def test_authorization_rejects_policy_drift() -> None:
    payload = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    payload["coverage_targets"] = [0.5, 0.9]

    with pytest.raises(ValidationError, match="coverage target drift"):
        FinalTestAuthorizationArtifact.model_validate(payload)
