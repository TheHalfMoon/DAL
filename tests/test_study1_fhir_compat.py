from __future__ import annotations

import pytest
from pydantic import ValidationError

from gaxbench.study1_fhir_compat import (
    FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES,
    D2FHIRLocalStore,
    parse_relative_fhir_get,
    stable_resource_ids,
)


def _resources() -> list[dict[str, object]]:
    return [
        {"resourceType": "Patient", "id": "p1", "meta": {"versionId": "1"}},
        {
            "resourceType": "Encounter",
            "id": "e2",
            "subject": {"reference": "Patient/p1"},
            "meta": {"versionId": "2"},
            "text": {"status": "generated", "div": "<div>two</div>"},
        },
        {
            "resourceType": "Encounter",
            "id": "e1",
            "patient": {"reference": "p1"},
            "meta": {"versionId": "1"},
            "text": {"status": "generated", "div": "<div>one</div>"},
        },
        {"resourceType": "Encounter", "id": "e3", "subject": {"reference": "Patient/p2"}},
    ]


def test_frozen_resource_types_match_upstream_tool_surface() -> None:
    assert FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES == (
        "Patient",
        "Encounter",
        "Condition",
        "MedicationRequest",
        "Procedure",
        "Observation",
        "MedicationAdministration",
        "Location",
        "Specimen",
        "Medication",
    )


def test_parser_accepts_relative_get_and_decodes_parameters() -> None:
    request = parse_relative_fhir_get(
        "Encounter?patient=p1&_count=2",
        role="calibration",
    )
    assert request.resource_type == "Encounter"
    assert [(p.name, p.value) for p in request.parameters] == [
        ("patient", "p1"),
        ("_count", "2"),
    ]


@pytest.mark.parametrize(
    "query",
    [
        "https://example.test/Encounter?patient=p1",
        "/Encounter?patient=p1",
        "Encounter/e1",
        "Encounter?_count=0",
        "Encounter?_count=1&_count=2",
    ],
)
def test_parser_rejects_noncompatible_query_shapes(query: str) -> None:
    with pytest.raises(ValueError):
        parse_relative_fhir_get(query, role="validation")


def test_parser_mechanically_rejects_final_role() -> None:
    with pytest.raises(ValidationError):
        parse_relative_fhir_get("Encounter?patient=p1", role="test")  # type: ignore[arg-type]


def test_unknown_search_parameter_is_explicitly_unsupported() -> None:
    store = D2FHIRLocalStore(_resources())
    request = parse_relative_fhir_get("Encounter?date=2150", role="validation")
    result = store.search(request)
    assert result.status == "unsupported-semantics"
    assert result.unsupported_parameters == ["date"]
    assert result.resource_ids == []


def test_request_get_surface_groups_resources_and_honors_count() -> None:
    store = D2FHIRLocalStore(_resources())
    request = parse_relative_fhir_get(
        "Encounter?patient=p1&_count=1",
        role="calibration",
    )
    result = store.search(request, surface="request-get")
    assert result.status == "completed"
    assert result.resource_ids == ["Encounter/e1"]
    resource = result.resources_by_type["Encounter"][0]
    assert "meta" in resource
    assert "text" in resource


def test_resource_search_surface_collects_matches_and_strips_text_meta() -> None:
    store = D2FHIRLocalStore(_resources())
    request = parse_relative_fhir_get(
        "Encounter?patient=p1&_count=1",
        role="validation",
    )
    result = store.search(request, surface="resource-search")
    assert result.resource_ids == ["Encounter/e1", "Encounter/e2"]
    assert all(
        "meta" not in row and "text" not in row
        for row in result.resources_by_type["Encounter"]
    )


def test_resource_id_aliases_are_supported() -> None:
    store = D2FHIRLocalStore(_resources())
    for query in ("Encounter?id=e2", "Encounter?_id=e2"):
        result = store.search(parse_relative_fhir_get(query, role="validation"))
        assert result.resource_ids == ["Encounter/e2"]


def test_stable_resource_ids_are_sorted_and_duplicate_safe() -> None:
    resources = [
        {"resourceType": "Observation", "id": "z"},
        {"resourceType": "Encounter", "id": "a"},
    ]
    assert stable_resource_ids(resources) == ["Encounter/a", "Observation/z"]
    with pytest.raises(ValueError, match="duplicate"):
        stable_resource_ids([resources[0], resources[0]])


def test_local_store_rejects_duplicate_resource_identity() -> None:
    duplicate = {"resourceType": "Encounter", "id": "e1"}
    with pytest.raises(ValueError, match="duplicate FHIR resource identity"):
        D2FHIRLocalStore([duplicate, duplicate])


def test_status_artifact_keeps_real_dev_qualification_blocked() -> None:
    import json
    from pathlib import Path

    status = json.loads(
        Path("registry/study1_sg000026_fhir_compatibility_status.json").read_text(
            encoding="utf-8"
        )
    )
    qualification = status["development_role_qualification"]
    final_boundary = status["sealed_final_boundary"]
    assert status["evidence_class"] == "synthetic-mechanics-only"
    assert qualification["status"] == "blocked-input-unavailable-under-firewall"
    assert qualification["calibration_rows"] == 341
    assert qualification["validation_rows"] == 1122
    assert final_boundary["patients"] == 40
    assert final_boundary["rows"] == 173
    assert final_boundary["test_gold_serialized"] is False
    assert final_boundary["access"] == "sealed"
    assert final_boundary["accessed_by_this_grain"] is False


def test_patient_search_is_not_approximated_for_unproven_resource_type() -> None:
    store = D2FHIRLocalStore(_resources())
    request = parse_relative_fhir_get("Patient?patient=p1", role="validation")
    result = store.search(request)
    assert result.status == "unsupported-semantics"
    assert result.unsupported_parameters == ["patient"]
