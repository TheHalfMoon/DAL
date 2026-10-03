from __future__ import annotations

from gaxbench.fhir_agentbench_qualification import _identifier_digest
from gaxbench.study1_query_trace_gate import (
    build_gate_runtime_from_resources,
    exercise_observed_query,
    normalize_relative_fhir_get,
    shard_for_question,
)


def _runtime():
    development = frozenset({_identifier_digest("p1")})
    resources = [
        {"resourceType": "Patient", "id": "p1"},
        {"resourceType": "Patient", "id": "p2"},
        {
            "resourceType": "Encounter",
            "id": "e1",
            "subject": {"reference": "Patient/p1"},
        },
        {
            "resourceType": "Encounter",
            "id": "e2",
            "subject": {"reference": "Patient/p2"},
        },
        {"resourceType": "Medication", "id": "m1"},
    ]
    return build_gate_runtime_from_resources(
        resources,
        development_patient_digests=development,
    )


def test_query_normalization_masks_patient_and_resource_values() -> None:
    search = normalize_relative_fhir_get(
        "Encounter?patient=super-secret-patient&_count=2"
    )
    assert search.mode == "search"
    assert search.pattern == (
        "search:Encounter?_count=<positive-int>&patient=<patient-id>"
    )
    assert "super-secret-patient" not in search.pattern

    direct = normalize_relative_fhir_get("Patient/super-secret-patient")
    assert direct.mode == "read"
    assert direct.pattern == "read:Patient/{id}"
    assert "super-secret-patient" not in direct.pattern


def test_unsupported_search_parameter_is_behavior_changing_blocker() -> None:
    result = exercise_observed_query(
        "Encounter?date=2150",
        role="validation",
        runtime=_runtime(),
    )
    assert result.status == "behavior-changing-blocker"
    assert result.pattern == "search:Encounter?date=<value>"
    assert result.reason_codes == ["unsupported-parameter:date"]


def test_development_scoped_patient_search_is_supported() -> None:
    result = exercise_observed_query(
        "Encounter?patient=p1&_count=5",
        role="calibration",
        runtime=_runtime(),
    )
    assert result.status == "supported"
    assert result.returned_resource_count == 1
    assert result.reason_codes == []


def test_outside_development_patient_is_blocked_and_not_materialized() -> None:
    runtime = _runtime()
    assert "Patient/p2" not in runtime.identity_index
    assert "Encounter/e2" not in runtime.identity_index

    result = exercise_observed_query(
        "Patient/p2",
        role="validation",
        runtime=runtime,
    )
    assert result.status == "behavior-changing-blocker"
    assert result.reason_codes == ["read-target-outside-development-role"]


def test_unscoped_patient_resource_search_is_blocked() -> None:
    result = exercise_observed_query(
        "Encounter?_count=5",
        role="validation",
        runtime=_runtime(),
    )
    assert result.status == "behavior-changing-blocker"
    assert result.reason_codes == ["unscoped-search-role-firewall"]


def test_resource_id_search_is_supported_only_for_development_safe_identity() -> None:
    runtime = _runtime()
    supported = exercise_observed_query(
        "Encounter?_id=e1",
        role="validation",
        runtime=runtime,
    )
    blocked = exercise_observed_query(
        "Encounter?_id=e2",
        role="validation",
        runtime=runtime,
    )
    assert supported.status == "supported"
    assert supported.returned_resource_count == 1
    assert blocked.status == "behavior-changing-blocker"
    assert blocked.reason_codes == ["resource-id-not-development-scoped-or-missing"]


def test_global_reference_resources_can_be_read_without_patient_scope() -> None:
    result = exercise_observed_query(
        "Medication/m1",
        role="calibration",
        runtime=_runtime(),
    )
    assert result.status == "supported"
    assert result.returned_resource_count == 1


def test_shard_assignment_is_deterministic_and_bounded() -> None:
    digest = _identifier_digest("question-123")
    observed = shard_for_question(digest, 8)
    assert 0 <= observed < 8
    assert shard_for_question(digest, 8) == observed
