from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl, urlsplit

from pydantic import Field, model_validator

from gaxbench import fhir_agentbench_qualification as fab
from gaxbench import study1_fhir_custodian as custodian
from gaxbench.fhir import validate_fhir_resource
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel
from gaxbench.study1_fhir_compat import (
    D2FHIRLocalStore,
    FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES,
    parse_relative_fhir_get,
)
from gaxbench.study1_fhir_runtime import (
    load_fhir_runtime_manifest,
    verify_fhir_runtime_root,
)

GateRole = Literal["calibration", "validation"]
GateStatus = Literal["supported", "behavior-changing-blocker"]
QueryMode = Literal["read", "search", "invalid"]

_PATIENT_SCOPED_TYPES = frozenset(
    {
        "Encounter",
        "Condition",
        "MedicationRequest",
        "Procedure",
        "Observation",
        "MedicationAdministration",
        "Specimen",
    }
)
_GLOBAL_TYPES = frozenset({"Location", "Medication"})
_LOCAL_SUPPORTED_PARAMETERS = frozenset({"id", "_id", "patient", "_count"})
_FHIR_COMPARATORS = frozenset({"eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"})


@dataclass(frozen=True)
class DevelopmentTraceInput:
    role: GateRole
    question_id_sha256: str
    input_text: str = field(repr=False)


@dataclass(frozen=True)
class GateRuntime:
    store: D2FHIRLocalStore = field(repr=False)
    identity_index: Mapping[str, Mapping[str, Any]] = field(repr=False)
    development_patient_digests: frozenset[str] = field(repr=False)


class DevelopmentTraceAudit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role_revision: str
    membership_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_rows: int = Field(ge=0)
    validation_rows: int = Field(ge=0)
    sealed_final_rows: int = Field(ge=0)
    shard_index: int = Field(ge=0)
    shard_count: int = Field(ge=1)
    selected_rows: int = Field(ge=0)
    selected_calibration_rows: int = Field(ge=0)
    selected_validation_rows: int = Field(ge=0)
    final_rows_materialized: Literal[0] = 0
    final_question_content_accessed: Literal[False] = False
    raw_questions_emitted: Literal[False] = False
    raw_patient_ids_emitted: Literal[False] = False

    @model_validator(mode="after")
    def validate_selected_counts(self) -> DevelopmentTraceAudit:
        if self.selected_rows != (
            self.selected_calibration_rows + self.selected_validation_rows
        ):
            raise ValueError("selected row accounting must close")
        return self


