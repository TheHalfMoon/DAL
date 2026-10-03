from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from pydantic import Field, model_validator

from gaxbench.fhir import validate_fhir_resource
from gaxbench.schema import StrictModel
from gaxbench.study1_fhir_compat import D2FHIRLocalStore, parse_relative_fhir_get
from gaxbench.study1_fhir_runtime import load_fhir_runtime_manifest, verify_fhir_runtime_root

CANONICAL_PROJECTION_SHA256 = "a09357620e811de49dd868773854e4f48e742a3882110c2f6228633ad161aae7"
CANONICAL_CALIBRATION_ROWS = 341
CANONICAL_VALIDATION_ROWS = 1122
CANONICAL_ROWS_WITH_EXPECTED_IDS = 1087
CANONICAL_ROWS_WITHOUT_EXPECTED_IDS = 376
CANONICAL_REFERENCE_COUNT = 21527
CANONICAL_UNIQUE_EXPECTED_RESOURCES = 14178

_ALLOWED_ROW_KEYS = frozenset(
    {"schema_version", "role", "question_id_sha256", "proc_query", "expected_resource_ids"}
)


class D2FHIRDirectIDQualification(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    study: Literal["DAL Study 1"] = "DAL Study 1"
    specgrain: Literal["SG-000026"] = "SG-000026"
    stage: Literal["D2"] = "D2"
    evidence_class: Literal["real-development-direct-id-only"] = "real-development-direct-id-only"
    status: Literal["partial-pass-direct-id-only", "partial-fail-direct-id"]
    projection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_rows: int = Field(ge=0)
    validation_rows: int = Field(ge=0)
    rows_with_expected_ids: int = Field(ge=0)
    rows_without_expected_ids: int = Field(ge=0)
    requested_reference_count: int = Field(ge=0)
    unique_expected_resource_count: int = Field(ge=0)
    resolved_reference_count: int = Field(ge=0)
    missing_reference_count: int = Field(ge=0)
    missing_reference_sha256s: list[str]
    exact_match_rows: int = Field(ge=0)
    mismatch_rows: int = Field(ge=0)
    runtime_parse_failure_count: int = Field(ge=0)
    resource_type_reference_counts: dict[str, int]
    exercised_query_patterns: list[str]
    query_trace_coverage: Literal["blocked-unavailable-from-authorized-projection"] = (
        "blocked-unavailable-from-authorized-projection"
    )
    query_trace_blocker_reason: str
    d2_closeout_allowed: Literal[False] = False
    later_stages_activated: Literal[False] = False
    sealed_final_rows_accessed: Literal[False] = False
    model_selection_performed: Literal[False] = False
    training_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_accounting(self) -> D2FHIRDirectIDQualification:
        if self.calibration_rows + self.validation_rows != (
            self.rows_with_expected_ids + self.rows_without_expected_ids
        ):
            raise ValueError("development row accounting must close")
        if (
            self.resolved_reference_count + self.missing_reference_count
            != self.requested_reference_count
        ):
            raise ValueError("reference accounting must close")
        if self.exact_match_rows + self.mismatch_rows != self.rows_with_expected_ids:
            raise ValueError("row comparison accounting must close")
        return self


def _projection_bytes(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as handle:
            return handle.read()
    return path.read_bytes()


def _load_projection(
    path: Path,
    *,
    expected_sha256: str,
    expected_calibration_rows: int,
    expected_validation_rows: int,
) -> tuple[list[dict[str, Any]], str]:
    payload = _projection_bytes(path)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"development projection SHA-256 mismatch: {digest} != {expected_sha256}")

    rows: list[dict[str, Any]] = []
    roles: Counter[str] = Counter()
    for line_number, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != _ALLOWED_ROW_KEYS:
            raise ValueError(f"development projection field drift at line {line_number}")
        role = row.get("role")
        if role not in {"calibration", "validation"}:
            raise ValueError("development projection contains a non-development role")
        roles[role] += 1
        rows.append(row)
    if roles["calibration"] != expected_calibration_rows:
        raise ValueError("development calibration row count drift")
    if roles["validation"] != expected_validation_rows:
        raise ValueError("development validation row count drift")
    return rows, digest


def _expected_refs(rows: list[dict[str, Any]]) -> tuple[set[str], Counter[str], int, int, int]:
    unique: set[str] = set()
    types: Counter[str] = Counter()
    rows_with = 0
    rows_without = 0
    total = 0
    for row in rows:
        expected = row["expected_resource_ids"]
        if not isinstance(expected, list) or any(not isinstance(item, str) for item in expected):
            raise ValueError("expected_resource_ids must be a list of strings")
        if expected != sorted(expected) or len(expected) != len(set(expected)):
            raise ValueError("expected_resource_ids must be sorted and unique per row")
        if expected:
            rows_with += 1
        else:
            rows_without += 1
        for item in expected:
            if "/" not in item:
                raise ValueError("expected resource identity must be ResourceType/id")
            resource_type, resource_id = item.split("/", 1)
            if not resource_type or not resource_id:
                raise ValueError("expected resource identity must be ResourceType/id")
            types[resource_type] += 1
            unique.add(item)
            total += 1
    return unique, types, rows_with, rows_without, total


def _load_wanted_resources(
    root: Path,
    wanted: set[str],
) -> tuple[dict[str, dict[str, Any]], int]:
    found: dict[str, dict[str, Any]] = {}
    parse_failures = 0
    files = sorted(root.rglob("*.ndjson.gz")) + sorted(root.rglob("*.ndjson"))
    if not files:
        raise RuntimeError("no FHIR NDJSON files found in verified runtime")
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
                    resource_type = value.get("resourceType")
                    resource_id = value.get("id")
                    if not isinstance(resource_type, str) or not isinstance(resource_id, str):
                        raise ValueError("FHIR resource requires resourceType and id")
                    key = f"{resource_type}/{resource_id}"
                    if key in wanted:
                        validate_fhir_resource(value)
                        found[key] = value
                except (json.JSONDecodeError, ValueError, TypeError):
                    parse_failures += 1
    return found, parse_failures


def qualify_real_development_direct_ids(
    projection_path: Path,
    runtime_root: Path,
    runtime_manifest_path: Path,
    *,
    expected_projection_sha256: str = CANONICAL_PROJECTION_SHA256,
    expected_calibration_rows: int = CANONICAL_CALIBRATION_ROWS,
    expected_validation_rows: int = CANONICAL_VALIDATION_ROWS,
) -> D2FHIRDirectIDQualification:
    runtime_manifest = load_fhir_runtime_manifest(runtime_manifest_path)
    runtime_verification = verify_fhir_runtime_root(runtime_root, runtime_manifest)
    if runtime_verification.status != "complete":
        raise ValueError("FHIR runtime checksum verification is incomplete")

    rows, projection_sha256 = _load_projection(
        projection_path,
        expected_sha256=expected_projection_sha256,
        expected_calibration_rows=expected_calibration_rows,
        expected_validation_rows=expected_validation_rows,
    )
    wanted, type_counts, rows_with, rows_without, requested_refs = _expected_refs(rows)
    resources, parse_failures = _load_wanted_resources(runtime_root, wanted)
    missing = sorted(wanted - set(resources))
    store = D2FHIRLocalStore(resources.values())

    exact_rows = 0
    mismatch_rows = 0
    resolved_references = 0
    for row in rows:
        expected = row["expected_resource_ids"]
        if not expected:
            continue
        retrieved: set[str] = set()
        for identity in expected:
            resource_type, resource_id = identity.split("/", 1)
            request = parse_relative_fhir_get(
                f"{resource_type}?id={quote(resource_id, safe='-._~')}",
                role=row["role"],
            )
            result = store.search(request, surface="resource-search")
            if result.status != "completed":
                continue
            returned = set(result.resource_ids)
            if identity in returned:
                resolved_references += 1
            retrieved.update(returned)
        if retrieved == set(expected):
            exact_rows += 1
        else:
            mismatch_rows += 1

    semantic_pass = not missing and not mismatch_rows and parse_failures == 0
    missing_hashes = [hashlib.sha256(item.encode("utf-8")).hexdigest() for item in missing]
    return D2FHIRDirectIDQualification(
        status="partial-pass-direct-id-only" if semantic_pass else "partial-fail-direct-id",
        projection_sha256=projection_sha256,
        calibration_rows=sum(row["role"] == "calibration" for row in rows),
        validation_rows=sum(row["role"] == "validation" for row in rows),
        rows_with_expected_ids=rows_with,
        rows_without_expected_ids=rows_without,
        requested_reference_count=requested_refs,
        unique_expected_resource_count=len(wanted),
        resolved_reference_count=resolved_references,
        missing_reference_count=requested_refs - resolved_references,
        missing_reference_sha256s=missing_hashes,
        exact_match_rows=exact_rows,
        mismatch_rows=mismatch_rows,
        runtime_parse_failure_count=parse_failures,
        resource_type_reference_counts=dict(sorted(type_counts.items())),
        exercised_query_patterns=["resource-search:ResourceType?id=<expected-resource-id>"],
        query_trace_blocker_reason=(
            "The founder-authorized Option A projection contains development proc_query SQL and "
            "expected resource IDs, but no development question text or benchmark agent tool-call "
            "traces. Upstream FHIR-AgentBench agents generate query strings dynamically. "
            "D2 therefore cannot honestly claim coverage of every query/search pattern "
            "observed on governed roles "
            "from this projection alone."
        ),
    )


def write_qualification(path: Path, report: D2FHIRDirectIDQualification) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = _args()
    report = qualify_real_development_direct_ids(
        Path(args.projection),
        Path(args.runtime_root),
        Path(args.runtime_manifest),
    )
    write_qualification(Path(args.output), report)
    print(
        json.dumps(
            {
                "status": report.status,
                "rows_with_expected_ids": report.rows_with_expected_ids,
                "rows_without_expected_ids": report.rows_without_expected_ids,
                "requested_reference_count": report.requested_reference_count,
                "resolved_reference_count": report.resolved_reference_count,
                "mismatch_rows": report.mismatch_rows,
                "query_trace_coverage": report.query_trace_coverage,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
