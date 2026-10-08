"""Fail-closed tests for unarmed Attempt-3 readiness, with no remote calls."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/qualify_sg000031_attempt3_readiness.py"


@pytest.fixture
def q():
    spec = importlib.util.spec_from_file_location("attempt3_readiness_test", PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def contract(q):
    return q.read_contract(ROOT)


def test_unarmed_policy_and_protected_sources_pass(q, contract):
    q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("status", "AUTHORIZED"),
    ("sha256", "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"),
    ("dispatch_permitted", True),
    ("claim_permitted", True),
])
def test_attempt2_authorization_cannot_arm_attempt3(q, contract, field, value):
    contract["execution_authorization"][field] = value
    with pytest.raises(ValueError, match="authorization"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("model_calls_permitted", True),
    ("scope", "scientific-dispatch"),
    ("issue", 158),
])
def test_engineering_scope_is_not_scientific_authority(q, contract, field, value):
    contract["engineering_authorization"][field] = value
    with pytest.raises(ValueError, match="engineering authorization"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("final_content_access", True),
    ("final_rows_materialized", 1),
    ("d4", True),
    ("training", True),
    ("founder_cost_usd", 1),
])
def test_final_firewall_and_zero_cost_are_immutable(q, contract, field, value):
    contract["readiness"][field] = value
    with pytest.raises(ValueError, match="final access"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("automatic_retry", True),
    ("attempt3_dispatches_allowed", 1),
    ("preflight_http_mutations_allowed", True),
    ("third_execution_requires_separate_founder_authorization", False),
])
def test_no_retry_mutation_or_auto_dispatch(q, contract, field, value):
    contract["governance"][field] = value
    with pytest.raises(ValueError, match="science firewall"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("r1_manifest_sha256", "0" * 64),
    ("population_identity_sha256", "0" * 64),
    ("producer_identity_sha256", "0" * 64),
    ("development_rows", 1462),
    ("sealed_final_patients", 41),
])
def test_frozen_science_and_population_unchanged(q, contract, field, value):
    contract["scientific_freeze"][field] = value
    with pytest.raises(ValueError, match="freeze"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("field,value", [
    ("permanent_ref", "refs/tags/dal-r2-issue158-attempt2"),
    ("ledger_branch", "codex/sg000031-r2-attempt2-journal"),
    ("receipt_marker", "DAL_R2_ATTEMPT2_CANONICAL_ADMISSION_V1"),
])
def test_namespace_reuse_fails_closed(q, contract, field, value):
    contract["reserved_namespace"][field] = value
    with pytest.raises(ValueError, match="namespace"):
        q.check_policy(ROOT, contract)


@pytest.mark.parametrize("ordinal,run_id", [(2, 37653806159), (3, 37653806159), (1, 999)])
def test_attempt_history_cannot_be_rewritten(q, contract, ordinal, run_id):
    contract["historical_attempts"][0]["ordinal"] = ordinal
    contract["historical_attempts"][0]["run_id"] = run_id
    with pytest.raises(ValueError, match="predecessors|dispatch identity"):
        q.check_policy(ROOT, contract)


def _routes(q, contract):
    old = contract["historical_attempts"][1]
    routes = {
        "actions/runs/37320473498": {
            "id": 37320473498, "run_attempt": 1,
            "status": "completed", "conclusion": "failure",
            "event": "workflow_dispatch",
        },
        "actions/runs/37653806159": {
            "id": 37653806159, "run_attempt": 1,
            "status": "completed", "conclusion": "failure",
            "event": "workflow_dispatch",
        },
        "git/ref/tags/dal-r2-issue158-attempt2": {
            "object": {"sha": old["claim_tag_object"]}
        },
        "git/tags/" + old["claim_tag_object"]: {
            "object": {"sha": old["canonical_main"]},
            "message": json.dumps({
                "execution_authorization_sha256":
                    old["execution_authorization_sha256"]
            }),
        },
        "actions/workflows/study1-sg000031-r2-recovery.yml/runs?per_page=100": {
            "total_count": 1, "workflow_runs": [{"id": 37320473498}]
        },
        "actions/workflows/study1-sg000031-r2-attempt2.yml/runs?per_page=100": {
            "total_count": 1, "workflow_runs": [{"id": 37653806159}]
        },
    }

    def api(path):
        if path == "git/ref/tags/dal-r2-issue166-attempt3":
            raise HTTPError("https://api.github.com", 404, "Not Found", {}, None)
        return routes[path]
    return routes, api


def test_live_history_synthetic_success_no_attempt3(q, contract):
    _, api = _routes(q, contract)
    assert q.check_history(ROOT, contract, api=api)["attempt3_tag_present"] is False


@pytest.mark.parametrize("fault", [
    "attempt1_not_failed", "attempt2_rerun", "additional_dispatch",
    "attempt2_tag_mutated", "attempt3_tag_exists",
])
def test_historical_and_attempt3_claim_faults_fail_closed(q, contract, fault):
    routes, base_api = _routes(q, contract)
    old = contract["historical_attempts"][1]
    if fault == "attempt1_not_failed":
        routes["actions/runs/37320473498"]["conclusion"] = "success"
    elif fault == "attempt2_rerun":
        routes["actions/runs/37653806159"]["run_attempt"] = 2
    elif fault == "additional_dispatch":
        routes["actions/workflows/study1-sg000031-r2-attempt2.yml/runs?per_page=100"][
            "total_count"
        ] = 2
    elif fault == "attempt2_tag_mutated":
        routes["git/ref/tags/dal-r2-issue158-attempt2"]["object"]["sha"] = "0" * 40

    def api(path):
        if fault == "attempt3_tag_exists" and path == (
            "git/ref/tags/dal-r2-issue166-attempt3"
        ):
            return {"object": {"sha": "0" * 40}}
        return base_api(path)

    with pytest.raises(ValueError):
        q.check_history(ROOT, contract, api=api)
    assert old["run_id"] == 37653806159


@pytest.mark.parametrize("event", ["workflow_dispatch", "schedule", "repository_dispatch"])
def test_scientific_events_cannot_enter_readiness(q, monkeypatch, event):
    monkeypatch.setenv("GITHUB_REPOSITORY", q.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    with pytest.raises(ValueError, match="only automated engineering"):
        q.qualify(ROOT)


def test_wrong_repository_rejected_before_any_io(q, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "foreign/other")
    with pytest.raises(ValueError, match="wrong repository"):
        q.qualify(ROOT)
