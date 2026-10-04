import json
from collections import Counter
from pathlib import Path

from gaxbench.study1_recovery_compat import (
    COMPARISON_MODIFIER_TO_VALUE_PREFIX,
    RECOVERY_RULE_VERSION,
    canonicalize_recovery_query,
    classify_persisted_source_pattern,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/study1_sg000030_r1_g1_manifest.json"
CONTRACT = ROOT / "registry/study1_sg000030_contract.json"
FRONTIER = ROOT / "registry/study1_sg000030_frontier_status.json"
PARENT_FRONTIER = ROOT / "registry/study1_sg000029_frontier_status.json"
SOURCE_EVIDENCE = ROOT / "registry/study1_sg000028_execution_37156028113.json"
BLOCKER_INVESTIGATION = ROOT / "registry/study1_sg000028_blocker_investigation.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_r1_g1_preserves_immutable_negative_parent_and_final_firewall() -> None:
    manifest = _load(MANIFEST)
    contract = _load(CONTRACT)
    frontier = _load(FRONTIER)

    result = manifest["immutable_original_result"]
    assert result["scientific_state"] == "BLOCKED"
    assert result["exposed_development_rows"] == 1463
    assert result["pass_rows"] == 224
    assert result["behavior_changing_blocker_rows"] == 1239
    assert result["may_be_relabelled_pass"] is False

    assert contract["immutable_parent"]["scientific_state"] == "BLOCKED"
    assert frontier["immutable_parent_sg000028"]["scientific_state"] == "BLOCKED"
    assert manifest["sealed_final_role"] == {
        "patients": 40,
        "rows": 173,
        "access_allowed": False,
    }
    assert contract["sealed_final_role"]["access_allowed"] is False
    assert frontier["final_role_access_allowed"] is False


def test_r1_authorization_does_not_authorize_r2_or_training() -> None:
    manifest = _load(MANIFEST)
    contract = _load(CONTRACT)
    frontier = _load(FRONTIER)
    parent_frontier = _load(PARENT_FRONTIER)

    assert parent_frontier["r1_implementation_authorized"] is True
    assert parent_frontier["r1_founder_authorization_issue"] == 153
    assert parent_frontier["r1_founder_authorization_comment"] == 5982001184
    assert parent_frontier["r2_execution_authorized"] is False

    boundary = manifest["authorization_boundary"]
    assert all(value is False for value in boundary.values())
    execution = contract["execution_boundary"]
    assert all(value is False for value in execution.values())
    assert frontier["new_inference_performed"] is False
    assert frontier["r2_execution_authorized"] is False
    assert frontier["training_authorized"] is False
    assert frontier["d4_activation_allowed"] is False


def test_source_pattern_inventory_is_exhaustively_classified_without_trace_regeneration() -> None:
    manifest = _load(MANIFEST)
    evidence = _load(SOURCE_EVIDENCE)
    entries = evidence["pattern_support_evidence"]

    inventory = manifest["source_pattern_inventory_policy"]
    assert len(entries) == inventory["expected_exact_pattern_count"]
    assert len(entries) == 248
    assert len({entry["source_pattern_sha256"] for entry in entries}) == 248
    assert evidence["artifact_firewall"]["raw_traces_emitted_by_persistence"] is False
    assert inventory["raw_trace_regeneration_allowed"] is False

    classifications = [classify_persisted_source_pattern(entry) for entry in entries]
    permitted = set(inventory["finite_dispositions"])
    assert set(classifications) <= permitted
    assert len(classifications) == 248

    counts = Counter(classifications)
    assert counts["hard-block-opaque-pattern"] == 39
    assert counts["comparison-transform-candidate"] > 0
    assert counts["resource-specific-support-pending"] > 0
    assert counts["observed-pass-through"] > 0


def test_empty_parameter_rule_drops_only_empty_pair_and_preserves_non_empty_sibling() -> None:
    result = canonicalize_recovery_query(
        "Observation?opaqueLegacyName=&patient=dev-1",
        role="calibration",
    )

    assert result.recovery_rule_version == RECOVERY_RULE_VERSION
    assert result.disposition == "recovery-transformed"
    assert result.recovery_transformed is True
    assert result.executable_under_r1 is True
    assert result.canonical_query == "Observation?patient=dev-1"
    assert result.transformation_rule_ids == ["empty-parameter-handling"]
    assert result.blocker_codes == []
    assert len(result.original_request_sha256) == 64


def test_empty_only_parameter_can_be_ignored_without_inventing_replacement_semantics() -> None:
    result = canonicalize_recovery_query(
        "Observation?opaqueLegacyName=",
        role="validation",
    )

    assert result.disposition == "recovery-transformed"
    assert result.executable_under_r1 is True
    assert result.canonical_query == "Observation"
    assert result.transformation_rule_ids == ["empty-parameter-handling"]


def test_comparison_modifier_mapping_is_exact_and_still_fail_closed_until_date_support() -> None:
    expected = {
        "date:gt": ("date", "gt"),
        "date:gte": ("date", "ge"),
        "date:lt": ("date", "lt"),
        "date:lte": ("date", "le"),
    }
    assert dict(COMPARISON_MODIFIER_TO_VALUE_PREFIX) == expected

    for modifier, (_, prefix) in expected.items():
        result = canonicalize_recovery_query(
            f"Observation?{modifier}=2020-01-01&patient=dev-1",
            role="calibration",
        )
        assert result.disposition == "hard-blocked"
        assert result.recovery_transformed is True
        assert result.executable_under_r1 is False
        assert result.canonical_query is None
        assert result.transformation_rule_ids == ["comparison-modifier-to-value-prefix"]
        assert result.blocker_codes == ["resource-specific-semantics-not-yet-qualified:date"]
        assert prefix in {"gt", "ge", "lt", "le"}


def test_comparison_mapping_rejects_ambiguous_pre_prefixed_value() -> None:
    result = canonicalize_recovery_query(
        "Observation?date:gte=gt2020-01-01&patient=dev-1",
        role="calibration",
    )

    assert result.disposition == "hard-blocked"
    assert result.executable_under_r1 is False
    assert result.canonical_query is None
    assert result.blocker_codes == ["ambiguous-comparison-prefix"]


def test_g1_fails_closed_for_unqualified_resource_specific_semantics() -> None:
    result = canonicalize_recovery_query(
        "Observation?status=final&patient=dev-1",
        role="validation",
    )

    assert result.disposition == "hard-blocked"
    assert result.recovery_transformed is False
    assert result.executable_under_r1 is False
    assert result.canonical_query is None
    assert result.blocker_codes == ["resource-specific-semantics-not-yet-qualified:status"]


def test_g1_rejects_non_relative_requests_without_exposing_original_request() -> None:
    result = canonicalize_recovery_query(
        "https://example.invalid/Observation?patient=dev-1",
        role="calibration",
    )

    assert result.disposition == "hard-blocked"
    assert result.executable_under_r1 is False
    assert result.canonical_query is None
    assert result.blocker_codes == ["invalid-relative-fhir-get"]
    dumped = result.model_dump()
    assert "raw_query" not in dumped
    assert "original_query" not in dumped


def test_r1_g1_manifest_matches_persisted_blocker_investigation_limits() -> None:
    manifest = _load(MANIFEST)
    investigation = _load(BLOCKER_INVESTIGATION)

    assert investigation["development_rows_investigated"] == 1463
    assert investigation["blocked_rows_retained"] == 1239
    assert investigation["malformed_name_rows_with_empty_parameter"] == 24
    class_counts = investigation["blocker_class_row_counts"]
    assert class_counts["comparison-prefix-used-as-search-modifier"] == 41
    assert investigation["raw_traces_accessed"] is False
    assert investigation["final_role_content_accessed"] is False
    assert manifest["resource_specific_support"]["new_support_claimed_by_g1"] is False
    assert manifest["hard_blocker_policy"]["unknown_semantics_guessing"] == "forbidden"
