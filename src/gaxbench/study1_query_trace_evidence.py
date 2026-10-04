"""Finite, privacy-safe output vocabulary for development trace evidence.

This changes exported identities only. It never changes or repairs an observed
request, its execution, role authorization, or scientific support classification.
"""

from __future__ import annotations

import hashlib
import re

PARAMETERS = frozenset(
    "id _id patient _count _date _include _limit _since _sort _until category code "
    "code.code code.coding.code code.coding.system code.system coding.code coding.system "
    "criteria date date-gt date.ge date.lt date:gt date:gte date:lt date:lte dateToday "
    "display effectiveDateTime effectiveDateTime.ge effectiveDateTime.lt "
    "effectivePeriod.end effectivePeriod.start encounter encounter:reference entryMode "
    "identifier.system identifier.value limit medicationAdministration.route "
    "medicationCodeableConcept medicationCodeableConcept.coding.code "
    "medicationCodeableConcept.coding.display medicationCodeableConcept.coding.system "
    "medicationReference medicationReference.display medicationRequest.route method "
    "reference request.method route route.code route.coding.code route.coding.display "
    "route.coding.system route.display route.system route:contains sort specimen status "
    "system type value valueBelow valueLessThan valueLow valueQuantity valueQuantity.lt".split()
)
VALUE_CLASSES = frozenset(
    "positive-int invalid-count id-list id patient-reference patient-id comparator "
    "token reference list empty value".split()
)
FIXED_REASONS = frozenset(
    "llm-call-error no-response no-tool-call unexpected-tool-name malformed-tool-arguments "
    "missing-query-string query-exercise-exception invalid-empty-or-surrounding-whitespace "
    "invalid-multiline-query invalid-non-relative-query invalid-query-path "
    "unsupported-read-query-parameters unsupported-resource-type "
    "unsupported-nested-or-operation-path unsupported-operation-or-history "
    "read-target-outside-development-role direct-read-not-development-scoped-or-missing "
    "search-target-outside-development-role resource-id-not-development-scoped-or-missing "
    "unscoped-search-role-firewall local-parser-rejected-observed-query".split()
)
RESOURCE_TYPES = frozenset(
    "Patient Encounter Condition MedicationRequest Procedure Observation "
    "MedicationAdministration Specimen Location Medication".split()
)


def _opaque(value: str, kind: str) -> str:
    return f"opaque-{kind}-sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_safe_reason(reason: str) -> bool:
    return (
        reason in FIXED_REASONS
        or (
            reason.startswith("unsupported-parameter:")
            and reason.removeprefix("unsupported-parameter:") in PARAMETERS
        )
        or re.fullmatch(r"opaque-reason-sha256:[0-9a-f]{64}", reason) is not None
    )


def safe_reason(reason: str) -> str:
    return reason if is_safe_reason(reason) else _opaque(reason, "reason")


def is_safe_pattern(pattern: str) -> bool:
    if re.fullmatch(r"opaque-pattern-sha256:[0-9a-f]{64}", pattern):
        return True
    if pattern.startswith("invalid:"):
        return pattern.removeprefix("invalid:") in FIXED_REASONS
    if pattern.startswith("read:"):
        return pattern[5:].removesuffix("/{id}") in RESOURCE_TYPES and pattern.endswith("/{id}")
    if pattern.startswith("search:"):
        resource, marker, query = pattern[7:].partition("?")
        if resource not in RESOURCE_TYPES or (marker and not query):
            return False
        for token in query.split("&") if query else []:
            match = re.fullmatch(r"([^=]+)=<([^<>]+)>", token)
            if not match or match[1] not in PARAMETERS or match[2] not in VALUE_CLASSES:
                return False
        return True
    return False


def safe_pattern(pattern: str) -> str:
    return pattern if is_safe_pattern(pattern) else _opaque(pattern, "pattern")
