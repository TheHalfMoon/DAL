from __future__ import annotations

from pathlib import Path

import pytest

from gaxbench.native_abstention_qualification import (
    PARENT_LEAKAGE_AUDIT_SHA256,
    PARENT_SPLIT_MANIFEST_SHA256,
    qualify_native_abstention,
)

ROOT = Path(__file__).parents[1]


def test_native_abstention_qualification_is_bound_to_parent_pubmedqa() -> None:
    role, audit, qualification = qualify_native_abstention(
        ROOT / "registry" / "pubmedqa_pqal_split_manifest.json",
        ROOT / "registry" / "pubmedqa_pqal_leakage_audit.json",
    )
    assert role.parent_split_manifest_sha256 == PARENT_SPLIT_MANIFEST_SHA256
    assert audit.parent_leakage_audit_sha256 == PARENT_LEAKAGE_AUDIT_SHA256
    assert role.roles["validation"].source_count == 450
    assert role.roles["validation"].pair_count == 900
    assert role.roles["calibration"].source_count == 50
    assert role.roles["calibration"].pair_count == 100
    assert role.roles["test"].source_count == 500
    assert role.roles["test"].pair_count == 1000
    assert qualification.source_item_count == 1000
    assert qualification.derived_item_count == 2000
    assert qualification.final_test_access == "sealed"
    assert qualification.test_supervision_serialized is False


def test_native_audit_preserves_intentional_pair_overlap_as_non_leakage() -> None:
    _, audit, _ = qualify_native_abstention(
        ROOT / "registry" / "pubmedqa_pqal_split_manifest.json",
        ROOT / "registry" / "pubmedqa_pqal_leakage_audit.json",
    )
    assert audit.intentional_within_source_pair_count == 1000
    assert audit.cross_role_pair_overlap_count == 0
    assert audit.abstain_candidate_action_count == 0


def test_changed_parent_manifest_fails_closed(tmp_path: Path) -> None:
    original = (ROOT / "registry" / "pubmedqa_pqal_split_manifest.json").read_text(
        encoding="utf-8"
    )
    tampered = tmp_path / "manifest.json"
    tampered.write_text(
        original.replace('"upstream_seed": 0', '"upstream_seed": 1'),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        qualify_native_abstention(
            tampered,
            ROOT / "registry" / "pubmedqa_pqal_leakage_audit.json",
        )
