from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from gaxbench.fhir_agentbench_qualification import _EXPECTED_HEADERS, git_blob_sha1
from gaxbench.study1_fhir_custodian import (
    FOUNDER_AUTHORIZATION_COMMENT_ID,
    FOUNDER_AUTHORIZATION_ISSUE,
    _parse_expected_resource_ids,
    _scan_selected_rows,
    build_blind_development_projection,
)

AUTHORIZATION_PATH = Path("registry/study1_sg000026_option_a_authorization.json")
WORKFLOW_PATH = Path(".github/workflows/study1-sg000026-option-a-custodian.yml")


def _row(*, split: str, question_id: str, patient: str, final: bool) -> dict[str, str]:
    index = question_id.rsplit("-", 1)[-1]
    if final:
        question = "FINAL_SECRET_QUESTION, with comma\nand newline"
        sql_query = "FINAL_SECRET_SQL"
        true_answer = "FINAL_SECRET_ANSWER"
        proc_query = "FINAL_SECRET_QUERY"
        true_fhir_ids = "{'Observation': ['FINAL_SECRET_ID']}"
    else:
        question = f"Development question {index}"
        sql_query = "SELECT development"
        true_answer = "development-answer"
        proc_query = f"Encounter?patient={index}"
        true_fhir_ids = f"{{'Encounter': ['e-{index}']}}"
    return {
        "split": split,
        "question_id": question_id,
        "question": question,
        "sql_query": sql_query,
        "true_answer": true_answer,
        "assumption": "fixture",
        "patient_fhir_id": patient,
        "template": "fixture template",
        "val_dict": "{}",
        "proc_query": proc_query,
        "main_table_name": "encounters",
        "mappable_to_fhir": "True",
        "true_fhir_ids": true_fhir_ids,
    }


def _write_fixture(path: Path) -> bytes:
    rows: list[dict[str, str]] = []
    for index in range(94):
        patient = f"Patient/{index:03d}"
        rows.append(
            _row(
                split="train",
                question_id=f"train-{index:03d}",
                patient=patient,
                final=False,
            )
        )
        rows.append(
            _row(
                split="test",
                question_id=f"test-{index:03d}",
                patient=patient,
                final=True,
            )
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_EXPECTED_HEADERS), lineterminator="\n")
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
    assert "FINAL_SECRET" not in emitted
    assert "Patient/" not in emitted
    assert '"question_id":' not in emitted
    assert "Development question" not in emitted
    assert manifest.is_file()


def test_csv_projection_does_not_decode_unselected_row_fields() -> None:
    body = b"safe,visible\nignored,\xff\n"
    selected = _scan_selected_rows(
        body,
        field_count=2,
        selected_columns=frozenset({0}),
        selected_rows=frozenset({1}),
    )
    assert selected == [(1, {0: "safe"})]


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


def test_authorization_and_workflow_keep_option_a_narrow() -> None:
    authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    assert authorization["authorized_option"] == "option-a-blind-metadata-only-custodian"
    assert authorization["authorization_issue"] == 120
    assert authorization["authorization_comment_id"] == 5963555775
    assert authorization["final_boundary"]["final_supervision_allowed"] is False
    assert authorization["later_stages_activated"] is False

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" not in workflow
    assert "branches:\n      - main" in workflow
    assert "source.unlink(missing_ok=True)" in workflow
    assert "sg000026-option-a/output/" in workflow
    assert "sg000026-option-a/source.csv" not in workflow
