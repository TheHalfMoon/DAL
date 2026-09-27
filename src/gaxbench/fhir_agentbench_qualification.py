from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.schema import StrictModel

FHIR_AGENTBENCH_REPOSITORY = "glee4810/FHIR-AgentBench"
FHIR_AGENTBENCH_SOURCE_COMMIT = "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
FHIR_AGENTBENCH_SOURCE_PATH = "final_dataset/questions_answers_sql_fhir.csv"
FHIR_AGENTBENCH_SOURCE_BLOB_SHA1 = "b2225370feeaefe962c27c4d90f911584e098ac2"
FHIR_AGENTBENCH_REPOSITORY_LICENSE = "CC-BY-4.0"
FHIR_AGENTBENCH_SOURCE_FHIR_VERSION = "R4"
FHIR_AGENTBENCH_RAW_URL = (
    "https://raw.githubusercontent.com/"
    f"{FHIR_AGENTBENCH_REPOSITORY}/{FHIR_AGENTBENCH_SOURCE_COMMIT}/"
    f"{FHIR_AGENTBENCH_SOURCE_PATH}"
)

EHRSQL_REPOSITORY = "glee4810/ehrsql-2024"
EHRSQL_LICENSE = "CC-BY-4.0"
EHRSQL_LATEST_COMMIT_BEFORE_FHIR_FREEZE = "1886034a8846dede2e8513a2ee16149c65a46fcf"
MIMIC_IV_DEMO_LICENSE = "ODbL-1.0"

_REQUIRED_COLUMNS = frozenset({"split", "question_id", "question"})
_SENSITIVE_COLUMNS = frozenset(
    {
        "true_answer",
        "sql_query",
        "true_fhir_ids",
        "patient_fhir_id",
    }
)


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
        if len(self.source_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.source_sha256
        ):
            raise ValueError("source_sha256 must be a lowercase SHA-256 digest")
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
    source_bytes = source_path.read_bytes()
    verify_frozen_source(source_bytes, expected_blob_sha1=expected_blob_sha1)

    split_counts: dict[str, int] = defaultdict(int)
    missing_by_column: dict[str, int] = defaultdict(int)
    question_id_counts: dict[str, int] = defaultdict(int)
    patient_splits: dict[str, set[str]] = defaultdict(set)
    patient_ids_by_split: dict[str, set[str]] = defaultdict(set)
    question_splits: dict[str, set[str]] = defaultdict(set)
    template_splits: dict[str, set[str]] = defaultdict(set)
    row_count = 0

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

        for raw_row in reader:
            row_count += 1
            row: dict[str, str] = {}
            for raw_key, raw_value in raw_row.items():
                if raw_key is None:
                    raise ValueError(f"row {row_count} has fields beyond the declared header")
                if isinstance(raw_value, list):
                    raise ValueError(f"row {row_count} has malformed repeated field data")
                row[raw_key.strip()] = (raw_value or "").strip()

            split = row["split"]
            question_id = row["question_id"]
            question = row["question"]
            if not split:
                raise ValueError(f"row {row_count} has empty split")
            if not question_id:
                raise ValueError(f"row {row_count} has empty question_id")
            if not question:
                raise ValueError(f"row {row_count} has empty question")

            split_counts[split] += 1
            question_id_counts[question_id] += 1
            for header in headers:
                if not row.get(header, ""):
                    missing_by_column[header] += 1

            question_splits[_fingerprint_text(question)].add(split)
            template = row.get("template", "")
            if template:
                template_splits[_fingerprint_text(template)].add(split)

            patient_id = row.get("patient_fhir_id", "")
            if patient_id:
                patient_digest = _identifier_digest(patient_id)
                patient_splits[patient_digest].add(split)
                patient_ids_by_split[split].add(patient_digest)

    if row_count == 0:
        raise ValueError("FHIR-AgentBench CSV must contain at least one data row")

    return FHIRAgentBenchSourceProbe(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_bytes=len(source_bytes),
        headers=headers,
        row_count=row_count,
        split_counts=dict(sorted(split_counts.items())),
        unique_question_ids=len(question_id_counts),
        duplicate_question_id_count=sum(
            1 for count in question_id_counts.values() if count > 1
        ),
        missing_by_column={
            header: missing_by_column.get(header, 0) for header in headers
        },
        unique_patient_fhir_ids_by_split={
            split: len(ids) for split, ids in sorted(patient_ids_by_split.items())
        },
        cross_split_patient_identity_count=_cross_split_group_count(patient_splits),
        cross_split_exact_question_count=_cross_split_group_count(question_splits),
        cross_split_template_count=_cross_split_group_count(template_splits),
    )


def report_exposes_sensitive_content(report: FHIRAgentBenchSourceProbe) -> bool:
    payload = report.model_dump(mode="json")
    serialized_keys = set(payload)
    if serialized_keys & _SENSITIVE_COLUMNS:
        return True
    return any(
        (
            report.raw_rows_serialized,
            report.raw_questions_serialized,
            report.raw_answers_serialized,
            report.raw_patient_identifiers_serialized,
        )
    )


def _cross_split_group_count(groups: dict[str, set[str]]) -> int:
    return sum(1 for splits in groups.values() if len(splits) > 1)


def _fingerprint_text(value: str) -> str:
    normalized = " ".join(value.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _identifier_digest(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
