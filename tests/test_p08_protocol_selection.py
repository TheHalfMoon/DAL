from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_protocol_selection import (
    CALIBRATION_MANIFEST_SHA256,
    COVERAGE_TARGETS,
    ECAL_CANDIDATES,
    FHIR_CANDIDATES,
    PAPER_CHECKPOINT_SHA256,
    SG000020_CONTRACT_SHA256,
    P08ProtocolSelectionContract,
    protocol_selection_contract_digest,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "registry" / "p08_calibration_selection_contract_sg000020.json"


def _payload() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_canonical_sg000020_contract_validates_and_hashes() -> None:
    contract = P08ProtocolSelectionContract.model_validate(_payload())
    assert protocol_selection_contract_digest(contract) == SG000020_CONTRACT_SHA256
    assert contract.final_test_access == "sealed"
    assert contract.calibration.manifest_sha256 == CALIBRATION_MANIFEST_SHA256
    assert contract.selected_paper_checkpoint.checkpoint_sha256 == PAPER_CHECKPOINT_SHA256
    assert contract.calibration.coverage_targets == list(COVERAGE_TARGETS)
    assert contract.ecal.candidate_order == list(ECAL_CANDIDATES)
    assert contract.fhir.candidate_order == list(FHIR_CANDIDATES)
    assert contract.authorization_candidate.can_authorize_inference is False


def test_calibration_role_assignments_are_non_overlapping_by_purpose() -> None:
    contract = P08ProtocolSelectionContract.model_validate(_payload())
    rows = contract.calibration.role_assignments
    assert [(row.dataset_id, row.count, row.purpose) for row in rows] == [
        ("pubmedqa-pqal", 50, "action-temperature-fit"),
        ("gax-native-abstention-pqal", 100, "sufficiency-platt-fit"),
        ("fhir-agentbench", 341, "fhir-representation-selection-only"),
    ]
    assert rows[0].action_space == ["maybe", "no", "yes"]
    assert rows[1].pair_policy == "50-evidence-present+50-evidence-withheld"


def test_fhir_source_is_open_frozen_demo_not_paid_gcp_runtime() -> None:
    contract = P08ProtocolSelectionContract.model_validate(_payload())
    source = contract.fhir.source
    assert source.fhir_agentbench_revision == "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    assert source.mimic_fhir_demo_version == "2.1.0"
    assert source.mimic_fhir_demo_license == "ODbL-1.0"
    assert source.mimic_fhir_demo_access == "open"
    assert source.source_checksum_policy == (
        "record-and-verify-PhysioNet-SHA256SUMS-before-selection"
    )


def test_contract_rejects_checkpoint_drift() -> None:
    payload = deepcopy(_payload())
    selected = payload["selected_paper_checkpoint"]
    assert isinstance(selected, dict)
    selected["checkpoint_sha256"] = "0" * 64
    with pytest.raises(ValidationError, match="paper checkpoint digest drift"):
        P08ProtocolSelectionContract.model_validate(payload)


def test_contract_rejects_ecal_candidate_drift() -> None:
    payload = deepcopy(_payload())
    ecal = payload["ecal"]
    assert isinstance(ecal, dict)
    candidates = ecal["candidate_order"]
    assert isinstance(candidates, list)
    candidates.reverse()
    with pytest.raises(ValidationError, match="ECAL candidate order drift"):
        P08ProtocolSelectionContract.model_validate(payload)


def test_contract_rejects_fhir_candidate_drift() -> None:
    payload = deepcopy(_payload())
    fhir = payload["fhir"]
    assert isinstance(fhir, dict)
    candidates = fhir["candidate_order"]
    assert isinstance(candidates, list)
    candidates.pop()
    with pytest.raises(ValidationError, match="FHIR candidate order drift"):
        P08ProtocolSelectionContract.model_validate(payload)


def test_contract_rejects_calibration_role_drift() -> None:
    payload = deepcopy(_payload())
    calibration = payload["calibration"]
    assert isinstance(calibration, dict)
    roles = calibration["role_assignments"]
    assert isinstance(roles, list)
    first = roles[0]
    assert isinstance(first, dict)
    first["count"] = 49
    with pytest.raises(ValidationError, match="calibration role assignment drift"):
        P08ProtocolSelectionContract.model_validate(payload)


def test_contract_rejects_any_final_test_opening() -> None:
    payload = deepcopy(_payload())
    payload["final_test_access"] = "open"
    with pytest.raises(ValidationError):
        P08ProtocolSelectionContract.model_validate(payload)
