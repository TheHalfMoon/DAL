import hashlib
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from gaxbench.study1_query_trace_gate import normalize_relative_fhir_get
from gaxbench.study1_recovery_runtime import (
    R1RecoveryRuntime,
    canonicalize_qualified_recovery_query,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(query):
    pattern = normalize_relative_fhir_get(query).pattern
    return {
        "safe_pattern": pattern,
        "source_pattern_sha256": hashlib.sha256(pattern.encode()).hexdigest(),
    }


def _runtime():
    resources = [
        {
            "resourceType": "Observation",
            "id": "a",
            "status": "preliminary",
            "subject": {"reference": "Patient/synthetic-dev"},
        },
        {
            "resourceType": "Observation",
            "id": "b",
            "status": "final",
            "subject": {"reference": "Patient/synthetic-dev"},
        },
        {
            "resourceType": "Observation",
            "id": "c",
            "status": "final",
            "subject": {"reference": "Patient/synthetic-sealed"},
        },
    ]
    return R1RecoveryRuntime.from_resources(
        resources,
        role="validation",
        development_patient_digests=frozenset({hashlib.sha256(b"synthetic-dev").hexdigest()}),
        synthetic_qualification=True,
    )


def test_status_precedes_count_and_sealed_resource_is_filtered():
    runtime = _runtime()
    query = "Observation?patient=synthetic-dev&status=final&_count=1"
    assert runtime._search(query) == ["Observation/b"]
    audit = runtime.exercise(query, source_entry=_entry(query))
    assert audit.disposition == "qualified-pass-through"
    assert audit.returned_resource_count == 1


@pytest.mark.parametrize(
    "query",
    [
        "Observation?patient=synthetic-sealed&status=final",
        "Observation?status=final",
        "Observation?patient=synthetic-dev&status=final&date=2020-01-01",
        "Observation?patient=synthetic-dev&status=final,amended",
        "Observation?patient=synthetic-dev&status=system|final",
        "Observation?patient=synthetic-dev&status=final&status=final",
        "Procedure?patient=synthetic-dev&status=completed",
        "Observation?patient=synthetic-dev&status:missing=true",
        "Observation?patient=synthetic-dev&date:gte=2020-01-01",
    ],
)
def test_unqualified_cases_remain_blocked(query):
    audit = _runtime().exercise(query, source_entry=_entry(query))
    assert audit.disposition == "hard-blocked"
    assert audit.returned_resource_count == 0


def test_lineage_is_exact_and_durable_audit_has_no_query_literals():
    query = "Observation?patient=synthetic-dev&status=final"
    entry = _entry(query)
    audit = _runtime().exercise(query, source_entry=entry)
    assert audit.original_request_sha256 == hashlib.sha256(query.encode()).hexdigest()
    assert audit.source_pattern_sha256 == entry["source_pattern_sha256"]
    serialized = json.dumps(asdict(audit))
    assert "synthetic-dev" not in serialized
    assert "canonical_query" not in serialized
    assert "raw_query" not in serialized
    entry["source_pattern_sha256"] = "0" * 64
    assert _runtime().exercise(query, source_entry=entry).blocker_codes == (
        "source-pattern-linkage-not-qualified",
    )


def test_empty_sibling_keeps_status_order_and_transformed_lineage():
    query = "Observation?status=final&status=&patient=synthetic-dev&_count=1"
    result = canonicalize_qualified_recovery_query(query, role="validation")
    assert result.canonical_query == "Observation?status=final&patient=synthetic-dev&_count=1"
    assert result.disposition == "recovery-transformed"
    assert result.original_request_sha256 == hashlib.sha256(query.encode()).hexdigest()
    audit = _runtime().exercise(query, source_entry=_entry(query))
    assert audit.recovery_transformed
    assert audit.returned_resource_count == 1


def test_final_role_cannot_construct_runtime():
    with pytest.raises(ValueError, match="development roles"):
        R1RecoveryRuntime.from_resources([], role="final", development_patient_digests=frozenset())


def test_normal_runtime_rejects_forged_fixture_entry_and_mutated_source(tmp_path):
    runtime = R1RecoveryRuntime.from_resources(
        [], role="calibration", development_patient_digests=frozenset()
    )
    assert len(runtime.source_entries) == 248
    query = "Observation?patient=synthetic-dev&status=final"
    result = runtime.exercise(query, source_entry=_entry(query))
    assert result.blocker_codes == ("source-pattern-linkage-not-qualified",)
    assert result.synthetic_qualification is False
    mutated = tmp_path / "mutated.json"
    mutated.write_text("{}")
    with pytest.raises(ValueError, match="digest mismatch"):
        R1RecoveryRuntime.from_resources(
            [],
            role="validation",
            development_patient_digests=frozenset(),
            source_evidence_path=mutated,
        )


def test_frozen_inventory_and_runtime_proof_reproduce_exactly():
    spec = importlib.util.spec_from_file_location(
        "r1_qualification", ROOT / "tools/qualify_sg000030_r1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inventory, qualification = module.build_evidence()
    for name, actual in (
        ("pattern_inventory", inventory),
        ("runtime_qualification", qualification),
    ):
        saved = (ROOT / f"registry/study1_sg000030_r1_{name}.json").read_bytes()
        assert saved.replace(b"\r\n", b"\n") == module.encoded(actual)
    assert sum(inventory["disposition_pattern_counts"].values()) == 248
    assert inventory["historical_blocker_rows_retained"] == 1239
    assert inventory["post_recovery_blocker_row_count"] is None
    assert qualification["case_count"] == 106
    assert qualification["new_model_inference_performed"] is False
    assert qualification["cloud_fhir_server_equivalence_claimed"] is False


def test_manifest_binds_exact_finite_implementation_and_proof():
    manifest = json.loads((ROOT / "registry/study1_sg000030_r1_manifest.json").read_text())
    for path, expected in manifest["bound_files"].items():
        content = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(content).hexdigest() == expected
    assert len(manifest["new_resource_parameter_pairs"]) == 2
    assert manifest["transformations"]["date_execution_qualified"] is False
    assert all(value is False for value in manifest["execution_boundary"].values())
    assert manifest["immutable_original"]["blocked_rows"] == 1239
