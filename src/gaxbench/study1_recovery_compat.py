from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import quote_plus

from pydantic import Field, model_validator

from gaxbench.schema import StrictModel
from gaxbench.study1_fhir_compat import (
    FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES,
    D2FHIRRole,
    parse_relative_fhir_get,
)

R1Disposition = Literal[
    "qualified-pass-through",
    "recovery-transformed",
    "hard-blocked",
]
R1PatternDisposition = Literal[
    "observed-pass-through",
    "comparison-transform-candidate",
    "resource-specific-support-pending",
    "hard-block-opaque-pattern",
    "hard-block-unproven-semantics",
    "hard-block-role-firewall",
    "hard-block-inference-or-shape",
    "hard-block-unattributed",
]

RECOVERY_RULE_VERSION = "sg000030-r1-g1-v1"
COMPARISON_MODIFIER_TO_VALUE_PREFIX: Mapping[str, tuple[str, str]] = {
    "date:gt": ("date", "gt"),
    "date:gte": ("date", "ge"),
    "date:lt": ("date", "lt"),
    "date:lte": ("date", "le"),
}
FHIR_COMPARISON_PREFIXES = ("eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap")
G1_QUALIFIED_PARAMETERS = frozenset({"id", "_id", "patient", "_count"})
G1_PATIENT_REFERENCE_RESOURCE_TYPES = frozenset(
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
HARD_RUNTIME_REASONS = frozenset(
    {
        "search-target-outside-development-role",
        "llm-call-error",
        "no-response",
        "no-tool-call",
        "invalid-non-relative-query",
    }
)


class R1RecoveryCanonicalization(StrictModel):
    """Fail-closed prospective canonicalization result for the new recovery system."""

    schema_version: Literal["0.1"] = "0.1"
    recovery_rule_version: Literal["sg000030-r1-g1-v1"] = RECOVERY_RULE_VERSION
    role: D2FHIRRole
    resource_type: str
    original_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: R1Disposition
    recovery_transformed: bool
    executable_under_r1: bool
    canonical_query: str | None = None
    transformation_rule_ids: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> R1RecoveryCanonicalization:
        if self.executable_under_r1 and self.canonical_query is None:
            raise ValueError("executable recovery request requires canonical_query")
        if not self.executable_under_r1 and self.canonical_query is not None:
            raise ValueError("blocked recovery request must not emit canonical_query")
        if self.disposition == "hard-blocked" and not self.blocker_codes:
            raise ValueError("hard-blocked recovery request requires blocker_codes")
        if self.disposition != "hard-blocked" and self.blocker_codes:
            raise ValueError("non-blocked recovery request cannot retain blocker_codes")
        if self.recovery_transformed != bool(self.transformation_rule_ids):
            raise ValueError("recovery_transformed must match transformation_rule_ids")
        if self.disposition == "qualified-pass-through" and self.recovery_transformed:
            raise ValueError("qualified pass-through cannot be recovery-transformed")
        if self.disposition == "recovery-transformed" and not self.recovery_transformed:
            raise ValueError("recovery-transformed disposition requires a transformation")
        return self


def canonicalize_recovery_query(
    query_string: str,
    *,
    role: D2FHIRRole,
) -> R1RecoveryCanonicalization:
    """Apply only the prospectively frozen R1-G1 structural recovery rules.

    The function never consults answer labels, expected resource IDs, SQL gold queries,
    model outputs, or final-role data. Unknown or unqualified semantics fail closed.
    """

    request_sha256 = hashlib.sha256(query_string.encode("utf-8")).hexdigest()
    try:
        request = parse_relative_fhir_get(query_string, role=role)
    except ValueError:
        return R1RecoveryCanonicalization(
            role=role,
            resource_type="unknown",
            original_request_sha256=request_sha256,
            disposition="hard-blocked",
            recovery_transformed=False,
            executable_under_r1=False,
            blocker_codes=["invalid-relative-fhir-get"],
        )

    if request.resource_type not in FHIR_AGENTBENCH_SUPPORTED_RESOURCE_TYPES:
        return _blocked(
            role=role,
            resource_type=request.resource_type,
            request_sha256=request_sha256,
            blocker_codes=["unsupported-resource-type"],
        )

    transformed_parameters: list[tuple[str, str]] = []
    transformation_rule_ids: list[str] = []
    blocker_codes: set[str] = set()

    for parameter in request.parameters:
        name = parameter.name
        value = parameter.value

        if value == "":
            transformed_parameters.append(("", ""))
            transformation_rule_ids.append("empty-parameter-handling")
            continue

        comparison_mapping = COMPARISON_MODIFIER_TO_VALUE_PREFIX.get(name)
        if comparison_mapping is not None:
            canonical_name, prefix = comparison_mapping
            if _has_explicit_comparison_prefix(value):
                blocker_codes.add("ambiguous-comparison-prefix")
                continue
            transformed_parameters.append((canonical_name, prefix + value))
            transformation_rule_ids.append("comparison-modifier-to-value-prefix")
            continue

        transformed_parameters.append((name, value))

    if blocker_codes:
        return _blocked(
            role=role,
            resource_type=request.resource_type,
            request_sha256=request_sha256,
            blocker_codes=sorted(blocker_codes),
            transformation_rule_ids=transformation_rule_ids,
        )

    retained_parameters = [pair for pair in transformed_parameters if pair != ("", "")]
    retained_names = {name for name, _ in retained_parameters}
    unqualified_names = sorted(retained_names - G1_QUALIFIED_PARAMETERS)
    if unqualified_names:
        return _blocked(
            role=role,
            resource_type=request.resource_type,
            request_sha256=request_sha256,
            blocker_codes=[
                "resource-specific-semantics-not-yet-qualified:" + name
                for name in unqualified_names
            ],
            transformation_rule_ids=transformation_rule_ids,
        )

    if (
        "patient" in retained_names
        and request.resource_type not in G1_PATIENT_REFERENCE_RESOURCE_TYPES
    ):
        return _blocked(
            role=role,
            resource_type=request.resource_type,
            request_sha256=request_sha256,
            blocker_codes=["patient-search-not-qualified-for-resource-type"],
            transformation_rule_ids=transformation_rule_ids,
        )

    canonical_query = _serialize_relative_query(request.resource_type, retained_parameters)
    transformed = bool(transformation_rule_ids)
    return R1RecoveryCanonicalization(
        role=role,
        resource_type=request.resource_type,
        original_request_sha256=request_sha256,
        disposition="recovery-transformed" if transformed else "qualified-pass-through",
        recovery_transformed=transformed,
        executable_under_r1=True,
        canonical_query=canonical_query,
        transformation_rule_ids=transformation_rule_ids,
    )


def classify_persisted_source_pattern(entry: Mapping[str, Any]) -> R1PatternDisposition:
    """Classify one persisted safe SG-000028 pattern without raw trace access."""

    safe_pattern = entry.get("safe_pattern")
    if not isinstance(safe_pattern, str):
        return "hard-block-unattributed"
    if safe_pattern.startswith("opaque-pattern-sha256:"):
        return "hard-block-opaque-pattern"

    raw_reasons = entry.get("blocker_reason_associations", {})
    if not isinstance(raw_reasons, Mapping):
        return "hard-block-unattributed"
    reasons = {str(reason) for reason in raw_reasons}

    if "search-target-outside-development-role" in reasons:
        return "hard-block-role-firewall"
    if reasons & (HARD_RUNTIME_REASONS - {"search-target-outside-development-role"}):
        return "hard-block-inference-or-shape"
    if any(reason.startswith("opaque-reason-sha256:") for reason in reasons):
        return "hard-block-unproven-semantics"
    if any(
        reason == "unsupported-parameter:" + modifier
        for modifier in COMPARISON_MODIFIER_TO_VALUE_PREFIX
        for reason in reasons
    ):
        return "comparison-transform-candidate"
    if any(reason.startswith("unsupported-parameter:") for reason in reasons):
        return "resource-specific-support-pending"

    if entry.get("support_status") == "observed-only-in-passing-rows":
        return "observed-pass-through"
    return "hard-block-unattributed"


def _blocked(
    *,
    role: D2FHIRRole,
    resource_type: str,
    request_sha256: str,
    blocker_codes: list[str],
    transformation_rule_ids: list[str] | None = None,
) -> R1RecoveryCanonicalization:
    rules = transformation_rule_ids or []
    return R1RecoveryCanonicalization(
        role=role,
        resource_type=resource_type,
        original_request_sha256=request_sha256,
        disposition="hard-blocked",
        recovery_transformed=bool(rules),
        executable_under_r1=False,
        transformation_rule_ids=rules,
        blocker_codes=blocker_codes,
    )


def _has_explicit_comparison_prefix(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in FHIR_COMPARISON_PREFIXES)


def _serialize_relative_query(resource_type: str, parameters: list[tuple[str, str]]) -> str:
    if not parameters:
        return resource_type
    encoded = "&".join(
        f"{quote_plus(name, safe='._-:')}={quote_plus(value, safe='._-:/,|')}"
        for name, value in parameters
    )
    return f"{resource_type}?{encoded}"
