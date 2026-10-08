"""All Attempt-3 admission tests are synthetic: no GitHub, model or patient I/O."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from gaxbench.study1_attempt3_admission import (
    Attempt3AdmissionController,
    Attempt3AdmissionWorker,
    check_contract,
    load_contract,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def contract():
    return load_contract(ROOT)


@pytest.fixture
def qualifier():
    path = ROOT / "tools/qualify_sg000031_attempt3_admission.py"
    spec = importlib.util.spec_from_file_location("dal_attempt3_qualifier", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_real_contract_is_strictly_unarmed(contract):
    evidence = check_contract(ROOT, contract)
    assert evidence["protected_files"] == 43
    assert evidence["unarmed"] is True


def test_controller_rehearsal_is_never_scientific(contract):
    result = Attempt3AdmissionController(contract).rehearse(ROOT)
    assert result["engineering_admission"] == "REHEARSED_UNARMED"
    assert result["model_posts"] == 0
    assert result["rows_replayed"] == 0
    assert result["permanent_claim_created"] is False
    assert result["scientific_execution_authorized"] is False
    assert result["final_content_access"] is False


@pytest.mark.parametrize("method", ["dispatch", "create_claim"])
def test_controller_has_no_permitted_scientific_side_effects(contract, method):
    controller = Attempt3AdmissionController(contract)
    with pytest.raises(PermissionError, match="NOT_AUTHORIZED"):
        getattr(controller, method)({"fake": "payload"})


def test_worker_cannot_execute():
    with pytest.raises(PermissionError, match="NOT_AUTHORIZED"):
        Attempt3AdmissionWorker().execute({"fake": "payload"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "AUTHORIZED"),
        ("sha256", "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"),
        ("dispatch_permitted", True),
        ("permanent_claim_permitted", True),
        ("model_calls_permitted", True),
        ("row_replay_permitted", True),
    ],
)
def test_arming_and_consumed_consent_reuse_rejected(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["execution_authorization"][field] = value
    with pytest.raises(ValueError, match="authorization"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("r2_state", "COMPLETE"),
        ("final_role", "OPEN"),
        ("final_content_access", True),
        ("final_rows_materialized", 173),
        ("training", True),
        ("fine_tuning", True),
        ("d4", True),
        ("scientific_dispatches", 1),
        ("model_posts", 1),
        ("founder_cost_usd", 1),
    ],
)
def test_scientific_final_and_cost_firewalls_rejected(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["firewall"][field] = value
    with pytest.raises(ValueError, match="firewall"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("read_only_http", False),
        ("synthetic_rehearsal_only", False),
        ("all_production_mutations_prohibited", False),
        ("worker_runtime_created", True),
        ("scientific_workflow_created", True),
        ("automatic_retry", True),
        ("next_scientific_execution_requires_new_founder_approval", False),
    ],
)
def test_admission_interlock_rejects_mutation(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["admission"][field] = value
    with pytest.raises(ValueError, match="interlock"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("r1_manifest_sha256", "0" * 64),
        ("producer_identity_sha256", "0" * 64),
        ("population_identity_sha256", "0" * 64),
        ("development_rows", 1462),
        ("calibration_rows", 340),
        ("sealed_final_patients", 41),
    ],
)
def test_freeze_drift_fail_closed(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["scientific_freeze"][field] = value
    with pytest.raises(ValueError, match="freeze"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("issue", 158),
        ("transcribed_comment_id", 6050120310),
        ("scientific_execution_authorized", True),
        ("provenance", "founder-direct-github-signature"),
    ],
)
def test_authorization_provenance_not_forgeable(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["engineering_authorization"][field] = value
    with pytest.raises(ValueError, match="provenance"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("permanent_ref", "refs/tags/dal-r2-issue158-attempt2"),
        ("ledger_branch", "codex/sg000031-r2-attempt2-journal"),
        ("scientific_workflow", ".github/workflows/study1-sg000031-r2-attempt2.yml"),
    ],
)
def test_historical_namespace_reuse_rejected(contract, field, value):
    altered = copy.deepcopy(contract)
    altered["reserved_scientific_namespace"][field] = value
    with pytest.raises(ValueError, match="namespace"):
        check_contract(ROOT, altered)


@pytest.mark.parametrize("event", ["workflow_dispatch", "schedule", "repository_dispatch"])
def test_manual_or_scientific_ci_event_rejected(qualifier, monkeypatch, event):
    monkeypatch.setenv("GITHUB_REPOSITORY", qualifier.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    with pytest.raises(ValueError, match="event is forbidden"):
        qualifier.validate_event_environment()


def test_wrong_repo_and_rerun_rejected(qualifier, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "other/DAL")
    with pytest.raises(ValueError, match="wrong admission repository"):
        qualifier.validate_event_environment()
    monkeypatch.setenv("GITHUB_REPOSITORY", qualifier.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    with pytest.raises(ValueError, match="reruns"):
        qualifier.validate_event_environment()


def test_founder_issue_requires_transcription_disclosure(qualifier):
    routes = {
        "issues/168": {"number": 168, "state": "open"},
        "issues/comments/6062562405": {
            "body": (
                "FOUNDER DECISION — OPTION A APPROVED; transcribed from founder instruction;"
                " scientific dispatch, model calls, row replay; founder-cost requirement"
            )
        },
    }
    assert (
        qualifier.check_founder_engineering_scope(api=routes.__getitem__)[
            "original_authorship_independently_attested_on_github"
        ]
        is False
    )
    routes["issues/comments/6062562405"]["body"] = "approval without scope"
    with pytest.raises(ValueError, match="incomplete"):
        qualifier.check_founder_engineering_scope(api=routes.__getitem__)


def test_candidate_live_head_and_base_fail_closed(qualifier, contract, monkeypatch):
    monkeypatch.setenv("PR_NUMBER", "171")
    monkeypatch.setenv("EXPECTED_BASE_SHA", contract["engineering_base"]["sha"])
    routes = {
        "git/ref/heads/main": {"object": {"sha": contract["engineering_base"]["sha"]}},
        "pulls/171": {
            "head": {"sha": "1" * 40},
            "base": {"sha": contract["engineering_base"]["sha"]},
        },
    }
    ancestry = {"checkout_sha": "1" * 40}
    assert (
        qualifier.check_live_identity("pull_request", ancestry, contract, api=routes.__getitem__)[
            "phase"
        ]
        == "candidate"
    )
    routes["pulls/171"]["head"]["sha"] = "0" * 40
    with pytest.raises(ValueError, match="exact head"):
        qualifier.check_live_identity("pull_request", ancestry, contract, api=routes.__getitem__)


def test_postmain_must_be_exact_normal_merge(qualifier, contract, monkeypatch):
    head = "3" * 40
    base = contract["engineering_base"]["sha"]
    actual_head = "2" * 40
    routes = {
        "git/ref/heads/main": {"object": {"sha": head}},
        "commits/" + head + "/pulls": [
            {
                "merged_at": "2026-10-08T12:00:00Z",
                "merge_commit_sha": head,
                "base": {"ref": "main"},
                "number": 171,
            }
        ],
        "pulls/171": {
            "merge_commit_sha": head,
            "base": {"ref": "main"},
            "head": {"sha": actual_head},
        },
    }
    monkeypatch.setattr(qualifier.native, "git", lambda *args: base + " " + actual_head)
    assert (
        qualifier.check_live_identity(
            "push", {"checkout_sha": head}, contract, api=routes.__getitem__
        )["phase"]
        == "post-main"
    )
    routes["pulls/171"]["head"]["sha"] = "bad"
    with pytest.raises(ValueError, match="normal merge"):
        qualifier.check_live_identity(
            "push", {"checkout_sha": head}, contract, api=routes.__getitem__
        )


def test_new_namespace_has_no_production_workflows(contract):
    assert not (ROOT / contract["reserved_scientific_namespace"]["scientific_workflow"]).exists()
    assert not (ROOT / contract["reserved_scientific_namespace"]["worker"]).exists()
    assert contract["execution_authorization"]["sha256"] is None
