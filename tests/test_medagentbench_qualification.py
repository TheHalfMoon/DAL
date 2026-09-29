from __future__ import annotations

import pytest

from gaxbench.medagentbench_audit import leakage_audit_payload
from gaxbench.medagentbench_qualification import (
    MEDAGENTBENCH_ROLE_REVISION,
    MedAgentBenchCorpusProbe,
    MedAgentBenchRoleManifest,
    MedAgentBenchRuntimeStatus,
    _jaccard,
    _near_duplicate_summary,
    _shingles,
    _visible_tasks,
    git_blob_sha1,
)
from gaxbench.provenance import canonical_json_sha256


def test_git_blob_sha1_matches_git_blob_format() -> None:
    assert git_blob_sha1(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_visible_task_projection_excludes_gold_fields() -> None:
    visible = _visible_tasks(
        [
            {
                "id": "task1_1",
                "instruction": "Find the matching record",
                "context": "abstract context",
                "sol": ["secret"],
                "eval_MRN": "secret-id",
            }
        ]
    )
    assert len(visible) == 1
    assert visible[0].task_id == "task1_1"
    assert visible[0].family == "task1"
    assert "secret" not in visible[0].normalized_text


def test_visible_task_projection_requires_string_context() -> None:
    with pytest.raises(ValueError, match="string context"):
        _visible_tasks([{"id": "task1_1", "instruction": "x", "context": None}])


def test_near_duplicate_summary_counts_cross_family_pairs() -> None:
    tasks = _visible_tasks(
        [
            {
                "id": "task1_1",
                "instruction": "alpha beta gamma delta epsilon zeta",
                "context": "",
            },
            {
                "id": "task2_1",
                "instruction": "alpha beta gamma delta epsilon zeta",
                "context": "",
            },
            {
                "id": "task3_1",
                "instruction": "one two three four five six",
                "context": "",
            },
        ]
    )
    near_pairs, cross_family_pairs, digest = _near_duplicate_summary(tasks)
    assert near_pairs == 1
    assert cross_family_pairs == 1
    assert len(digest) == 64


def test_shingle_jaccard_is_bounded() -> None:
    left = _shingles("a b c d e f", 5)
    right = _shingles("a b c d e g", 5)
    assert 0.0 <= _jaccard(left, right) <= 1.0


def test_role_manifest_is_final_test_only() -> None:
    manifest = MedAgentBenchRoleManifest(item_count=300, membership_sha256="0" * 64)
    assert manifest.role_revision == MEDAGENTBENCH_ROLE_REVISION
    assert manifest.role == "final-test"
    assert manifest.training_use_forbidden is True
    assert manifest.calibration_use_forbidden is True
    assert manifest.model_selection_use_forbidden is True
    assert manifest.final_test_access == "sealed"


def test_official_runtime_is_fail_closed() -> None:
    status = MedAgentBenchRuntimeStatus(
        blocked_reason="external artifacts are not qualified"
    )
    assert status.official_runtime_status == "blocked"
    assert status.docker_reference_is_mutable_tag is True
    assert status.refsol_immutable_revision_verified is False
    assert status.refsol_license_verified is False
    assert status.official_success_rate_claim_allowed is False


def test_persisted_audit_payload_matches_qualification_digest_contract() -> None:
    probe = MedAgentBenchCorpusProbe(
        task_sha256="0" * 64,
        task_count=2,
        unique_task_id_count=2,
        duplicate_task_id_count=0,
        task_field_names=["context", "id", "instruction"],
        task_family_counts={"task1": 2},
        exact_duplicate_visible_task_count=0,
        near_duplicate_visible_pair_count=1,
        cross_family_near_duplicate_pair_count=0,
        near_duplicate_pair_digest="1" * 64,
        function_sha256="2" * 64,
        function_count=1,
        unique_function_name_count=1,
        duplicate_function_name_count=0,
        function_field_names=["description", "name", "parameters"],
    )
    payload = leakage_audit_payload(probe)
    assert payload["role_revision"] == MEDAGENTBENCH_ROLE_REVISION
    assert payload["near_duplicate_visible_pair_count"] == 1
    assert len(canonical_json_sha256(payload)) == 64
