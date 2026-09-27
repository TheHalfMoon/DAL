from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

FHIR_AGENTBENCH_REPOSITORY = "glee4810/FHIR-AgentBench"
FHIR_AGENTBENCH_SOURCE_COMMIT = "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
FHIR_AGENTBENCH_SOURCE_PATH = "final_dataset/questions_answers_sql_fhir.csv"
FHIR_AGENTBENCH_SOURCE_BLOB_SHA1 = "b2225370feeaefe962c27c4d90f911584e098ac2"
FHIR_AGENTBENCH_SOURCE_SHA256 = "e2045692fef7f5f4f77496935160f5fc727e162d213e94feed61401948e512a0"
FHIR_AGENTBENCH_REPOSITORY_LICENSE = "CC-BY-4.0"
FHIR_AGENTBENCH_SOURCE_FHIR_VERSION = "R4"
FHIR_AGENTBENCH_EXPECTED_ROWS = 2931
FHIR_AGENTBENCH_EXPECTED_PATIENTS = 94
FHIR_AGENTBENCH_CALIBRATION_PATIENTS = 14
FHIR_AGENTBENCH_VALIDATION_PATIENTS = 40
FHIR_AGENTBENCH_TEST_PATIENTS = 40
FHIR_AGENTBENCH_NEAR_DUPLICATE_SHINGLES = 5
FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD = 0.80
FHIR_AGENTBENCH_ROLE_REVISION = "gax-fhir-agentbench-patient-disjoint-v0.2"
FHIR_AGENTBENCH_RAW_URL = (
    "https://raw.githubusercontent.com/"
    f"{FHIR_AGENTBENCH_REPOSITORY}/{FHIR_AGENTBENCH_SOURCE_COMMIT}/"
    f"{FHIR_AGENTBENCH_SOURCE_PATH}"
)

EHRSQL_REPOSITORY = "glee4810/ehrsql-2024"
EHRSQL_LICENSE = "CC-BY-4.0"
EHRSQL_LATEST_COMMIT_BEFORE_FHIR_FREEZE = "1886034a8846dede2e8513a2ee16149c65a46fcf"
MIMIC_IV_DEMO_LICENSE = "ODbL-1.0"

_REQUIRED_COLUMNS = frozenset({"split", "question_id", "question", "patient_fhir_id"})
_EXPECTED_HEADERS = (
    "split",
    "question_id",
    "question",
    "sql_query",
    "true_answer",
    "assumption",
    "patient_fhir_id",
    "template",
    "val_dict",
    "proc_query",
    "main_table_name",
    "mappable_to_fhir",
    "true_fhir_ids",
)
_SENSITIVE_COLUMNS = frozenset(
    {
        "true_answer",
        "sql_query",
        "true_fhir_ids",
        "patient_fhir_id",
    }
)

GAXRole = Literal["calibration", "validation", "test"]
ExclusionReason = Literal[
    "upstream-test-row-for-non-test-patient",
    "non-test-row-for-test-patient",
]


@dataclass(frozen=True)
class _SourceRow:
    upstream_split: str
    question_id: str
    question: str
    template: str
    patient_digest: str


