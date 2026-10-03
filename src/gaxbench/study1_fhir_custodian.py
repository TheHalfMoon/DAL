from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Literal, Mapping

from pydantic import Field, model_validator

from gaxbench.fhir_agentbench_qualification import (
    FHIR_AGENTBENCH_ROLE_REVISION,
    FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
    FHIR_AGENTBENCH_SOURCE_COMMIT,
    FHIR_AGENTBENCH_SOURCE_SHA256,
    _SourceRow,
    _assign_patient_roles,
    _exclusion_reason,
    _identifier_digest,
    verify_frozen_source,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

CANONICAL_MEMBERSHIP_SHA256 = (
    "b90e774067d0a0e4251e32584b3aeea9629a01df9201fc550988e70d17dbda15"
)
CANONICAL_CALIBRATION_ROWS = 341
CANONICAL_VALIDATION_ROWS = 1122
CANONICAL_FINAL_ROWS = 173
FOUNDER_AUTHORIZATION_ISSUE = 120
FOUNDER_AUTHORIZATION_COMMENT_ID = 5963555775

D2ProjectionRole = Literal["calibration", "validation"]


class D2FHIRDevelopmentProjectionRow(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    role: D2ProjectionRole
    question_id_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proc_query: str = Field(min_length=1)
    expected_resource_ids: list[str]

    @model_validator(mode="after")
    def validate_expected_ids(self) -> D2FHIRDevelopmentProjectionRow:
        if self.expected_resource_ids != sorted(self.expected_resource_ids):
            raise ValueError("expected_resource_ids must be deterministically sorted")
        if len(self.expected_resource_ids) != len(set(self.expected_resource_ids)):
            raise ValueError("expected_resource_ids must be unique")
        return self


class D2FHIRCustodianManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    study_id: Literal["study1"] = "study1"
    stage: Literal["D2"] = "D2"
    specgrain_id: Literal["SG-000026"] = "SG-000026"
    recovery_option: Literal["option-a-blind-metadata-only-custodian"] = (
        "option-a-blind-metadata-only-custodian"
    )
    authorization_issue: Literal[120] = 120
    authorization_comment_id: Literal[5963555775] = 5963555775
    source_commit: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role_revision: str
    membership_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_rows: int = Field(ge=0)
    validation_rows: int = Field(ge=0)
    sealed_final_rows: int = Field(ge=0)
    projection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    projection_rows: int = Field(ge=0)
    final_rows_materialized: Literal[0] = 0
    final_sensitive_fields_accessed: Literal[False] = False
    raw_question_ids_emitted: Literal[False] = False
    raw_patient_ids_emitted: Literal[False] = False

    @model_validator(mode="after")
    def validate_counts(self) -> D2FHIRCustodianManifest:
        if self.projection_rows != self.calibration_rows + self.validation_rows:
            raise ValueError("projection_rows must equal calibration_rows + validation_rows")
        return self


def build_blind_development_projection(
    source_path: Path,
    projection_path: Path,
    manifest_path: Path,
    *,
    expected_blob_sha1: str = FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
    expected_source_sha256: str = FHIR_AGENTBENCH_SOURCE_SHA256,
    expected_membership_sha256: str | None = CANONICAL_MEMBERSHIP_SHA256,
    expected_calibration_rows: int = CANONICAL_CALIBRATION_ROWS,
    expected_validation_rows: int = CANONICAL_VALIDATION_ROWS,
    expected_final_rows: int = CANONICAL_FINAL_ROWS,
) -> D2FHIRCustodianManifest:
    source_bytes = source_path.read_bytes()
    verify_frozen_source(source_bytes, expected_blob_sha1=expected_blob_sha1)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != expected_source_sha256:
        raise ValueError(
            f"FHIR-AgentBench SHA-256 mismatch: {source_sha256} != {expected_source_sha256}"
        )

    metadata_rows = _read_metadata_only(source_path)
    source_rows = [
        _SourceRow(
            upstream_split=row["split"],
            question_id=row["question_id"],
            question="",
            template="",
            patient_digest=_identifier_digest(row["patient_fhir_id"]),
        )
        for row in metadata_rows
    ]
    if len({row.question_id for row in source_rows}) != len(source_rows):
        raise ValueError("FHIR-AgentBench question_id values must be unique")

    roles_by_patient = _assign_patient_roles(source_rows)
    membership_payload, role_counts = _membership_payload(source_rows, roles_by_patient)
    membership_sha256 = canonical_json_sha256(membership_payload)
    if expected_membership_sha256 is not None and membership_sha256 != expected_membership_sha256:
        raise ValueError(
            "frozen role-membership digest mismatch: "
            f"{membership_sha256} != {expected_membership_sha256}"
        )

    rows = _project_development_rows(source_path, roles_by_patient)
    calibration_rows = sum(row.role == "calibration" for row in rows)
    validation_rows = sum(row.role == "validation" for row in rows)
    if calibration_rows != expected_calibration_rows:
        raise ValueError("calibration projection row count drift")
    if validation_rows != expected_validation_rows:
        raise ValueError("validation projection row count drift")
    if role_counts["test"] != expected_final_rows:
        raise ValueError("sealed final role row count drift")

    rows.sort(key=lambda row: row.question_id_sha256)
    projection_bytes = _projection_bytes(rows)
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_bytes(projection_bytes)
    manifest = D2FHIRCustodianManifest(
        source_commit=FHIR_AGENTBENCH_SOURCE_COMMIT,
        source_sha256=source_sha256,
        role_revision=FHIR_AGENTBENCH_ROLE_REVISION,
        membership_sha256=membership_sha256,
        calibration_rows=calibration_rows,
        validation_rows=validation_rows,
        sealed_final_rows=role_counts["test"],
        projection_sha256=hashlib.sha256(projection_bytes).hexdigest(),
        projection_rows=len(rows),
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def _read_metadata_only(source_path: Path) -> list[dict[str, str]]:
    required = {"split", "question_id", "patient_fhir_id"}
    rows: list[dict[str, str]] = []
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or ())
        missing = required - headers
        if missing:
            raise ValueError(f"missing custodian metadata columns: {sorted(missing)}")
        for row_number, raw in enumerate(reader, start=1):
            row = {name: (raw.get(name) or "").strip() for name in required}
            if not all(row.values()):
                raise ValueError(f"empty custodian metadata at row {row_number}")
            rows.append(row)
    return rows


def _membership_payload(
    rows: list[_SourceRow],
    roles_by_patient: Mapping[str, str],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    payload: list[dict[str, str]] = []
    counts = {"calibration": 0, "validation": 0, "test": 0}
    for row in rows:
        role = roles_by_patient[row.patient_digest]
        question_digest = _identifier_digest(row.question_id)
        included = (role == "test" and row.upstream_split == "test") or (
            role in {"calibration", "validation"} and row.upstream_split != "test"
        )
        if included:
            counts[role] += 1
            payload.append(
                {
                    "question_id_sha256": question_digest,
                    "patient_identity_sha256": row.patient_digest,
                    "membership": role,
                }
            )
        else:
            payload.append(
                {
                    "question_id_sha256": question_digest,
                    "patient_identity_sha256": row.patient_digest,
                    "membership": "excluded",
                    "reason": _exclusion_reason(row, role),
                }
            )
    payload.sort(key=lambda entry: entry["question_id_sha256"])
    return payload, counts


def _project_development_rows(
    source_path: Path,
    roles_by_patient: Mapping[str, str],
) -> list[D2FHIRDevelopmentProjectionRow]:
    rows: list[D2FHIRDevelopmentProjectionRow] = []
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"split", "question_id", "patient_fhir_id", "proc_query", "true_fhir_ids"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing development projection columns: {sorted(missing)}")
        for raw in reader:
            split = (raw.get("split") or "").strip()
            question_id = (raw.get("question_id") or "").strip()
            patient_id = (raw.get("patient_fhir_id") or "").strip()
            role = roles_by_patient[_identifier_digest(patient_id)]
            if role not in {"calibration", "validation"} or split == "test":
                continue
            rows.append(_project_development_row(raw, role=role, question_id=question_id))
    return rows


def _project_development_row(
    raw: Mapping[str, str],
    *,
    role: str,
    question_id: str,
) -> D2FHIRDevelopmentProjectionRow:
    if role not in {"calibration", "validation"}:
        raise ValueError("custodian may materialize development roles only")
    proc_query = (raw.get("proc_query") or "").strip()
    if not proc_query:
        raise ValueError("development row has empty proc_query")
    return D2FHIRDevelopmentProjectionRow(
        role=role,
        question_id_sha256=_identifier_digest(question_id),
        proc_query=proc_query,
        expected_resource_ids=_parse_expected_resource_ids(raw.get("true_fhir_ids") or ""),
    )


def _parse_expected_resource_ids(value: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        raise ValueError("development true_fhir_ids is not a literal mapping") from exc
    if not isinstance(parsed, dict):
        raise ValueError("development true_fhir_ids must be a mapping")
    identities: list[str] = []
    for resource_type, resource_ids in parsed.items():
        if not isinstance(resource_type, str) or not isinstance(resource_ids, list):
            raise ValueError("development true_fhir_ids has invalid shape")
        for resource_id in resource_ids:
            if not isinstance(resource_id, str) or not resource_id:
                raise ValueError("development true_fhir_ids contains invalid resource id")
            identities.append(f"{resource_type}/{resource_id}")
    if len(identities) != len(set(identities)):
        raise ValueError("development true_fhir_ids contains duplicate resource identity")
    return sorted(identities)


def _projection_bytes(rows: list[D2FHIRDevelopmentProjectionRow]) -> bytes:
    return "".join(
        json.dumps(row.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        + "\n"
        for row in rows
    ).encode("utf-8")
