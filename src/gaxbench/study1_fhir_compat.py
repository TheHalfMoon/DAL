from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Literal
from urllib.parse import parse_qsl, urlsplit

from pydantic import Field, JsonValue, model_validator

from gaxbench.fhir import validate_fhir_resource
from gaxbench.schema import StrictModel

D2FHIRRole = Literal["calibration", "validation"]
D2FHIRSurface = Literal["request-get", "resource-search"]
D2FHIRSearchStatus = Literal["completed", "unsupported-semantics"]

FROZEN_FHIR_AGENTBENCH_REVISION = "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES = (
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
_SUPPORTED_PARAMETERS = frozenset({"id", "_id", "patient", "_count"})
_PATIENT_REFERENCE_RESOURCE_TYPES = frozenset(
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


class D2FHIRSearchParameter(StrictModel):
    name: str = Field(min_length=1)
    value: str


class D2FHIRSearchRequest(StrictModel):
    """Validated relative FHIR GET request on a permitted D2 development role."""

    schema_version: Literal["0.1"] = "0.1"
    role: D2FHIRRole
    resource_type: str = Field(min_length=1)
    raw_query: str = Field(min_length=1)
    parameters: list[D2FHIRSearchParameter]

    @model_validator(mode="after")
    def validate_request(self) -> D2FHIRSearchRequest:
        if self.resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
            raise ValueError(
                f"unsupported frozen FHIR-AgentBench resource type: {self.resource_type}"
            )
        return self


class D2FHIRSearchResult(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    role: D2FHIRRole
    resource_type: str
    surface: D2FHIRSurface
    status: D2FHIRSearchStatus
    resource_ids: list[str]
    resources_by_type: dict[str, list[dict[str, JsonValue]]]
    unsupported_parameters: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> D2FHIRSearchResult:
        if self.status == "completed" and self.unsupported_parameters:
            raise ValueError("completed FHIR search cannot retain unsupported parameters")
        if self.status == "unsupported-semantics" and not self.unsupported_parameters:
            raise ValueError("unsupported FHIR search must name unsupported parameters")
        if self.resource_ids != sorted(self.resource_ids):
            raise ValueError("resource_ids must use deterministic lexical order")
        return self


class D2FHIRLocalStore:
    """Read-only compatibility surface for synthetic D2 fixtures only."""

    def __init__(self, resources: Iterable[Mapping[str, JsonValue]]) -> None:
        indexed: dict[tuple[str, str], dict[str, JsonValue]] = {}
        for raw_resource in resources:
            resource = dict(raw_resource)
            validate_fhir_resource(resource)
            resource_type_value = resource.get("resourceType")
            if not isinstance(resource_type_value, str):
                raise ValueError("D2 local FHIR resource requires a string resourceType")
            resource_type = resource_type_value
            resource_id = resource.get("id")
            if not isinstance(resource_id, str) or not resource_id:
                raise ValueError("D2 local FHIR resources require a non-empty id")
            if resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
                raise ValueError(f"resource type is outside frozen tool surface: {resource_type}")
            key = (resource_type, resource_id)
            if key in indexed:
                raise ValueError(f"duplicate FHIR resource identity: {resource_type}/{resource_id}")
            indexed[key] = resource
        self._resources = indexed

    def search(
        self,
        request: D2FHIRSearchRequest,
        *,
        surface: D2FHIRSurface = "request-get",
    ) -> D2FHIRSearchResult:
        unsupported_names = {
            parameter.name
            for parameter in request.parameters
            if parameter.name not in _SUPPORTED_PARAMETERS
        }
        if (
            any(parameter.name == "patient" for parameter in request.parameters)
            and request.resource_type not in _PATIENT_REFERENCE_RESOURCE_TYPES
        ):
            unsupported_names.add("patient")
        unsupported = sorted(unsupported_names)
        if unsupported:
            return D2FHIRSearchResult(
                role=request.role,
                resource_type=request.resource_type,
                surface=surface,
                status="unsupported-semantics",
                resource_ids=[],
                resources_by_type={},
                unsupported_parameters=unsupported,
            )

        candidates = [
            dict(resource)
            for (resource_type, _), resource in self._resources.items()
            if resource_type == request.resource_type
        ]
        for parameter in request.parameters:
            if parameter.name in {"id", "_id"}:
                identifiers = {part for part in parameter.value.split(",") if part}
                candidates = [
                    resource for resource in candidates if resource.get("id") in identifiers
                ]
            elif parameter.name == "patient":
                candidates = [
                    resource
                    for resource in candidates
                    if _matches_patient(request.resource_type, resource, parameter.value)
                ]

        candidates.sort(key=lambda resource: str(resource["id"]))
        count = _count_parameter(request.parameters)
        if surface == "request-get" and count is not None:
            candidates = candidates[:count]

        materialized = [
            _materialize_resource(resource, surface=surface) for resource in candidates
        ]
        resource_ids = sorted(
            f"{resource['resourceType']}/{resource['id']}" for resource in materialized
        )
        return D2FHIRSearchResult(
            role=request.role,
            resource_type=request.resource_type,
            surface=surface,
            status="completed",
            resource_ids=resource_ids,
            resources_by_type=_group_resources(materialized),
        )


def parse_relative_fhir_get(
    query_string: str,
    *,
    role: D2FHIRRole,
) -> D2FHIRSearchRequest:
    """Parse the frozen benchmark's relative GET query shape without network access."""

    if not query_string or query_string != query_string.strip():
        raise ValueError("FHIR query string must be non-empty and have no surrounding whitespace")
    if any(character in query_string for character in ("\r", "\n")):
        raise ValueError("FHIR query string must be single-line")

    parsed = urlsplit(query_string)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise ValueError("D2 accepts relative FHIR GET query strings only")
    path = parsed.path
    if not path or path.startswith("/") or "/" in path:
        raise ValueError("D2 FHIR query path must be exactly one resource type")
    if path.startswith("$") or "_history" in path:
        raise ValueError(
            "FHIR operations and history access are outside the D2 read-only search surface"
        )

    parameters = [
        D2FHIRSearchParameter(name=name, value=value)
        for name, value in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    request = D2FHIRSearchRequest(
        role=role,
        resource_type=path,
        raw_query=query_string,
        parameters=parameters,
    )
    _count_parameter(parameters)
    return request


def stable_resource_ids(
    resources: Iterable[Mapping[str, JsonValue]],
) -> list[str]:
    """Serialize resource identities deterministically as ResourceType/id strings."""

    identities: list[str] = []
    for resource in resources:
        validate_fhir_resource(resource)
        resource_type = resource["resourceType"]
        resource_id = resource.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError("stable FHIR resource-ID serialization requires resource.id")
        identities.append(f"{resource_type}/{resource_id}")
    if len(identities) != len(set(identities)):
        raise ValueError("stable FHIR resource-ID serialization rejects duplicate identities")
    return sorted(identities)


def _count_parameter(parameters: Iterable[D2FHIRSearchParameter]) -> int | None:
    values = [parameter.value for parameter in parameters if parameter.name == "_count"]
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("D2 FHIR search accepts at most one _count parameter")
    try:
        count = int(values[0])
    except ValueError as exc:
        raise ValueError("_count must be a positive integer") from exc
    if count < 1:
        raise ValueError("_count must be a positive integer")
    return count


def _matches_patient(
    resource_type: str,
    resource: Mapping[str, JsonValue],
    patient_id: str,
) -> bool:
    if not patient_id:
        return False
    if resource_type not in _PATIENT_REFERENCE_RESOURCE_TYPES:
        return False
    wanted = {patient_id, f"Patient/{patient_id}"}
    return any(reference in wanted for reference in _patient_references(resource))


def _patient_references(resource: Mapping[str, JsonValue]) -> tuple[str, ...]:
    references: list[str] = []
    for field in ("patient", "subject"):
        value = resource.get(field)
        if isinstance(value, dict):
            reference = value.get("reference")
            if isinstance(reference, str):
                references.append(reference)
    return tuple(references)


def _materialize_resource(
    resource: dict[str, JsonValue],
    *,
    surface: D2FHIRSurface,
) -> dict[str, JsonValue]:
    materialized = dict(resource)
    if surface == "resource-search":
        materialized.pop("text", None)
        materialized.pop("meta", None)
    return materialized


def _group_resources(
    resources: Iterable[dict[str, JsonValue]],
) -> dict[str, list[dict[str, JsonValue]]]:
    grouped: dict[str, list[dict[str, JsonValue]]] = {}
    for resource in resources:
        resource_type = str(resource["resourceType"])
        grouped.setdefault(resource_type, []).append(resource)
    return {resource_type: grouped[resource_type] for resource_type in sorted(grouped)}
