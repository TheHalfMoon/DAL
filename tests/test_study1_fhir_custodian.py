from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from gaxbench.fhir_agentbench_qualification import git_blob_sha1
from gaxbench.study1_fhir_custodian import (
    FOUNDER_AUTHORIZATION_COMMENT_ID,
    FOUNDER_AUTHORIZATION_ISSUE,
    _parse_expected_resource_ids,
    _project_development_row,
    build_blind_development_projection,
)


def _write_fixture(path: Path) -> bytes:
    fieldnames = [
        "split",
        "question_id",
        "patient_fhir_id",
        "proc_query",
        "true_fhir_ids",
    ]
    rows: list[dict[str, str]] = []
    for index in range(94):
        patient = f"Patient/{index:03d}"
        rows.append(
            {
                "split": "train",
                "question_id": f"train-{index:03d}",
                "patient_fhir_id": patient,
                "proc_query": f"Encounter?patient={index:03d}",
                "true_fhir_ids": f"{{'Encounter': ['e-{index:03d}']}}",
            }
        )
        rows.append(
            {
                "split": "test",
                "question_id": f"test-{index:03d}",
                "patient_fhir_id": patient,
                "proc_query": "FINAL_SECRET_QUERY",
                "true_fhir_ids": "{'Observation': ['FINAL_SECRET_ID']}",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path.read_bytes()


def test_blind_custodian_emits_only_development_projection(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    payload = _write_fixture(source)
    projection = tmp_path / "development.jsonl"
    manifest = tmp_path / "manifest.json"

    result = build_blind_development_projection(
        source,
        projection,
        manifest,
        expected_blob_sha1=git_blob_sha1(payload),
        expected_source_sha256=hashlib.sha256(payload).hexdigest(),
        expected_membership_sha256=None,
        expected_calibration_rows=14,
        expected_validation_rows=40,
        expected_final_rows=40,
    )

    assert result.calibration_rows == 14
    assert result.validation_rows == 40
    assert result.sealed_final_rows == 40
    assert result.projection_rows == 54
    assert result.final_rows_materialized == 0
    assert result.final_sensitive_fields_accessed is False
    assert FOUNDER_AUTHORIZATION_ISSUE == 120
    assert FOUNDER_AUTHORIZATION_COMMENT_ID == 5963555775

    emitted = projection.read_text(encoding="utf-8")
    assert "FINAL_SECRET_QUERY" not in emitted
    assert "FINAL_SECRET_ID" not in emitted
    assert "Patient/" not in emitted
    assert '"question_id":' not in emitted
    assert manifest.is_file()


class _SensitiveTrap(Mapping[str, str]):
    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"sensitive field accessed: {key}")

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def get(self, key: str, default: str | None = None) -> str | None:
        raise AssertionError(f"sensitive field accessed: {key}")


def test_non_development_role_is_rejected_before_sensitive_field_access() -> None:
    with pytest.raises(ValueError, match="development roles only"):
        _project_development_row(_SensitiveTrap(), role="test", question_id="sealed-q")


def test_expected_resource_id_parser_is_deterministic() -> None:
    assert _parse_expected_resource_ids("{'Observation': ['z'], 'Encounter': ['b', 'a']}") == [
        "Encounter/a",
        "Encounter/b",
        "Observation/z",
    ]

    with pytest.raises(ValueError, match="literal mapping"):
        _parse_expected_resource_ids("not-a-mapping")
    with pytest.raises(ValueError, match="duplicate"):
        _parse_expected_resource_ids("{'Encounter': ['a', 'a']}")
