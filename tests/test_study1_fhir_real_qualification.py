from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from gaxbench.study1_fhir_real_qualification import qualify_real_development_direct_ids


def _write_runtime(root: Path, resources: list[dict[str, object]]) -> Path:
    target = root / "fhir" / "fixture.ndjson.gz"
    target.parent.mkdir(parents=True)
    with gzip.open(target, "wt", encoding="utf-8", newline="\n") as handle:
        for resource in resources:
            handle.write(json.dumps(resource, sort_keys=True) + "\n")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "0.1",
        "study": "DAL Study 1",
        "specgrain": "SG-000026",
        "stage": "D2",
        "purpose": "fixture",
        "source": {},
        "cost_boundary": {},
        "scope_boundary": {},
        "files": [{"path": "fhir/fixture.ndjson.gz", "sha256": digest}],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _write_projection(path: Path, rows: list[dict[str, object]]) -> str:
    payload = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    ).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _row(role: str, expected: list[str]) -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "role": role,
        "question_id_sha256": "0" * 64,
        "proc_query": "SELECT fixture",
        "expected_resource_ids": expected,
    }


def test_real_direct_id_qualification_passes_but_keeps_query_trace_blocked(
    tmp_path: Path,
) -> None:
    manifest = _write_runtime(
        tmp_path / "runtime",
        [{"resourceType": "Encounter", "id": "e1"}],
    )
    projection = tmp_path / "projection.jsonl"
    projection_sha = _write_projection(
        projection,
        [_row("calibration", ["Encounter/e1"]), _row("validation", [])],
    )
    report = qualify_real_development_direct_ids(
        projection,
        tmp_path / "runtime",
        manifest,
        expected_projection_sha256=projection_sha,
        expected_calibration_rows=1,
        expected_validation_rows=1,
    )
    assert report.status == "partial-pass-direct-id-only"
    assert report.requested_reference_count == 1
    assert report.resolved_reference_count == 1
    assert report.exact_match_rows == 1
    assert report.rows_without_expected_ids == 1
    assert report.query_trace_coverage == "blocked-unavailable-from-authorized-projection"
    assert report.d2_closeout_allowed is False
    assert report.sealed_final_rows_accessed is False


def test_missing_real_resource_is_retained_as_negative_evidence(tmp_path: Path) -> None:
    manifest = _write_runtime(tmp_path / "runtime", [])
    projection = tmp_path / "projection.jsonl"
    projection_sha = _write_projection(
        projection,
        [_row("calibration", ["Observation/missing"]), _row("validation", [])],
    )
    report = qualify_real_development_direct_ids(
        projection,
        tmp_path / "runtime",
        manifest,
        expected_projection_sha256=projection_sha,
        expected_calibration_rows=1,
        expected_validation_rows=1,
    )
    assert report.status == "partial-fail-direct-id"
    assert report.resolved_reference_count == 0
    assert report.missing_reference_count == 1
    assert report.mismatch_rows == 1
    assert len(report.missing_reference_sha256s) == 1


def test_projection_field_drift_is_rejected_before_runtime_use(tmp_path: Path) -> None:
    manifest = _write_runtime(tmp_path / "runtime", [])
    projection = tmp_path / "projection.jsonl"
    row = _row("calibration", [])
    row["question"] = "not authorized"
    projection_sha = _write_projection(projection, [row, _row("validation", [])])
    with pytest.raises(ValueError, match="field drift"):
        qualify_real_development_direct_ids(
            projection,
            tmp_path / "runtime",
            manifest,
            expected_projection_sha256=projection_sha,
            expected_calibration_rows=1,
            expected_validation_rows=1,
        )


WORKFLOW = Path(".github/workflows/study1-sg000026-real-direct-id-qualification.yml")


def test_real_qualification_workflow_is_main_only_and_digest_bound() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" not in workflow
    assert "branches:\n      - main" in workflow
    assert "actions: read" in workflow
    assert 'CUSTODIAN_ARTIFACT_ID: "11260661014"' in workflow
    assert (
        'CUSTODIAN_ARTIFACT_DIGEST: "sha256:'
        '5de5bcb8c7a3f37d23da503f40362ef1a7bc7e7d143c5876a0e0992f21428114"' in workflow
    )
    assert (
        'PROJECTION_SHA256: "a09357620e811de49dd868773854e4f48e742a3882110c2f6228633ad161aae7"'
        in workflow
    )
    assert 'CUSTODIAN_RUN_ID: "37084890139"' in workflow
    assert 'CUSTODIAN_HEAD_SHA: "e1db1efe6f42523d3b02feec4458f0da6612eb77"' in workflow
    assert "gh api" in workflow
    assert "gh run download" in workflow
    assert "custodian_zip_sha256" not in workflow
    assert "blocked-unavailable-from-authorized-projection" in workflow
    assert "d2_closeout_allowed" in workflow