class FHIRAgentBenchSourceProbe(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["fhir-agentbench"] = "fhir-agentbench"
    source_repository: Literal["glee4810/FHIR-AgentBench"] = "glee4810/FHIR-AgentBench"
    source_commit: Literal["bbb42909a5a7eb907d1cd91f72a560729e7037ea"] = (
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    )
    source_path: Literal["final_dataset/questions_answers_sql_fhir.csv"] = (
        "final_dataset/questions_answers_sql_fhir.csv"
    )
    source_blob_sha1: Literal["b2225370feeaefe962c27c4d90f911584e098ac2"] = (
        "b2225370feeaefe962c27c4d90f911584e098ac2"
    )
    source_sha256: str
    source_bytes: int = Field(ge=1)
    source_fhir_version: Literal["R4"] = "R4"
    headers: list[str]
    row_count: int = Field(ge=1)
    split_counts: dict[str, int]
    unique_question_ids: int = Field(ge=1)
    duplicate_question_id_count: int = Field(ge=0)
    missing_by_column: dict[str, int]
    unique_patient_fhir_ids_by_split: dict[str, int]
    cross_split_patient_identity_count: int = Field(ge=0)
    cross_split_exact_question_count: int = Field(ge=0)
    cross_split_template_count: int = Field(ge=0)
    repository_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    ehrsql_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    mimic_iv_demo_license: Literal["ODbL-1.0"] = "ODbL-1.0"
    ehrsql_generation_revision_proven: Literal[False] = False
    temporal_ehrsql_revision: Literal["1886034a8846dede2e8513a2ee16149c65a46fcf"] = (
        "1886034a8846dede2e8513a2ee16149c65a46fcf"
    )
    temporal_ehrsql_revision_is_generation_proof: Literal[False] = False
    raw_rows_serialized: Literal[False] = False
    raw_questions_serialized: Literal[False] = False
    raw_answers_serialized: Literal[False] = False
    raw_patient_identifiers_serialized: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_probe(self) -> FHIRAgentBenchSourceProbe:
        _require_sha256(self.source_sha256, "source_sha256")
        if len(self.headers) != len(set(self.headers)):
            raise ValueError("CSV headers must be unique")
        missing_required = _REQUIRED_COLUMNS - set(self.headers)
        if missing_required:
            raise ValueError(f"missing required CSV columns: {sorted(missing_required)}")
        if sum(self.split_counts.values()) != self.row_count:
            raise ValueError("split_counts must sum to row_count")
        if any(count < 0 for count in self.missing_by_column.values()):
            raise ValueError("missing counts must be non-negative")
        return self


class FHIRAgentBenchRoleManifest(StrictModel):
    schema_version: Literal["0.2"] = "0.2"
    dataset_id: Literal["fhir-agentbench"] = "fhir-agentbench"
    role_revision: Literal["gax-fhir-agentbench-patient-disjoint-v0.2"] = (
        "gax-fhir-agentbench-patient-disjoint-v0.2"
    )
    patient_identity: Literal["sha256-normalized-patient-fhir-id"] = (
        "sha256-normalized-patient-fhir-id"
    )
    assignment_rule: Literal[
        "first-40-upstream-test-patients-by-sha256-test;"
        "remaining-first-14-calibration;remaining-40-validation"
    ] = (
        "first-40-upstream-test-patients-by-sha256-test;"
        "remaining-first-14-calibration;remaining-40-validation"
    )
    row_inclusion_rule: Literal[
        "test-role-keeps-upstream-test-only;non-test-roles-keep-train-valid-only"
    ] = "test-role-keeps-upstream-test-only;non-test-roles-keep-train-valid-only"
    patient_count: Literal[94] = 94
    calibration_patient_count: Literal[14] = 14
    validation_patient_count: Literal[40] = 40
    test_patient_count: Literal[40] = 40
    calibration_row_count: int = Field(ge=1)
    validation_row_count: int = Field(ge=1)
    test_row_count: int = Field(ge=1)
    excluded_row_count: int = Field(ge=0)
    excluded_upstream_test_for_non_test_role_count: int = Field(ge=0)
    excluded_non_test_for_test_role_count: int = Field(ge=0)
    membership_sha256: str
    upstream_split_counts: dict[str, int]
    upstream_split_preserved_as_metadata: Literal[True] = True
    gax_test_rows_are_upstream_test_only: Literal[True] = True
    upstream_test_rows_reassigned_to_non_test_roles: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"
    test_gold_serialized: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> FHIRAgentBenchRoleManifest:
        _require_sha256(self.membership_sha256, "membership_sha256")
        included = self.calibration_row_count + self.validation_row_count + self.test_row_count
        if included + self.excluded_row_count != FHIR_AGENTBENCH_EXPECTED_ROWS:
            raise ValueError("included plus excluded rows must cover all frozen rows")
        excluded_parts = (
            self.excluded_upstream_test_for_non_test_role_count
            + self.excluded_non_test_for_test_role_count
        )
        if excluded_parts != self.excluded_row_count:
            raise ValueError("excluded-row reasons must sum to excluded_row_count")
        return self


class FHIRAgentBenchLeakageAudit(StrictModel):
    schema_version: Literal["0.2"] = "0.2"
    dataset_id: Literal["fhir-agentbench"] = "fhir-agentbench"
    role_revision: Literal["gax-fhir-agentbench-patient-disjoint-v0.2"] = (
        "gax-fhir-agentbench-patient-disjoint-v0.2"
    )
    upstream_cross_split_patient_identity_count: int = Field(ge=0)
    upstream_cross_split_exact_question_count: int = Field(ge=0)
    upstream_cross_split_template_count: int = Field(ge=0)
    gax_cross_role_patient_identity_count: int = Field(ge=0)
    gax_cross_role_exact_question_count: int = Field(ge=0)
    gax_cross_role_template_count: int = Field(ge=0)
    gax_cross_role_near_duplicate_question_pair_count: int = Field(ge=0)
    near_duplicate_normalization: Literal["lowercase-unicode-word-tokens"] = (
        "lowercase-unicode-word-tokens"
    )
    near_duplicate_shingle_size: Literal[5] = 5
    near_duplicate_jaccard_threshold: float = Field(default=0.8, ge=0.8, le=0.8)
    patient_disjoint: bool
    non_test_roles_contain_upstream_test_rows: Literal[False] = False
    test_role_contains_non_test_rows: Literal[False] = False
    benchmark_native_template_overlap_disclosed: Literal[True] = True
    public_benchmark_pretraining_contamination: Literal["unresolved-public-benchmark"] = (
        "unresolved-public-benchmark"
    )
    ehrsql_generation_revision_proven: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"
    test_tuning_forbidden: Literal[True] = True


class FHIRAgentBenchQualificationReport(StrictModel):
    schema_version: Literal["0.2"] = "0.2"
    dataset_id: Literal["fhir-agentbench"] = "fhir-agentbench"
    source_sha256: str
    source_blob_sha1: Literal["b2225370feeaefe962c27c4d90f911584e098ac2"] = (
        "b2225370feeaefe962c27c4d90f911584e098ac2"
    )
    source_commit: Literal["bbb42909a5a7eb907d1cd91f72a560729e7037ea"] = (
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    )
    role_revision: Literal["gax-fhir-agentbench-patient-disjoint-v0.2"] = (
        "gax-fhir-agentbench-patient-disjoint-v0.2"
    )
    row_count: Literal[2931] = 2931
    role_manifest_sha256: str
    leakage_audit_sha256: str
    status: Literal["qualified", "blocked"]
    redistribution_from_gax: Literal["metadata-only"] = "metadata-only"
    repository_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    ehrsql_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    mimic_iv_demo_license: Literal["ODbL-1.0"] = "ODbL-1.0"
    ehrsql_generation_revision_proven: Literal[False] = False
    public_source_contains_test_supervision: Literal[True] = True
    qualification_logic_uses_test_supervision: Literal[False] = False
    upstream_test_rows_reassigned_to_non_test_roles: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_hashes(self) -> FHIRAgentBenchQualificationReport:
        _require_sha256(self.source_sha256, "source_sha256")
        _require_sha256(self.role_manifest_sha256, "role_manifest_sha256")
        _require_sha256(self.leakage_audit_sha256, "leakage_audit_sha256")
        return self


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_frozen_source(
    data: bytes,
    *,
    expected_blob_sha1: str = FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
) -> None:
    actual = git_blob_sha1(data)
    if actual != expected_blob_sha1:
        raise ValueError(
            "FHIR-AgentBench source Git blob mismatch: "
            f"expected {expected_blob_sha1}, got {actual}"
        )


def probe_frozen_source(
    path: str | Path,
    *,
    expected_blob_sha1: str = FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
) -> FHIRAgentBenchSourceProbe:
    source_path = Path(path)
    source_bytes, headers, rows, missing_by_column = _read_source(
        source_path,
        expected_blob_sha1=expected_blob_sha1,
    )

    split_counts: dict[str, int] = defaultdict(int)
    question_id_counts: dict[str, int] = defaultdict(int)
    patient_splits: dict[str, set[str]] = defaultdict(set)
    patient_ids_by_split: dict[str, set[str]] = defaultdict(set)
    question_splits: dict[str, set[str]] = defaultdict(set)
    template_splits: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        split_counts[row.upstream_split] += 1
        question_id_counts[row.question_id] += 1
        patient_splits[row.patient_digest].add(row.upstream_split)
        patient_ids_by_split[row.upstream_split].add(row.patient_digest)
        question_splits[_fingerprint_text(row.question)].add(row.upstream_split)
        if row.template:
            template_splits[_fingerprint_text(row.template)].add(row.upstream_split)

    return FHIRAgentBenchSourceProbe(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_bytes=len(source_bytes),
        headers=headers,
        row_count=len(rows),
        split_counts=dict(sorted(split_counts.items())),
        unique_question_ids=len(question_id_counts),
        duplicate_question_id_count=sum(
            1 for count in question_id_counts.values() if count > 1
        ),
        missing_by_column=missing_by_column,
        unique_patient_fhir_ids_by_split={
            split: len(ids) for split, ids in sorted(patient_ids_by_split.items())
        },
        cross_split_patient_identity_count=_cross_split_group_count(patient_splits),
        cross_split_exact_question_count=_cross_split_group_count(question_splits),
        cross_split_template_count=_cross_split_group_count(template_splits),
    )


def qualify_frozen_source(
    path: str | Path,
) -> tuple[
    FHIRAgentBenchSourceProbe,
    FHIRAgentBenchRoleManifest,
    FHIRAgentBenchLeakageAudit,
    FHIRAgentBenchQualificationReport,
]:
    probe = probe_frozen_source(path)
    if probe.source_sha256 != FHIR_AGENTBENCH_SOURCE_SHA256:
        raise ValueError(
            "FHIR-AgentBench source SHA-256 mismatch: "
            f"expected {FHIR_AGENTBENCH_SOURCE_SHA256}, got {probe.source_sha256}"
        )
    if probe.headers != list(_EXPECTED_HEADERS):
        raise ValueError("FHIR-AgentBench frozen CSV header differs from the qualified schema")
    if probe.row_count != FHIR_AGENTBENCH_EXPECTED_ROWS:
        raise ValueError("FHIR-AgentBench frozen row count differs from the qualified source")
    if probe.duplicate_question_id_count:
        raise ValueError("FHIR-AgentBench question_id values must be unique")

    _, _, rows, _ = _read_source(Path(path))
    roles_by_patient = _assign_patient_roles(rows)
    rows_with_roles, excluded = _included_rows_with_roles(rows, roles_by_patient)

    role_counts: dict[GAXRole, int] = {"calibration": 0, "validation": 0, "test": 0}
    membership_payload: list[dict[str, str]] = []
    included_ids: set[str] = set()
    for row, role in rows_with_roles:
        role_counts[role] += 1
        question_digest = _identifier_digest(row.question_id)
        included_ids.add(question_digest)
        membership_payload.append(
            {
                "question_id_sha256": question_digest,
                "patient_identity_sha256": row.patient_digest,
                "membership": role,
            }
        )

    for row in rows:
        question_digest = _identifier_digest(row.question_id)
        if question_digest in included_ids:
            continue
        assigned_role = roles_by_patient[row.patient_digest]
        reason = _exclusion_reason(row, assigned_role)
        membership_payload.append(
            {
                "question_id_sha256": question_digest,
                "patient_identity_sha256": row.patient_digest,
                "membership": "excluded",
                "reason": reason,
            }
        )
    membership_payload.sort(key=lambda entry: entry["question_id_sha256"])

    manifest = FHIRAgentBenchRoleManifest(
        calibration_row_count=role_counts["calibration"],
        validation_row_count=role_counts["validation"],
        test_row_count=role_counts["test"],
        excluded_row_count=sum(excluded.values()),
        excluded_upstream_test_for_non_test_role_count=excluded[
            "upstream-test-row-for-non-test-patient"
        ],
        excluded_non_test_for_test_role_count=excluded["non-test-row-for-test-patient"],
        membership_sha256=canonical_json_sha256(membership_payload),
        upstream_split_counts=probe.split_counts,
    )

    gax_patient_roles: dict[str, set[str]] = defaultdict(set)
    gax_question_roles: dict[str, set[str]] = defaultdict(set)
    gax_template_roles: dict[str, set[str]] = defaultdict(set)
    non_test_roles_contain_upstream_test_rows = False
    test_role_contains_non_test_rows = False
    for row, role in rows_with_roles:
        gax_patient_roles[row.patient_digest].add(role)
        gax_question_roles[_fingerprint_text(row.question)].add(role)
        if row.template:
            gax_template_roles[_fingerprint_text(row.template)].add(role)
        if role in {"calibration", "validation"} and row.upstream_split == "test":
            non_test_roles_contain_upstream_test_rows = True
        if role == "test" and row.upstream_split != "test":
            test_role_contains_non_test_rows = True

    if non_test_roles_contain_upstream_test_rows or test_role_contains_non_test_rows:
        raise ValueError(
            "FHIR-AgentBench role policy leaked rows across the upstream test boundary"
        )

    audit = FHIRAgentBenchLeakageAudit(
        upstream_cross_split_patient_identity_count=probe.cross_split_patient_identity_count,
        upstream_cross_split_exact_question_count=probe.cross_split_exact_question_count,
        upstream_cross_split_template_count=probe.cross_split_template_count,
        gax_cross_role_patient_identity_count=_cross_split_group_count(gax_patient_roles),
        gax_cross_role_exact_question_count=_cross_split_group_count(gax_question_roles),
        gax_cross_role_template_count=_cross_split_group_count(gax_template_roles),
        gax_cross_role_near_duplicate_question_pair_count=_near_duplicate_pair_count(
            rows_with_roles
        ),
        patient_disjoint=_cross_split_group_count(gax_patient_roles) == 0,
        non_test_roles_contain_upstream_test_rows=False,
        test_role_contains_non_test_rows=False,
    )

    role_manifest_sha256 = canonical_json_sha256(manifest.model_dump(mode="json"))
    leakage_audit_sha256 = canonical_json_sha256(audit.model_dump(mode="json"))
    status: Literal["qualified", "blocked"] = (
        "qualified"
        if audit.patient_disjoint
        and audit.gax_cross_role_exact_question_count == 0
        and probe.duplicate_question_id_count == 0
        else "blocked"
    )
    report = FHIRAgentBenchQualificationReport(
        source_sha256=probe.source_sha256,
        role_manifest_sha256=role_manifest_sha256,
        leakage_audit_sha256=leakage_audit_sha256,
        status=status,
    )
    return probe, manifest, audit, report


def report_exposes_sensitive_content(report: StrictModel) -> bool:
    payload = report.model_dump(mode="json")
    serialized_keys = set(payload)
    if serialized_keys & _SENSITIVE_COLUMNS:
        return True
    raw_flags = (
        payload.get("raw_rows_serialized"),
        payload.get("raw_questions_serialized"),
        payload.get("raw_answers_serialized"),
        payload.get("raw_patient_identifiers_serialized"),
    )
    return any(flag is True for flag in raw_flags)


def _read_source(
    source_path: Path,
    *,
    expected_blob_sha1: str = FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
) -> tuple[bytes, list[str], list[_SourceRow], dict[str, int]]:
    source_bytes = source_path.read_bytes()
    verify_frozen_source(source_bytes, expected_blob_sha1=expected_blob_sha1)

    missing_by_column: dict[str, int] = defaultdict(int)
    rows: list[_SourceRow] = []
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("FHIR-AgentBench CSV must contain a header row")
        headers = [header.strip() for header in reader.fieldnames]
        if any(not header for header in headers):
            raise ValueError("FHIR-AgentBench CSV headers must be non-empty")
        if len(headers) != len(set(headers)):
            raise ValueError("FHIR-AgentBench CSV headers must be unique")
        missing_required = _REQUIRED_COLUMNS - set(headers)
        if missing_required:
            raise ValueError(f"missing required CSV columns: {sorted(missing_required)}")

        for row_number, raw_row in enumerate(reader, start=1):
            row: dict[str, str] = {}
            for raw_key, raw_value in raw_row.items():
                if raw_key is None:
                    raise ValueError(f"row {row_number} has fields beyond the declared header")
                if isinstance(raw_value, list):
                    raise ValueError(f"row {row_number} has malformed repeated field data")
                row[raw_key.strip()] = (raw_value or "").strip()

            for header in headers:
                if not row.get(header, ""):
                    missing_by_column[header] += 1

            split = row["split"]
            question_id = row["question_id"]
            question = row["question"]
            patient_id = row["patient_fhir_id"]
            if not split:
                raise ValueError(f"row {row_number} has empty split")
            if not question_id:
                raise ValueError(f"row {row_number} has empty question_id")
            if not question:
                raise ValueError(f"row {row_number} has empty question")
            if not patient_id:
                raise ValueError(f"row {row_number} has empty patient_fhir_id")

            rows.append(
                _SourceRow(
                    upstream_split=split,
                    question_id=question_id,
                    question=question,
                    template=row.get("template", ""),
                    patient_digest=_identifier_digest(patient_id),
                )
            )

    if not rows:
        raise ValueError("FHIR-AgentBench CSV must contain at least one data row")
    return (
        source_bytes,
        headers,
        rows,
        {header: missing_by_column.get(header, 0) for header in headers},
    )


def _assign_patient_roles(rows: list[_SourceRow]) -> dict[str, GAXRole]:
    patient_digests = sorted({row.patient_digest for row in rows})
    if len(patient_digests) != FHIR_AGENTBENCH_EXPECTED_PATIENTS:
        raise ValueError(f"expected {FHIR_AGENTBENCH_EXPECTED_PATIENTS} unique patients")

    test_candidates = sorted(
        {row.patient_digest for row in rows if row.upstream_split == "test"}
    )
    if len(test_candidates) < FHIR_AGENTBENCH_TEST_PATIENTS:
        raise ValueError("not enough upstream-test patient identities for the frozen test role")

    test_patients = set(test_candidates[:FHIR_AGENTBENCH_TEST_PATIENTS])
    non_test_patients = [patient for patient in patient_digests if patient not in test_patients]
    if len(non_test_patients) != (
        FHIR_AGENTBENCH_CALIBRATION_PATIENTS + FHIR_AGENTBENCH_VALIDATION_PATIENTS
    ):
        raise ValueError("frozen patient partition does not match preregistered role counts")

    calibration_patients = set(non_test_patients[:FHIR_AGENTBENCH_CALIBRATION_PATIENTS])
    validation_patients = set(non_test_patients[FHIR_AGENTBENCH_CALIBRATION_PATIENTS :])

    roles: dict[str, GAXRole] = {}
    for patient in patient_digests:
        if patient in test_patients:
            roles[patient] = "test"
        elif patient in calibration_patients:
            roles[patient] = "calibration"
        elif patient in validation_patients:
            roles[patient] = "validation"
        else:
            raise ValueError("patient was not assigned to a GAX role")
    return roles


def _included_rows_with_roles(
    rows: list[_SourceRow],
    roles_by_patient: dict[str, GAXRole],
) -> tuple[list[tuple[_SourceRow, GAXRole]], dict[ExclusionReason, int]]:
    included: list[tuple[_SourceRow, GAXRole]] = []
    excluded: dict[ExclusionReason, int] = {
        "upstream-test-row-for-non-test-patient": 0,
        "non-test-row-for-test-patient": 0,
    }
    for row in rows:
        role = roles_by_patient[row.patient_digest]
        if role == "test" and row.upstream_split == "test":
            included.append((row, role))
        elif role in {"calibration", "validation"} and row.upstream_split != "test":
            included.append((row, role))
        else:
            excluded[_exclusion_reason(row, role)] += 1
    return included, excluded


def _exclusion_reason(row: _SourceRow, role: GAXRole) -> ExclusionReason:
    if role == "test" and row.upstream_split != "test":
        return "non-test-row-for-test-patient"
    if role in {"calibration", "validation"} and row.upstream_split == "test":
        return "upstream-test-row-for-non-test-patient"
    raise ValueError("row does not require exclusion under the frozen role policy")


def _near_duplicate_pair_count(rows_with_roles: list[tuple[_SourceRow, GAXRole]]) -> int:
    prepared = [(role, _text_shingles(row.question)) for row, role in rows_with_roles]
    count = 0
    for left_index, (left_role, left_shingles) in enumerate(prepared):
        for right_role, right_shingles in prepared[left_index + 1 :]:
            if left_role == right_role:
                continue
            maximum = max(len(left_shingles), len(right_shingles))
            minimum = min(len(left_shingles), len(right_shingles))
            if maximum == 0 or minimum / maximum < FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD:
                continue
            intersection = len(left_shingles & right_shingles)
            union_size = len(left_shingles) + len(right_shingles) - intersection
            if union_size == 0:
                continue
            if intersection / union_size >= FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD:
                count += 1
    return count


def _text_shingles(text: str) -> frozenset[tuple[str, ...]]:
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    if not tokens:
        return frozenset()
    size = FHIR_AGENTBENCH_NEAR_DUPLICATE_SHINGLES
    if len(tokens) < size:
        return frozenset({tuple(tokens)})
    return frozenset(
        tuple(tokens[index : index + size]) for index in range(len(tokens) - size + 1)
    )


def _cross_split_group_count(groups: dict[str, set[str]]) -> int:
    return sum(1 for splits in groups.values() if len(splits) > 1)


def _fingerprint_text(value: str) -> str:
    normalized = " ".join(value.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _identifier_digest(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
