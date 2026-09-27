from __future__ import annotations

import csv
from pathlib import Path

import pytest

from gaxbench.fhir_agentbench_qualification import (
    _SourceRow,
    _assign_patient_roles,
    _identifier_digest,
    _included_rows_with_roles,
    git_blob_sha1,
    probe_frozen_source,
    report_exposes_sensitive_content,
    verify_frozen_source,
)


def _write_fixture(path: Path) -> bytes:
    rows = [
        {
            "split": "train",
            "question_id": "q1",
            "question": "What resource belongs to patient 1?",
            "sql_query": "SELECT secret_train",
            "true_answer": "secret-answer-1",
            "assumption": "fixture",
            "patient_fhir_id": "Patient/alpha",
            "template": "What resource belongs to patient {patient_id}?",
            "val_dict": "{}",
            "true_fhir_ids": "{'Patient': ['alpha']}",
        },
        {
            "split": "valid",
            "question_id": "q2",
            "question": "What resource belongs to patient 2?",
            "sql_query": "SELECT secret_valid",
            "true_answer": "secret-answer-2",
            "assumption": "fixture",
            "patient_fhir_id": "Patient/alpha",
            "template": "What resource belongs to patient {patient_id}?",
            "val_dict": "{}",
            "true_fhir_ids": "{'Patient': ['alpha']}",
        },
        {
            "split": "test",
            "question_id": "q3",
            "question": "Is a different question present?",
            "sql_query": "SELECT secret_test",
            "true_answer": "secret-answer-3",
            "assumption": "fixture",
            "patient_fhir_id": "Patient/beta",
            "template": "Is a different question present?",
            "val_dict": "{}",
            "true_fhir_ids": "{'Patient': ['beta']}",
        },
    ]
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path.read_bytes()


def _role_policy_rows() -> list[_SourceRow]:
    rows: list[_SourceRow] = []
    for patient_index in range(94):
        patient_digest = _identifier_digest(f"Patient/{patient_index:03d}")
        rows.append(
            _SourceRow(
                upstream_split="train",
                question_id=f"train-{patient_index:03d}",
                question=f"Train question {patient_index}",
                template="Train question {patient_id}",
                patient_digest=patient_digest,
            )
        )
        rows.append(
            _SourceRow(
                upstream_split="test",
                question_id=f"test-{patient_index:03d}",
                question=f"Test question {patient_index}",
                template="Test question {patient_id}",
                patient_digest=patient_digest,
            )
        )
    return rows


def test_probe_is_metadata_only_and_detects_cross_split_identity(tmp_path: Path) -> None:
    source = tmp_path / "fixture.csv"
    payload = _write_fixture(source)
    report = probe_frozen_source(source, expected_blob_sha1=git_blob_sha1(payload))

    assert report.row_count == 3
    assert report.split_counts == {"test": 1, "train": 1, "valid": 1}
    assert report.unique_question_ids == 3
    assert report.duplicate_question_id_count == 0
    assert report.cross_split_patient_identity_count == 1
    assert report.cross_split_exact_question_count == 0
    assert report.cross_split_template_count == 1
    assert report.final_test_access == "sealed"
    assert report.ehrsql_generation_revision_proven is False
    assert report_exposes_sensitive_content(report) is False

    serialized = report.model_dump_json()
    assert "secret-answer" not in serialized
    assert "secret_train" not in serialized
    assert "Patient/alpha" not in serialized
    assert "What resource belongs" not in serialized


def test_probe_counts_duplicate_question_ids(tmp_path: Path) -> None:
    source = tmp_path / "fixture.csv"
    _write_fixture(source)
    text = source.read_text(encoding="utf-8").replace("q2,", "q1,", 1)
    source.write_text(text, encoding="utf-8")
    payload = source.read_bytes()
    report = probe_frozen_source(source, expected_blob_sha1=git_blob_sha1(payload))
    assert report.unique_question_ids == 2
    assert report.duplicate_question_id_count == 1


def test_frozen_source_rejects_wrong_blob() -> None:
    with pytest.raises(ValueError, match="Git blob mismatch"):
        verify_frozen_source(b"not-the-frozen-source")


def test_role_policy_never_moves_upstream_test_rows_into_non_test_roles() -> None:
    rows = _role_policy_rows()
    roles = _assign_patient_roles(rows)
    included, excluded = _included_rows_with_roles(rows, roles)

    assert sum(role == "test" for role in roles.values()) == 40
    assert sum(role == "calibration" for role in roles.values()) == 14
    assert sum(role == "validation" for role in roles.values()) == 40

    for row, role in included:
        if role == "test":
            assert row.upstream_split == "test"
        else:
            assert row.upstream_split != "test"

    assert excluded["non-test-row-for-test-patient"] == 40
    assert excluded["upstream-test-row-for-non-test-patient"] == 54
    assert len(included) == 94


def test_role_policy_is_patient_disjoint() -> None:
    rows = _role_policy_rows()
    roles = _assign_patient_roles(rows)
    included, _ = _included_rows_with_roles(rows, roles)

    observed_roles: dict[str, set[str]] = {}
    for row, role in included:
        observed_roles.setdefault(row.patient_digest, set()).add(role)

    assert all(len(patient_roles) == 1 for patient_roles in observed_roles.values())
    assert set().union(*observed_roles.values()) == {"calibration", "validation", "test"}
