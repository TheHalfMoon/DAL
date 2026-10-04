"""R1-G2 synthetic-qualified runtime; no model transport or benchmark loader."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gaxbench.study1_fhir_compat import D2FHIRRole, parse_relative_fhir_get
from gaxbench.study1_query_trace_evidence import is_safe_pattern
from gaxbench.study1_query_trace_gate import (
    GateRuntime,
    _search_scope_blocker,
    build_gate_runtime_from_resources,
    normalize_relative_fhir_get,
)
from gaxbench.study1_recovery_compat import (
    R1RecoveryCanonicalization,
    _serialize_relative_query,
    canonicalize_recovery_query,
)

R1_RUNTIME_VERSION = "sg000030-r1-g2-v1"
SOURCE_EVIDENCE_SHA256 = "631c04d8717eb896c0496197c9a82dac60bf2eb9575f945b8716b796c2dca785"
STATUS_VALUES = {
    "Observation": frozenset(
        {
            "registered",
            "preliminary",
            "final",
            "amended",
            "corrected",
            "cancelled",
            "entered-in-error",
            "unknown",
        }
    ),
    "MedicationRequest": frozenset(
        {
            "active",
            "on-hold",
            "cancelled",
            "completed",
            "entered-in-error",
            "stopped",
            "draft",
            "unknown",
        }
    ),
}


@dataclass(frozen=True)
class R1RecoveryExercise:
    """Hash-only durable audit. Query literals and returned resources stay transient."""

    original_request_sha256: str
    source_pattern_sha256: str
    disposition: str
    recovery_transformed: bool
    transformation_rule_ids: tuple[str, ...]
    blocker_codes: tuple[str, ...]
    returned_resource_count: int
    synthetic_qualification: bool
    runtime_version: str = R1_RUNTIME_VERSION


def canonicalize_qualified_recovery_query(
    query_string: str, *, role: D2FHIRRole
) -> R1RecoveryCanonicalization:
    """Extend G1 only for a single unmodified scalar status token on two resources."""
    try:
        request = parse_relative_fhir_get(query_string, role=role)
    except ValueError:
        return canonicalize_recovery_query(query_string, role=role)
    status = [p.value for p in request.parameters if p.name == "status" and p.value]
    if not status:
        return canonicalize_recovery_query(query_string, role=role)
    if len(status) != 1 or status[0] not in STATUS_VALUES.get(request.resource_type, frozenset()):
        return _reject(query_string, role, "unqualified-status-token-shape-or-resource")

    # Strip only the already-qualified non-empty status pair while consulting frozen G1.
    remaining = [(p.name, p.value) for p in request.parameters if p.name != "status" or not p.value]
    base = canonicalize_recovery_query(
        _serialize_relative_query(request.resource_type, remaining), role=role
    )
    if base.executable_under_r1:
        # G1 executable transformations are empty-pair removals only: date stays blocked.
        retained = [(p.name, p.value) for p in request.parameters if p.value]
        canonical = _serialize_relative_query(request.resource_type, retained)
        base = base.model_copy(update={"canonical_query": canonical})
    return base.model_copy(update={"original_request_sha256": _digest(query_string)})


@dataclass(frozen=True)
class R1RecoveryRuntime:
    role: D2FHIRRole
    gate: GateRuntime = field(repr=False)
    source_entries: Mapping[str, Mapping[str, Any]] = field(repr=False)
    synthetic_qualification: bool = False

    @classmethod
    def from_resources(
        cls,
        resources: Iterable[Mapping[str, Any]],
        *,
        role: D2FHIRRole,
        development_patient_digests: frozenset[str],
        source_evidence_path: Path | None = None,
        synthetic_qualification: bool = False,
    ) -> R1RecoveryRuntime:
        if role not in {"calibration", "validation"}:
            raise ValueError("R1 runtime accepts development roles only")
        source_entries: dict[str, Mapping[str, Any]] = {}
        if not synthetic_qualification:
            path = source_evidence_path or (
                Path(__file__).resolve().parents[2]
                / "registry/study1_sg000028_execution_37156028113.json"
            )
            content = path.read_bytes().replace(b"\r\n", b"\n")
            if hashlib.sha256(content).hexdigest() != SOURCE_EVIDENCE_SHA256:
                raise ValueError("canonical SG-000028 source evidence digest mismatch")
            entries = json.loads(content)["pattern_support_evidence"]
            source_entries = {entry["source_pattern_sha256"]: entry for entry in entries}
            if len(source_entries) != 248:
                raise ValueError("canonical source inventory must contain exactly 248 identities")
        return cls(
            role,
            build_gate_runtime_from_resources(
                resources, development_patient_digests=development_patient_digests
            ),
            source_entries,
            synthetic_qualification,
        )

    def exercise(self, query_string: str, *, source_entry: Mapping[str, Any]) -> R1RecoveryExercise:
        """Require exact persisted structural linkage before exercising any request."""
        normalized = normalize_relative_fhir_get(query_string)
        pattern_sha = _digest(normalized.pattern)
        result = canonicalize_qualified_recovery_query(query_string, role=self.role)
        if (
            not is_safe_pattern(normalized.pattern)
            or normalized.pattern.startswith("opaque-pattern-sha256:")
            or source_entry.get("safe_pattern") != normalized.pattern
            or source_entry.get("source_pattern_sha256") != pattern_sha
            or (
                not self.synthetic_qualification
                and self.source_entries.get(pattern_sha) != source_entry
            )
        ):
            result = _reject(query_string, self.role, "source-pattern-linkage-not-qualified")
        elif normalized.mode != "search":
            result = _reject(query_string, self.role, "unqualified-request-shape")
        if result.executable_under_r1:
            scope = _search_scope_blocker(
                query_string, resource_type=normalized.resource_type or "", runtime=self.gate
            )
            if scope:
                result = _reject(query_string, self.role, scope)
        count = 0
        if result.executable_under_r1:
            assert result.canonical_query is not None
            count = len(self._search(result.canonical_query))
        return R1RecoveryExercise(
            original_request_sha256=_digest(query_string),
            source_pattern_sha256=pattern_sha,
            disposition=result.disposition,
            recovery_transformed=result.recovery_transformed,
            transformation_rule_ids=tuple(result.transformation_rule_ids),
            blocker_codes=tuple(result.blocker_codes),
            returned_resource_count=count,
            synthetic_qualification=self.synthetic_qualification,
        )

    def _search(self, canonical_query: str) -> list[str]:
        request = parse_relative_fhir_get(canonical_query, role=self.role)
        status = [p.value for p in request.parameters if p.name == "status"]
        counts = [int(p.value) for p in request.parameters if p.name == "_count"]
        base_request = request.model_copy(
            update={
                "parameters": [p for p in request.parameters if p.name not in {"status", "_count"}]
            }
        )
        base = self.gate.store.search(base_request)
        if base.status != "completed":
            raise ValueError("qualified recovery request drifted outside frozen D2 runtime")
        candidates = base.resources_by_type.get(request.resource_type, [])
        if status:
            candidates = [r for r in candidates if r.get("status") == status[0]]
        identities = sorted(f"{r['resourceType']}/{r['id']}" for r in candidates)
        return identities[: counts[0]] if counts else identities


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reject(query: str, role: D2FHIRRole, code: str) -> R1RecoveryCanonicalization:
    original = canonicalize_recovery_query(query, role=role)
    return original.model_copy(
        update={
            "disposition": "hard-blocked",
            "executable_under_r1": False,
            "canonical_query": None,
            "blocker_codes": [code],
        }
    )
