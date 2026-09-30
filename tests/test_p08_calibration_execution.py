from __future__ import annotations

import pytest
from pydantic import ValidationError

from gaxbench.p08_calibration_execution import (
    AuthorizationCandidate,
    FhirRepresentationEvidence,
    artifact_digest,
    fit_platt,
    fit_temperature,
    frozen_ecal_ledger,
    select_fhir_representation,
)


def test_temperature_fit_is_deterministic_and_nonworsening() -> None:
    logits: list[list[float]] = []
    labels: list[int] = []
    for index in range(50):
        label = index % 3
        labels.append(label)
        row = [0.0, 0.0, 0.0]
        row[label] = 2.0 if index % 5 else 0.2
        logits.append(row)
    first = fit_temperature(logits, labels)
    second = fit_temperature(logits, labels)
    assert first == second
    assert first.count == 50
    assert first.temperature > 0.0
    assert first.nll_after <= first.nll_before


def test_platt_fit_is_deterministic_and_nonworsening() -> None:
    raw = [2.0 + index / 100.0 for index in range(50)] + [
        -2.0 - index / 100.0 for index in range(50)
    ]
    labels = [1] * 50 + [0] * 50
    first = fit_platt(raw, labels)
    second = fit_platt(raw, labels)
    assert first == second
    assert first.count == 100
    assert first.bce_after <= first.bce_before
    assert first.iterations_used <= 100


def test_calibration_functions_fail_closed_on_role_count_drift() -> None:
    with pytest.raises(ValueError, match="exactly 50"):
        fit_temperature([[1.0, 0.0, 0.0]], [0])
    with pytest.raises(ValueError, match="exactly 100"):
        fit_platt([1.0, -1.0], [1, 0])


def test_frozen_ecal_ledger_preserves_all_candidates_and_checkpoint() -> None:
    ledger = frozen_ecal_ledger()
    assert [row.component for row in ledger.decisions] == [
        "evidence",
        "hard-negative",
        "proper-scoring",
        "replay-retention",
        "state-action-contrastive",
    ]
    assert [row.component for row in ledger.decisions if row.decision == "keep"] == [
        "evidence"
    ]
    assert [row.component for row in ledger.decisions if row.decision == "reject"] == [
        "hard-negative",
        "proper-scoring",
        "replay-retention",
        "state-action-contrastive",
    ]
    assert ledger.checkpoint_mutated is False
    assert ledger.final_test_access == "sealed"
    assert len(artifact_digest(ledger)) == 64


def _fhir_row(
    representation: str, median: float, *, eligible: bool = True
) -> FhirRepresentationEvidence:
    return FhirRepresentationEvidence(
        representation=representation,  # type: ignore[arg-type]
        requested_reference_count=20,
        resolved_reference_count=20 if eligible else 19,
        unique_resource_count=10,
        missing_resource_count=0 if eligible else 1,
        parse_failure_count=0,
        deterministic_repeat=True,
        key_order_invariant=representation != "source-order-json",
        source_order_sensitivity_recorded=representation == "source-order-json",
        narrative_exposure_count=0,
        median_rendered_bytes=median,
        min_rendered_bytes=1,
        max_rendered_bytes=100,
        eligible=eligible,
    )


def test_fhir_selection_uses_minimum_eligible_median_and_frozen_tie_break() -> None:
    rows = [
        _fhir_row("canonical-structured", 80.0),
        _fhir_row("canonical-with-narrative", 100.0),
        _fhir_row("flat-text", 70.0),
        _fhir_row("source-order-json", 70.0),
    ]
    evidence = select_fhir_representation(
        rows,
        physionet_sha256s_sha256="a" * 64,
        checksum_entry_count=30,
        checksum_verified_file_count=30,
    )
    assert evidence.selected_representation == "flat-text"
    assert evidence.final_test_access == "sealed"


def test_fhir_selection_rejects_no_eligible_candidate() -> None:
    rows = [
        _fhir_row("canonical-structured", 80.0, eligible=False),
        _fhir_row("canonical-with-narrative", 100.0, eligible=False),
        _fhir_row("flat-text", 70.0, eligible=False),
        _fhir_row("source-order-json", 65.0, eligible=False),
    ]
    with pytest.raises(ValueError, match="no eligible"):
        select_fhir_representation(
            rows,
            physionet_sha256s_sha256="b" * 64,
            checksum_entry_count=30,
            checksum_verified_file_count=30,
        )


def test_authorization_candidate_is_structurally_sealed() -> None:
    candidate = AuthorizationCandidate(
        required_system_bundle_digests={
            "gax-paper-candidate": "0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b",
            "clinical-encoder": "b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388",
            "laya": "b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534",
        },
        calibration_evidence_sha256="c" * 64,
        selected_ecal_configuration_sha256="d" * 64,
        selected_fhir_representation_sha256="e" * 64,
    )
    assert candidate.final_test_access == "sealed"
    assert candidate.can_authorize_inference is False
    payload = candidate.model_dump(mode="json")
    payload["can_authorize_inference"] = True
    with pytest.raises(ValidationError):
        AuthorizationCandidate.model_validate(payload)
