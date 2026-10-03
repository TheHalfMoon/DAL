from __future__ import annotations

import ast
import csv
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.fhir_agentbench_qualification import (
    FHIR_AGENTBENCH_ROLE_REVISION,
    FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
    FHIR_AGENTBENCH_SOURCE_COMMIT,
    FHIR_AGENTBENCH_SOURCE_SHA256,
    GAXRole,
    _assign_patient_roles,
    _exclusion_reason,
    _EXPECTED_HEADERS,
    _identifier_digest,
    _SourceRow,
    verify_frozen_source,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

CANONICAL_MEMBERSHIP_SHA256 = "b90e774067d0a0e4251e32584b3aeea9629a01df9201fc550988e70d17dbda15"
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

    headers, body = _split_header(source_bytes)
    if tuple(headers) != _EXPECTED_HEADERS:
        raise ValueError("FHIR-AgentBench header order drifted from the frozen source")
    index = {name: headers.index(name) for name in headers}

    metadata_fields = frozenset(
        {index["split"], index["question_id"], index["patient_fhir_id"]}
    )
    metadata_rows = _scan_selected_rows(
        body,
        field_count=len(headers),
        selected_columns=metadata_fields,
    )
    source_rows: list[_SourceRow] = []
    row_metadata: dict[int, tuple[str, str, str]] = {}
    for row_number, selected in metadata_rows:
        split = _required_selected(selected, index["split"], row_number, "split")
        question_id = _required_selected(
            selected, index["question_id"], row_number, "question_id"
        )
        patient_id = _required_selected(
            selected, index["patient_fhir_id"], row_number, "patient_fhir_id"
        )
        patient_digest = _identifier_digest(patient_id)
        row_metadata[row_number] = (split, question_id, patient_digest)
        source_rows.append(
            _SourceRow(
                upstream_split=split,
                question_id=question_id,
                question="",
                template="",
                patient_digest=patient_digest,
            )
        )
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

    development_rows: dict[int, tuple[D2ProjectionRole, str]] = {}
    for row_number, (split, question_id, patient_digest) in row_metadata.items():
        role = roles_by_patient[patient_digest]
        if split == "test":
            continue
        if role == "calibration":
            development_rows[row_number] = ("calibration", question_id)
        elif role == "validation":
            development_rows[row_number] = ("validation", question_id)

    projection_fields = frozenset({index["proc_query"], index["true_fhir_ids"]})
    selected_projection_rows = _scan_selected_rows(
        body,
        field_count=len(headers),
        selected_columns=projection_fields,
        selected_rows=frozenset(development_rows),
    )
    rows: list[D2FHIRDevelopmentProjectionRow] = []
    for row_number, selected in selected_projection_rows:
        role, question_id = development_rows[row_number]
        proc_query = _required_selected(
            selected, index["proc_query"], row_number, "proc_query"
        )
        true_fhir_ids = _required_selected(
            selected, index["true_fhir_ids"], row_number, "true_fhir_ids"
        )
        rows.append(
            _project_development_values(
                role=role,
                question_id=question_id,
                proc_query=proc_query,
                true_fhir_ids=true_fhir_ids,
            )
        )

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


def _split_header(source_bytes: bytes) -> tuple[list[str], bytes]:
    line_end = source_bytes.find(b"\n")
    if line_end < 0:
        raise ValueError("FHIR-AgentBench CSV is missing a header line")
    header_bytes = source_bytes[:line_end].rstrip(b"\r")
    header_text = header_bytes.decode("utf-8-sig")
    headers = next(csv.reader([header_text]))
    if not headers or any(not header for header in headers):
        raise ValueError("FHIR-AgentBench CSV has invalid headers")
    return headers, source_bytes[line_end + 1 :]


def _scan_selected_rows(
    body: bytes,
    *,
    field_count: int,
    selected_columns: frozenset[int],
    selected_rows: frozenset[int] | None = None,
) -> list[tuple[int, dict[int, str]]]:
    outputs: list[tuple[int, dict[int, str]]] = []
    row_number = 1
    field_index = 0
    row_values: dict[int, str] = {}
    in_quotes = False
    after_quote = False
    field_started = False
    buffer: bytearray | None = _selected_buffer(
        row_number, field_index, selected_columns, selected_rows
    )

    def finish_field() -> None:
        nonlocal field_index, buffer, field_started, after_quote
        if buffer is not None:
            row_values[field_index] = bytes(buffer).decode("utf-8").strip()
        field_index += 1
        field_started = False
        after_quote = False
        buffer = _selected_buffer(row_number, field_index, selected_columns, selected_rows)

    def finish_row() -> None:
        nonlocal row_number, field_index, row_values, buffer
        if field_index != field_count:
            raise ValueError(
                f"CSV row {row_number} field count drift: {field_index} != {field_count}"
            )
        if selected_rows is None or row_number in selected_rows:
            outputs.append((row_number, row_values))
        row_number += 1
        field_index = 0
        row_values = {}
        buffer = _selected_buffer(row_number, field_index, selected_columns, selected_rows)

    position = 0
    while position < len(body):
        byte = body[position]
        if in_quotes:
            if byte == 34:
                if position + 1 < len(body) and body[position + 1] == 34:
                    if buffer is not None:
                        buffer.append(34)
                    position += 2
                    continue
                in_quotes = False
                after_quote = True
                position += 1
                continue
            if buffer is not None:
                buffer.append(byte)
            position += 1
            continue

        if after_quote:
            if byte == 44:
                finish_field()
                position += 1
                continue
            if byte in {10, 13}:
                finish_field()
                finish_row()
                if byte == 13 and position + 1 < len(body) and body[position + 1] == 10:
                    position += 2
                else:
                    position += 1
                continue
            if byte in {9, 32}:
                position += 1
                continue
            raise ValueError(f"unexpected byte after quoted CSV field at row {row_number}")

        if byte == 34 and not field_started:
            in_quotes = True
            field_started = True
            position += 1
            continue
        if byte == 34:
            raise ValueError(f"unexpected quote in unquoted CSV field at row {row_number}")
        if byte == 44:
            finish_field()
            position += 1
            continue
        if byte in {10, 13}:
            finish_field()
            finish_row()
            if byte == 13 and position + 1 < len(body) and body[position + 1] == 10:
                position += 2
            else:
                position += 1
            continue
        field_started = True
        if buffer is not None:
            buffer.append(byte)
        position += 1

    if in_quotes:
        raise ValueError("unterminated quoted CSV field")
    if field_started or field_index or row_values:
        finish_field()
        finish_row()
    return outputs


def _selected_buffer(
    row_number: int,
    field_index: int,
    selected_columns: frozenset[int],
    selected_rows: frozenset[int] | None,
) -> bytearray | None:
    if field_index not in selected_columns:
        return None
    if selected_rows is not None and row_number not in selected_rows:
        return None
    return bytearray()


def _required_selected(
    selected: Mapping[int, str],
    field_index: int,
    row_number: int,
    field_name: str,
) -> str:
    value = selected.get(field_index, "")
    if not value:
        raise ValueError(f"empty {field_name} at row {row_number}")
    return value


def _membership_payload(
    rows: list[_SourceRow],
    roles_by_patient: Mapping[str, GAXRole],
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


def _project_development_values(
    *,
    role: D2ProjectionRole,
    question_id: str,
    proc_query: str,
    true_fhir_ids: str,
) -> D2FHIRDevelopmentProjectionRow:
    return D2FHIRDevelopmentProjectionRow(
        role=role,
        question_id_sha256=_identifier_digest(question_id),
        proc_query=proc_query,
        expected_resource_ids=_parse_expected_resource_ids(true_fhir_ids),
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
        json.dumps(row.model_dump(mode="json"), sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")