class NormalizedQuery(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    mode: QueryMode
    resource_type: str | None = None
    pattern: str
    parameter_names: list[str] = Field(default_factory=list)
    blocker_reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_blocking(self) -> NormalizedQuery:
        if self.mode == "invalid" and not self.blocker_reason_codes:
            raise ValueError("invalid query must retain a blocker reason")
        return self


class QueryExercise(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    pattern: str
    status: GateStatus
    returned_resource_count: int = Field(ge=0)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> QueryExercise:
        if self.status == "supported" and self.reason_codes:
            raise ValueError("supported query cannot retain blocker reasons")
        if self.status == "behavior-changing-blocker" and not self.reason_codes:
            raise ValueError("blocked query must retain reason codes")
        return self


def shard_for_question(question_id_sha256: str, shard_count: int) -> int:
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if len(question_id_sha256) != 64:
        raise ValueError("question_id_sha256 must be a full SHA-256 digest")
    try:
        value = int(question_id_sha256[:16], 16)
    except ValueError as exc:
        raise ValueError("question_id_sha256 must be hexadecimal") from exc
    return value % shard_count


def build_development_trace_inputs(
    source_path: Path,
    *,
    shard_index: int,
    shard_count: int,
) -> tuple[list[DevelopmentTraceInput], DevelopmentTraceAudit, frozenset[str]]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid shard coordinates")

    source_bytes = source_path.read_bytes()
    fab.verify_frozen_source(
        source_bytes,
        expected_blob_sha1=fab.FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
    )
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != fab.FHIR_AGENTBENCH_SOURCE_SHA256:
        raise ValueError("FHIR-AgentBench source SHA-256 drift")

    headers, body = custodian._split_header(source_bytes)
    if tuple(headers) != fab._EXPECTED_HEADERS:
        raise ValueError("FHIR-AgentBench header order drifted from frozen source")
    index = {name: headers.index(name) for name in headers}

    metadata_fields = frozenset(
        {index["split"], index["question_id"], index["patient_fhir_id"]}
    )
    metadata_rows = custodian._scan_selected_rows(
        body,
        field_count=len(headers),
        selected_columns=metadata_fields,
    )

    source_rows: list[fab._SourceRow] = []
    row_metadata: dict[int, tuple[str, str, str]] = {}
    for row_number, selected in metadata_rows:
        split = custodian._required_selected(
            selected,
            index["split"],
            row_number,
            "split",
        )
        question_id = custodian._required_selected(
            selected,
            index["question_id"],
            row_number,
            "question_id",
        )
        patient_id = custodian._required_selected(
            selected,
            index["patient_fhir_id"],
            row_number,
            "patient_fhir_id",
        )
        patient_digest = fab._identifier_digest(patient_id)
        row_metadata[row_number] = (split, question_id, patient_digest)
        source_rows.append(
            fab._SourceRow(
                upstream_split=split,
                question_id=question_id,
                question="",
                template="",
                patient_digest=patient_digest,
            )
        )

    if len({row.question_id for row in source_rows}) != len(source_rows):
        raise ValueError("FHIR-AgentBench question_id values must be unique")

    roles_by_patient = fab._assign_patient_roles(source_rows)
    membership_payload, role_counts = custodian._membership_payload(
        source_rows,
        roles_by_patient,
    )
    membership_sha256 = canonical_json_sha256(membership_payload)
    if membership_sha256 != custodian.CANONICAL_MEMBERSHIP_SHA256:
        raise ValueError("frozen role-membership digest mismatch")
    if role_counts["calibration"] != custodian.CANONICAL_CALIBRATION_ROWS:
        raise ValueError("calibration role count drift")
    if role_counts["validation"] != custodian.CANONICAL_VALIDATION_ROWS:
        raise ValueError("validation role count drift")
    if role_counts["test"] != custodian.CANONICAL_FINAL_ROWS:
        raise ValueError("sealed final role count drift")

    development_rows: dict[int, tuple[GateRole, str, str]] = {}
    development_patient_digests: set[str] = set()
    selected_row_numbers: set[int] = set()
    for row_number, (split, question_id, patient_digest) in row_metadata.items():
        role = roles_by_patient[patient_digest]
        if split == "test":
            continue
        if role == "calibration":
            gate_role: GateRole = "calibration"
        elif role == "validation":
            gate_role = "validation"
        else:
            continue
        question_digest = fab._identifier_digest(question_id)
        development_rows[row_number] = (gate_role, question_digest, patient_digest)
        development_patient_digests.add(patient_digest)
        if shard_for_question(question_digest, shard_count) == shard_index:
            selected_row_numbers.add(row_number)

    selected_fields = frozenset(
        {index["question"], index["assumption"], index["patient_fhir_id"]}
    )
    selected_rows = custodian._scan_selected_rows(
        body,
        field_count=len(headers),
        selected_columns=selected_fields,
        selected_rows=frozenset(selected_row_numbers),
    )

    inputs: list[DevelopmentTraceInput] = []
    selected_role_counts: Counter[str] = Counter()
    for row_number, selected in selected_rows:
        role, question_digest, patient_digest = development_rows[row_number]
        question = custodian._required_selected(
            selected,
            index["question"],
            row_number,
            "question",
        )
        patient_id = custodian._required_selected(
            selected,
            index["patient_fhir_id"],
            row_number,
            "patient_fhir_id",
        )
        if fab._identifier_digest(patient_id) != patient_digest:
            raise ValueError("development patient identity drift between custodian passes")
        assumption = selected.get(index["assumption"], "").strip()

        input_text = f"Question: {question}\nContext:\nPatient FHIR ID is {patient_id}."
        if assumption:
            input_text += f"\n{assumption}"
        inputs.append(
            DevelopmentTraceInput(
                role=role,
                question_id_sha256=question_digest,
                input_text=input_text,
            )
        )
        selected_role_counts[role] += 1

    inputs.sort(key=lambda item: item.question_id_sha256)
    audit = DevelopmentTraceAudit(
        source_sha256=source_sha256,
        role_revision=fab.FHIR_AGENTBENCH_ROLE_REVISION,
        membership_sha256=membership_sha256,
        calibration_rows=role_counts["calibration"],
        validation_rows=role_counts["validation"],
        sealed_final_rows=role_counts["test"],
        shard_index=shard_index,
        shard_count=shard_count,
        selected_rows=len(inputs),
        selected_calibration_rows=selected_role_counts["calibration"],
        selected_validation_rows=selected_role_counts["validation"],
    )
    return inputs, audit, frozenset(development_patient_digests)


def normalize_relative_fhir_get(query_string: str) -> NormalizedQuery:
    if not query_string or query_string != query_string.strip():
        return _invalid_query("invalid-empty-or-surrounding-whitespace")
    if any(character in query_string for character in ("\r", "\n")):
        return _invalid_query("invalid-multiline-query")

    parsed = urlsplit(query_string)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return _invalid_query("invalid-non-relative-query")
    if not parsed.path or parsed.path.startswith("/"):
        return _invalid_query("invalid-query-path")

    parts = parsed.path.split("/")
    if any(not part for part in parts):
        return _invalid_query("invalid-query-path")

    if len(parts) == 2:
        resource_type, _ = parts
        if parsed.query:
            return _invalid_query("unsupported-read-query-parameters")
        if resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
            return _invalid_query("unsupported-resource-type")
        return NormalizedQuery(
            mode="read",
            resource_type=resource_type,
            pattern=f"read:{resource_type}/{{id}}",
        )

    if len(parts) != 1:
        return _invalid_query("unsupported-nested-or-operation-path")

    resource_type = parts[0]
    if resource_type.startswith("$") or "_history" in resource_type:
        return _invalid_query("unsupported-operation-or-history")
    if resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
        return _invalid_query("unsupported-resource-type")

    parameters = parse_qsl(parsed.query, keep_blank_values=True)
    names = [name for name, _ in parameters]
    tokens = sorted(
        f"{name}=<{_value_class(name, value)}>" for name, value in parameters
    )
    suffix = f"?{'&'.join(tokens)}" if tokens else ""
    return NormalizedQuery(
        mode="search",
        resource_type=resource_type,
        pattern=f"search:{resource_type}{suffix}",
        parameter_names=sorted(names),
    )


def build_gate_runtime_from_resources(
    resources: Iterable[Mapping[str, Any]],
    *,
    development_patient_digests: frozenset[str],
) -> GateRuntime:
    filtered: list[dict[str, Any]] = []
    identity_index: dict[str, dict[str, Any]] = {}
    for raw in resources:
        resource = dict(raw)
        validate_fhir_resource(resource)
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not isinstance(resource_type, str) or not isinstance(resource_id, str):
            raise ValueError("runtime resource requires resourceType and id")
        if resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
            continue
        if not _resource_is_development_safe(
            resource,
            development_patient_digests=development_patient_digests,
        ):
            continue
        identity = f"{resource_type}/{resource_id}"
        if identity in identity_index:
            raise ValueError(f"duplicate runtime resource identity: {identity}")
        identity_index[identity] = resource
        filtered.append(resource)
    return GateRuntime(
        store=D2FHIRLocalStore(filtered),
        identity_index=identity_index,
        development_patient_digests=development_patient_digests,
    )


def load_verified_gate_runtime(
    runtime_root: Path,
    runtime_manifest_path: Path,
    *,
    development_patient_digests: frozenset[str],
) -> GateRuntime:
    manifest = load_fhir_runtime_manifest(runtime_manifest_path)
    verification = verify_fhir_runtime_root(runtime_root, manifest)
    if verification.status != "complete":
        raise ValueError("FHIR runtime checksum verification is incomplete")

    resources: list[dict[str, Any]] = []
    parse_failures = 0
    files = sorted(runtime_root.rglob("*.ndjson.gz")) + sorted(
        runtime_root.rglob("*.ndjson")
    )
    if not files:
        raise ValueError("verified FHIR runtime contains no NDJSON files")
    for path in files:
        opener: Any = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                    if not isinstance(value, dict):
                        raise ValueError("FHIR NDJSON row is not an object")
                    resources.append(value)
                except (json.JSONDecodeError, ValueError, TypeError):
                    parse_failures += 1
    if parse_failures:
        raise ValueError(f"FHIR runtime parse failures: {parse_failures}")
    return build_gate_runtime_from_resources(
        resources,
        development_patient_digests=development_patient_digests,
    )


def exercise_observed_query(
    query_string: str,
    *,
    role: GateRole,
    runtime: GateRuntime,
) -> QueryExercise:
    normalized = normalize_relative_fhir_get(query_string)
    if normalized.mode == "invalid":
        return QueryExercise(
            pattern=normalized.pattern,
            status="behavior-changing-blocker",
            returned_resource_count=0,
            reason_codes=normalized.blocker_reason_codes,
        )

    if normalized.mode == "read":
        resource_type, resource_id = urlsplit(query_string).path.split("/", 1)
        if resource_type == "Patient":
            if fab._identifier_digest(resource_id) not in runtime.development_patient_digests:
                return _blocked(
                    normalized.pattern,
                    "read-target-outside-development-role",
                )
        identity = f"{resource_type}/{resource_id}"
        if identity not in runtime.identity_index:
            return _blocked(
                normalized.pattern,
                "direct-read-not-development-scoped-or-missing",
            )
        return QueryExercise(
            pattern=normalized.pattern,
            status="supported",
            returned_resource_count=1,
        )

    unsupported_names = sorted(
        set(normalized.parameter_names) - _LOCAL_SUPPORTED_PARAMETERS
    )
    if unsupported_names:
        return QueryExercise(
            pattern=normalized.pattern,
            status="behavior-changing-blocker",
            returned_resource_count=0,
            reason_codes=[
                f"unsupported-parameter:{name}" for name in unsupported_names
            ],
        )

    scope_blocker = _search_scope_blocker(
        query_string,
        resource_type=normalized.resource_type or "",
        runtime=runtime,
    )
    if scope_blocker is not None:
        return _blocked(normalized.pattern, scope_blocker)

    try:
        request = parse_relative_fhir_get(query_string, role=role)
    except ValueError:
        return _blocked(normalized.pattern, "local-parser-rejected-observed-query")

    result = runtime.store.search(request, surface="request-get")
    if result.status != "completed":
        reasons = [
            f"unsupported-parameter:{name}" for name in result.unsupported_parameters
        ]
        return QueryExercise(
            pattern=normalized.pattern,
            status="behavior-changing-blocker",
            returned_resource_count=0,
            reason_codes=reasons,
        )
    return QueryExercise(
        pattern=normalized.pattern,
        status="supported",
        returned_resource_count=len(result.resource_ids),
    )


def _invalid_query(reason: str) -> NormalizedQuery:
    return NormalizedQuery(
        mode="invalid",
        pattern=f"invalid:{reason}",
        blocker_reason_codes=[reason],
    )


def _value_class(name: str, value: str) -> str:
    if name == "_count":
        return "positive-int" if value.isdigit() and int(value) > 0 else "invalid-count"
    if name in {"id", "_id"}:
        return "id-list" if "," in value else "id"
    if name == "patient":
        return "patient-reference" if value.startswith("Patient/") else "patient-id"
    if len(value) >= 2 and value[:2] in _FHIR_COMPARATORS:
        return "comparator"
    if "|" in value:
        return "token"
    if "/" in value:
        return "reference"
    if "," in value:
        return "list"
    if not value:
        return "empty"
    return "value"


def _resource_is_development_safe(
    resource: Mapping[str, Any],
    *,
    development_patient_digests: frozenset[str],
) -> bool:
    resource_type = str(resource.get("resourceType", ""))
    if resource_type == "Patient":
        resource_id = resource.get("id")
        return isinstance(resource_id, str) and (
            fab._identifier_digest(resource_id) in development_patient_digests
        )
    if resource_type in _GLOBAL_TYPES:
        return True
    if resource_type not in _PATIENT_SCOPED_TYPES:
        return False
    patient_ids = _resource_patient_ids(resource)
    if not patient_ids:
        return False
    return all(
        fab._identifier_digest(patient_id) in development_patient_digests
        for patient_id in patient_ids
    )


def _resource_patient_ids(resource: Mapping[str, Any]) -> set[str]:
    patient_ids: set[str] = set()
    for field_name in ("patient", "subject"):
        value = resource.get(field_name)
        if not isinstance(value, Mapping):
            continue
        reference = value.get("reference")
        if not isinstance(reference, str):
            continue
        if reference.startswith("Patient/") and len(reference) > len("Patient/"):
            patient_ids.add(reference[len("Patient/") :])
        elif reference:
            patient_ids.add(reference)
    return patient_ids


def _search_scope_blocker(
    query_string: str,
    *,
    resource_type: str,
    runtime: GateRuntime,
) -> str | None:
    if resource_type in _GLOBAL_TYPES:
        return None

    parsed = urlsplit(query_string)
    parameters = parse_qsl(parsed.query, keep_blank_values=True)
    patient_values = [value for name, value in parameters if name == "patient"]
    id_values = [value for name, value in parameters if name in {"id", "_id"}]

    if patient_values:
        for value in patient_values:
            patient_id = value[len("Patient/") :] if value.startswith("Patient/") else value
            if fab._identifier_digest(patient_id) not in runtime.development_patient_digests:
                return "search-target-outside-development-role"
        return None

    if resource_type == "Patient" and id_values:
        for value in id_values:
            for patient_id in value.split(","):
                if fab._identifier_digest(patient_id) not in runtime.development_patient_digests:
                    return "search-target-outside-development-role"
        return None

    if id_values:
        for value in id_values:
            for resource_id in value.split(","):
                identity = f"{resource_type}/{resource_id}"
                if identity not in runtime.identity_index:
                    return "resource-id-not-development-scoped-or-missing"
        return None

    return "unscoped-search-role-firewall"


def _blocked(pattern: str, reason: str) -> QueryExercise:
    return QueryExercise(
        pattern=pattern,
        status="behavior-changing-blocker",
        returned_resource_count=0,
        reason_codes=[reason],
    )
