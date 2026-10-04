"""Deterministic R1 proof on invented fixtures and persisted safe identities only."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from gaxbench.study1_query_trace_gate import normalize_relative_fhir_get
from gaxbench.study1_recovery_compat import classify_persisted_source_pattern
from gaxbench.study1_recovery_runtime import R1_RUNTIME_VERSION, STATUS_VALUES, R1RecoveryRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "registry/study1_sg000028_execution_37156028113.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def synthetic_entry(query: str) -> dict[str, Any]:
    pattern = normalize_relative_fhir_get(query).pattern
    return {"safe_pattern": pattern, "source_pattern_sha256": digest(pattern.encode())}


def fixtures() -> list[dict[str, Any]]:
    # Intentionally invented fixtures: no benchmark source, questions, answers, or IDs.
    return [
        {
            "resourceType": resource,
            "id": f"synthetic-{i:02}",
            "status": status,
            "subject": {"reference": "Patient/synthetic-patient"},
        }
        for resource, statuses in sorted(STATUS_VALUES.items())
        for i, status in enumerate(sorted(statuses))
    ]


def qualify_runtime() -> dict[str, Any]:
    resources = fixtures()
    patient_hash = digest(b"synthetic-patient")
    runtime = R1RecoveryRuntime.from_resources(
        resources,
        role="calibration",
        development_patient_digests=frozenset({patient_hash}),
        synthetic_qualification=True,
    )
    cases = []
    for resource, statuses in sorted(STATUS_VALUES.items()):
        for status in sorted(statuses):
            for count in (None, 1, 2):
                for patient in ("synthetic-patient", "Patient/synthetic-patient"):
                    query = f"{resource}?patient={patient}&status={status}"
                    if count is not None:
                        query += f"&_count={count}"
                    # Independent normative scalar-token reference projection.
                    expected = sorted(
                        f"{r['resourceType']}/{r['id']}"
                        for r in resources
                        if r["resourceType"] == resource and r["status"] == status
                    )
                    if count is not None:
                        expected = expected[:count]
                    canonical = runtime.exercise(query, source_entry=synthetic_entry(query))
                    actual = runtime._search(query)
                    assert actual == expected
                    assert canonical.disposition == "qualified-pass-through"
                    assert canonical.returned_resource_count == len(expected)
                    cases.append(asdict(canonical))
    # Equivalence to unchanged frozen D2 for the inherited surface, not a cloud-server claim.
    for resource in sorted(STATUS_VALUES):
        query = f"{resource}?patient=synthetic-patient&_count=2"
        from gaxbench.study1_fhir_compat import parse_relative_fhir_get

        frozen = runtime.gate.store.search(parse_relative_fhir_get(query, role="calibration"))
        assert runtime._search(query) == frozen.resource_ids
    # Adversarial cases include scope, token shape, other pairs, dates, and opaque identity.
    blocked = [
        "Observation?patient=sealed-synthetic&status=final",
        "Observation?status=final",
        "Observation?patient=synthetic-patient&status=final,amended",
        "Observation?patient=synthetic-patient&status=system|final",
        "Observation?patient=synthetic-patient&status=final&status=final",
        "Encounter?patient=synthetic-patient&status=finished",
        "Observation?patient=synthetic-patient&date:gte=2020-01-01",
        "Observation?patient=synthetic-patient&code=x",
        "Observation?patient=synthetic-patient&opaqueSecret=value",
    ]
    for query in blocked:
        audit = runtime.exercise(query, source_entry=synthetic_entry(query))
        assert audit.disposition == "hard-blocked"
        assert audit.returned_resource_count == 0
        cases.append(asdict(audit))
    empty_query = "Observation?patient=synthetic-patient&status=&_count=2"
    empty = runtime.exercise(empty_query, source_entry=synthetic_entry(empty_query))
    assert empty.disposition == "recovery-transformed"
    assert empty.original_request_sha256 == digest(empty_query.encode())
    assert empty.returned_resource_count == 2
    cases.append(asdict(empty))
    return {
        "runtime_version": R1_RUNTIME_VERSION,
        "synthetic_only": True,
        "cases": cases,
        "case_count": len(cases),
        "scalar_token_oracle_equivalence_cases": 96,
        "inherited_d2_equivalence_cases": 2,
        "cloud_fhir_server_equivalence_claimed": False,
        "normative_oracle_scope": (
            "Two exact scalar status code searches only; no token systems, OR, modifiers, "
            "repeated non-empty status, dates, sorting, includes, or references added."
        ),
        "new_model_inference_performed": False,
        "raw_benchmark_source_accessed": False,
        "final_role_content_accessed": False,
    }


def classify_inventory(entry: dict[str, Any]) -> str:
    disposition = classify_persisted_source_pattern(entry)
    if disposition == "resource-specific-support-pending":
        pattern = entry["safe_pattern"]
        resource, _, query = pattern.removeprefix("search:").partition("?")
        names = {part.partition("=")[0] for part in query.split("&")}
        if resource in STATUS_VALUES and names <= {"id", "_id", "patient", "_count", "status"}:
            return "scalar-status-support-candidate"
    return disposition


def build_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    source_bytes = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    source = json.loads(source_bytes)
    entries = source["pattern_support_evidence"]
    assert len(entries) == len({e["source_pattern_sha256"] for e in entries}) == 248
    inventory = [dict(entry, r1_disposition=classify_inventory(entry)) for entry in entries]
    inventory.sort(key=lambda entry: entry["source_pattern_sha256"])
    counts = dict(sorted(Counter(e["r1_disposition"] for e in inventory).items()))
    record = {
        "schema_version": "study1-r1-safe-inventory-v1",
        "source_path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": digest(source_bytes),
        "runtime_version": R1_RUNTIME_VERSION,
        "pattern_count": 248,
        "disposition_pattern_counts": counts,
        "inventory": inventory,
        "call_level_causal_attribution_claimed": False,
        "candidate_means_executable_or_recovered": False,
        "historical_blocker_rows_retained": 1239,
        "post_recovery_blocker_row_count": None,
        "post_recovery_blocker_count_requires_separately_authorized_r2": True,
    }
    return record, qualify_runtime()


if __name__ == "__main__":
    inventory, qualification = build_evidence()
    for name, value in (
        ("study1_sg000030_r1_pattern_inventory.json", inventory),
        ("study1_sg000030_r1_runtime_qualification.json", qualification),
    ):
        (ROOT / "registry" / name).write_bytes(encoded(value))
    print(
        json.dumps(
            {
                "patterns": 248,
                "runtime_cases": qualification["case_count"],
                "dispositions": inventory["disposition_pattern_counts"],
            }
        )
    )
