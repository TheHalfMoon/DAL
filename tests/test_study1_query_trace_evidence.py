from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from gaxbench.study1_query_trace_evidence import (
    is_safe_pattern,
    is_safe_reason,
    safe_pattern,
    safe_reason,
)
from gaxbench.study1_query_trace_gate import normalize_relative_fhir_get

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name",
    [
        "private-patient-id",
        "date>2099-01-01",
        "clinical free text",
        "gt;42.5",
        "x%26patient",
        "code\nprivate",
        "opaque-pattern-sha256:private",
    ],
)
def test_malformed_names_remain_distinct_opaque_blocker_evidence(name: str) -> None:
    pattern = f"search:Observation?{name}=<empty>&patient=<patient-id>"
    reason = f"unsupported-parameter:{name}"
    output_pattern = safe_pattern(pattern)
    output_reason = safe_reason(reason)
    assert output_pattern.startswith("opaque-pattern-sha256:")
    assert output_reason.startswith("opaque-reason-sha256:")
    assert name not in output_pattern
    assert name not in output_reason
    assert is_safe_pattern(output_pattern) and is_safe_reason(output_reason)
    assert safe_pattern(output_pattern) == output_pattern
    assert safe_reason(output_reason) == output_reason
    assert safe_pattern(pattern + " ") != output_pattern


def test_valid_structure_and_request_semantics_are_unchanged() -> None:
    normalized = normalize_relative_fhir_get("Encounter?date=2099-01-01&patient=private")
    assert safe_pattern(normalized.pattern) == "search:Encounter?date=<value>&patient=<patient-id>"
    assert safe_reason("unsupported-parameter:date") == "unsupported-parameter:date"
    assert safe_reason("search-target-outside-development-role") == (
        "search-target-outside-development-role"
    )
    assert safe_pattern("read:Patient/{id}") == "read:Patient/{id}"
    assert not is_safe_pattern("search:Observation?code=<private>")
    assert not is_safe_reason("unsupported-parameter:private")


def test_aggregate_rejects_literal_keys_at_the_output_boundary() -> None:
    spec = importlib.util.spec_from_file_location(
        "sg28_safe_aggregate", ROOT / "scripts/study1_sg000028_query_trace_aggregate.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert not module._is_normalized_pattern("search:Patient?private-id=<empty>")
    assert module._is_normalized_pattern(safe_pattern("search:Patient?private-id=<empty>"))


def test_output_only_repair_cannot_automatically_rerun_completed_inference() -> None:
    text = (ROOT / ".github/workflows/study1-sg000028-query-trace-gate.yml").read_text()
    assert "needs: execution-scope" in text
    assert "if: needs.execution-scope.outputs.execute == 'true'" in text
    assert 'frontier.get("query_trace_evidence_generated") is False' in text
    assert 'frontier.get("compatibility_requalification_authorized") is True' in text
