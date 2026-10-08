"""Synthetic and negative Gate B1 tests, never any scientific data/model I/O."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from gaxbench.study1_attempt3_b1 import (
    ClaimState,
    FrozenAttempt3Controller,
    FrozenAttempt3Worker,
    FrozenScientificTransport,
    SyntheticSingleUseClaim,
    check_policy,
    load_contract,
    partition_denominator,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def contract():
    return load_contract(ROOT)


@pytest.fixture
def q():
    path = ROOT / "tools/qualify_sg000031_attempt3_b1.py"
    spec = importlib.util.spec_from_file_location("dal_b1_qualifier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_contract_unarmed_43_files_and_frozen_producer(contract):
    report = check_policy(ROOT, contract)
    assert report["unarmed"] is True
    assert report["protected_files_verified"] == 43
    assert contract["execution_authorization"]["sha256"] is None


def test_qualified_b1_rehearsal_is_only_structural(contract):
    report = FrozenAttempt3Controller(ROOT, contract).rehearse()
    assert report["admission"] == "SCIENTIFIC_CAPABILITY_ENGINEERING_UNARMED"
    assert report["shard_count"] == 8
    assert sum(report["shard_row_counts"]) == 1463
    assert report["first_turn_generation_limit"] == 1463
    assert report["scientific_dispatches"] == 0
    assert report["model_http_posts"] == 0
    assert report["rows_materialized"] == 0
    assert report["permanent_scientific_claim_created"] is False
    assert report["execution_authorization_sha256"] is None
    assert report["r2_state"] == "BLOCKED"


def test_in_memory_claim_is_one_shot_even_on_pre_model_failure():
    claim = SyntheticSingleUseClaim()
    assert claim.consume_once(inject_pre_model_failure=True) == "CONSUMED_PRE_MODEL_FAILURE"
    assert claim.failed_before_model is True
    assert claim.state is ClaimState.CONSUMED
    with pytest.raises(PermissionError, match="already consumed"):
        claim.consume_once()


def test_synthetic_claim_does_not_replay_even_if_no_failure():
    claim = SyntheticSingleUseClaim()
    assert claim.consume_once() == "CONSUMED_SYNTHETIC_ONLY"
    with pytest.raises(PermissionError, match="already consumed"):
        claim.consume_once(inject_pre_model_failure=True)


def test_no_actual_scientific_dispatch_or_transport(contract):
    controller = FrozenAttempt3Controller(ROOT, contract)
    with pytest.raises(PermissionError, match="Gate B2"):
        controller.dispatch("payload")
    with pytest.raises(PermissionError, match="Gate B2"):
        controller.create_permanent_claim("tag")
    worker = FrozenAttempt3Worker()
    with pytest.raises(PermissionError, match="Gate B2"):
        worker.run("payload")
    with pytest.raises(PermissionError, match="Gate B2"):
        worker.load_development_rows("source.csv")
    with pytest.raises(PermissionError, match="sealed final"):
        worker.load_sealed_final("anything")
    with pytest.raises(PermissionError, match="Gate B2"):
        FrozenScientificTransport().post("http://127.0.0.1", "model_body")


def test_exact_shard_math_never_materializes_rows(contract):
    plan = FrozenAttempt3Worker().plan(contract)
    assert len(plan) == 8
    assert [p.number_of_rows for p in plan] == [183] * 7 + [182]
    assert all(p.science_enabled is False for p in plan)
    assert sum(p.max_first_turn_generations for p in plan) == 1463


@pytest.mark.parametrize(
    "total,shards",
    [
        (1462, 8),
        (1464, 8),
        (1463, 7),
        (1463, 9),
        (True, 8),
        (1463, True),
    ],
)
def test_shard_plan_rejects_altered_science_scope(total, shards):
    with pytest.raises(ValueError, match="scientific population"):
        partition_denominator(total, shards)


@pytest.mark.parametrize(
    "key,value",
    [
        ("status", "AUTHORIZED"),
        ("sha256", "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"),
        ("approved_scientific_execution_issue", 171),
        ("single_run_token", "old"),
        ("science_dispatch_permitted", True),
        ("model_http_post_permitted", True),
        ("development_row_replay_permitted", True),
        ("permanent_claim_permitted", True),
    ],
)
def test_b1_cannot_create_or_reuse_execution_authorization(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["execution_authorization"][key] = value
    with pytest.raises(ValueError, match="Gate B2"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r2", "PASS"),
        ("scientific_execution_authorized", True),
        ("model_posts", 1),
        ("rows_replayed", 1),
        ("permanent_claim_created", True),
        ("final_role", "UNSEALED"),
        ("final_rows_materialized", 173),
        ("final_content_access", True),
        ("d4", True),
        ("training", True),
        ("founder_cost_usd", 1),
    ],
)
def test_scientific_firewall_fail_closed(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["science_firewall"][key] = value
    with pytest.raises(ValueError, match="firewall"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("shards", 9),
        ("first_turn_generations_per_row", 2),
        ("maximum_first_turn_generations", 1462),
        ("automatic_retries", 1),
        ("second_turn_reasoning", True),
        ("answer_correctness_scoring", True),
        ("selective_row_omission", True),
        ("final_role_access", True),
        ("model_switching", True),
        ("claim_consumption", "AFTER_MODEL"),
    ],
)
def test_single_use_scientific_budget_and_claim_rules(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["execution_shape"][key] = value
    with pytest.raises(ValueError, match="one-shot"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("model_revision", "different"),
        ("tokenizer_revision", "different"),
        ("gguf_sha256", "0" * 64),
        ("llama_cpp_revision", "different"),
        ("fhir_agentbench_revision", "different"),
        ("transport_patch_sha256", "0" * 64),
        ("strategy", "two_turn_request"),
        ("temperature", 0.5),
        ("agent_context_tokens", 8192),
        ("producer_identity_sha256", "0" * 64),
    ],
)
def test_producer_frozen_from_actual_attempt2_contract(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["frozen_science"]["producer"][key] = value
    with pytest.raises(ValueError, match="frozen model"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("development_rows", 1462),
        ("calibration_rows", 342),
        ("validation_rows", 1121),
        ("r1_manifest_sha256", "0" * 64),
        ("population_sha256", "0" * 64),
        ("sealed_final_rows", 174),
    ],
)
def test_frozen_r1_development_and_final_population(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["frozen_science"][key] = value
    with pytest.raises(ValueError, match="freeze|frozen|final counts|denominator"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("workflow_dispatch_created", True),
        ("scientific_worker_workflow_created", True),
        ("credentialed_transport_created", True),
        ("raw_row_loader_created", True),
        ("production_claim_writer_created", True),
        ("production_http_client_created", True),
        ("admission_mode", "SCIENTIFIC_DISPATCH"),
    ],
)
def test_no_operational_science_capability_under_b1(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["engineering_gate"][key] = value
    with pytest.raises(ValueError, match="unexpectedly armed"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("permanent_tag", "refs/tags/dal-r2-issue158-attempt2"),
        ("ledger_branch", "codex/sg000031-r2-attempt2-journal"),
        ("scientific_workflow", ".github/workflows/study1-sg000031-r2-attempt2.yml"),
        ("scientific_worker", ".github/workflows/study1-sg000031-r2-attempt2-worker.yml"),
    ],
)
def test_no_consumed_scientific_namespace_reuse(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["claim_namespace"][key] = value
    with pytest.raises(ValueError, match="namespace"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "key,value",
    [
        ("issue", 168),
        ("assistant_transcribed_comment_id", 6050120310),
        ("original_founder_github_comment", True),
        ("scope", "SCIENTIFIC_EXECUTION"),
    ],
)
def test_no_fabrication_of_founder_approval_origin(contract, key, value):
    bad = copy.deepcopy(contract)
    bad["engineering_authorization"][key] = value
    with pytest.raises(ValueError, match="provenance"):
        check_policy(ROOT, bad)


@pytest.mark.parametrize(
    "event",
    [
        "workflow_dispatch",
        "repository_dispatch",
        "schedule",
        "workflow_call",
    ],
)
def test_no_manual_or_scientific_ci_event(q, monkeypatch, event):
    monkeypatch.setenv("GITHUB_REPOSITORY", q.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    with pytest.raises(ValueError, match="rejects"):
        q.check_environment()


def test_no_ci_rerun(q, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", q.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    with pytest.raises(ValueError, match="rerun"):
        q.check_environment()


def test_wrong_github_repo_denied(q, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "other/repo")
    with pytest.raises(ValueError, match="wrong canonical"):
        q.check_environment()


def test_native_founder_comment_identity_and_provenance(q):
    routes = {
        "issues/171": {"number": 171, "state": "open"},
        "issues/comments/6066751157": {
            "issue_url": q.native.REPOSITORY_API + "/issues/171",
            "body": (
                "FOUNDER DECISION — GATE B1 APPROVED. "
                "assistant-posted transcription. "
                "does NOT permit scientific dispatch. "
                "Return for a separate explicit Gate B2 authorization"
            ),
        },
    }
    response = q.verify_founder_record(api=routes.__getitem__)
    assert response["direct_founder_github_signature"] is False
    assert response["scope"] == "UNARMED_ENGINEERING_ONLY"
    routes["issues/comments/6066751157"]["issue_url"] = "foreign"
    with pytest.raises(ValueError, match="issue mismatch"):
        q.verify_founder_record(api=routes.__getitem__)


def test_candidate_exact_live_head_base_and_state(q, monkeypatch):
    base = q.B1_BASE
    head = "1" * 40
    monkeypatch.setenv("EXPECTED_BASE_SHA", base)
    monkeypatch.setenv("PR_NUMBER", "172")
    routes = {
        "git/ref/heads/main": {"object": {"sha": base}},
        "pulls/172": {
            "head": {"sha": head},
            "base": {"sha": base},
            "state": "open",
            "merged": False,
        },
    }
    assert (
        q.validate_live("pull_request", {"checkout_sha": head}, api=routes.__getitem__)["phase"]
        == "candidate"
    )
    routes["pulls/172"]["head"]["sha"] = "0" * 40
    with pytest.raises(ValueError, match="exact-head"):
        q.validate_live("pull_request", {"checkout_sha": head}, api=routes.__getitem__)


def test_postmain_must_use_true_normal_merge_parent_and_pr(q, monkeypatch):
    base = q.B1_BASE
    head = "2" * 40
    merge = "3" * 40
    routes = {
        "git/ref/heads/main": {"object": {"sha": merge}},
        "commits/" + merge + "/pulls": [
            {
                "merged_at": "2026-10-08T10:00:00Z",
                "merge_commit_sha": merge,
                "base": {"ref": "main"},
                "number": 172,
            }
        ],
        "pulls/172": {
            "head": {"sha": head},
            "merge_commit_sha": merge,
        },
    }
    monkeypatch.setattr(q.native, "git", lambda *args: base + " " + head)
    assert (
        q.validate_live("push", {"checkout_sha": merge}, api=routes.__getitem__)["phase"]
        == "post-main"
    )
    routes["pulls/172"]["head"]["sha"] = "changed"
    with pytest.raises(ValueError, match="does not match"):
        q.validate_live("push", {"checkout_sha": merge}, api=routes.__getitem__)


def test_scientific_worker_workflows_still_not_present(contract):
    for key in ("scientific_workflow", "scientific_worker"):
        assert not (ROOT / contract["claim_namespace"][key]).exists()
