"""Negative-case qualification for consumed Attempt-2 ancestry repair; no GitHub I/O."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/qualify_sg000031_postconsumption_ancestry.py"


@pytest.fixture
def verifier():
    spec = importlib.util.spec_from_file_location("r2_postconsumption_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_worker_has_one_full_history_checkout(verifier):
    actual_worker = (ROOT / verifier.WORKFLOW).read_text(encoding="utf-8")
    assert actual_worker.count("fetch-depth: 0") == 1
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in actual_worker


@pytest.mark.parametrize("depth", ["true", "unexpected"])
def test_shallow_or_ambiguous_git_checkout_fails_closed(verifier, depth):
    def git(*args):
        if args == ("rev-parse", "--is-shallow-repository"):
            return depth
        pytest.fail("must reject shallow checkout before ancestry access")
    with pytest.raises(ValueError, match="shallow checkout"):
        verifier.verify_worker_and_ancestry(ROOT, git)


@pytest.mark.parametrize("change", ["tree", "reversed-parents", "missing-parent"])
def test_wrong_tree_or_merge_ancestry_is_rejected(verifier, change):
    def git(*args):
        if args == ("rev-parse", "--is-shallow-repository"):
            return "false"
        if args == ("rev-parse", verifier.ATTEMPT_MAIN + "^{tree}"):
            return "f" * 40 if change == "tree" else verifier.ATTEMPT_TREE
        if args == ("show", "-s", "--format=%P", verifier.ATTEMPT_MAIN):
            parents = verifier.FROZEN_PARENTS
            if change == "reversed-parents":
                return " ".join(reversed(parents))
            if change == "missing-parent":
                return parents[0]
            return " ".join(parents)
        pytest.fail("unexpected Git read")
    with pytest.raises(ValueError, match="tree|parents"):
        verifier.verify_worker_and_ancestry(ROOT, git)


def _fixture(verifier):
    claim = {
        "schema_version": "study1-r2-attempt2-claim-v1",
        "attempt_ordinal": 2,
        "predecessor_attempt_ordinal": 1,
        "run_id": verifier.ATTEMPT_RUN,
        "run_attempt": 1,
        "main_sha": verifier.ATTEMPT_MAIN,
        "tree": verifier.ATTEMPT_TREE,
        "contract_sha256": verifier.CONTRACT_SHA,
        "execution_authorization_sha256": verifier.AUTH_SHA,
        "attempt1_lineage_sha256": verifier.LINEAGE_SHA,
        "engineering_qualified": True,
        "zero_cost_infrastructure_verified": True,
        "qualification_receipt": {
            "r1_manifest_sha256": verifier.R1_SHA,
            "population_sha256": verifier.POPULATION_SHA,
            "producer_identity_sha256": verifier.PRODUCER_SHA,
            "main_sha": verifier.ATTEMPT_MAIN,
            "tree": verifier.ATTEMPT_TREE,
            "base_sha": verifier.REPAIR_MAIN,
            "head_sha": verifier.REPAIR_HEAD,
        },
    }
    claim["qualification_receipt_sha256"] = verifier.native.digest(
        verifier.native.json_bytes(claim["qualification_receipt"])
    )
    routes = {
        "git/ref/tags/dal-r2-issue158-attempt2": {
            "object": {"sha": verifier.ATTEMPT_TAG}
        },
        "git/tags/" + verifier.ATTEMPT_TAG: {
            "object": {
                "sha": verifier.ATTEMPT_MAIN,
                "type": "commit",
                "url": verifier.native.REPOSITORY_API + "/git/commits/"
                + verifier.ATTEMPT_MAIN,
            },
            "message": json.dumps(claim),
        },
        "actions/runs/" + str(verifier.ATTEMPT_RUN): {
            "id": verifier.ATTEMPT_RUN,
            "run_attempt": 1,
            "head_sha": verifier.ATTEMPT_MAIN,
            "path": verifier.EXECUTION_WORKFLOW,
            "event": "workflow_dispatch",
            "status": "completed",
            "conclusion": "failure",
        },
        "actions/workflows/study1-sg000031-r2-attempt2.yml/runs?per_page=100": {
            "total_count": 1,
            "workflow_runs": [{"id": verifier.ATTEMPT_RUN}],
        },
    }
    return routes, claim


def test_consumed_claim_with_frozen_history_passes(verifier, monkeypatch):
    routes, claim = _fixture(verifier)
    monkeypatch.setattr(verifier.native, "lf_digest", lambda *_: verifier.CONTRACT_SHA)
    monkeypatch.setattr(
        verifier, "RECEIPT_SHA", claim["qualification_receipt_sha256"]
    )
    assert verifier.verify_consumed_claim(ROOT, lambda path: routes[path]) == claim


@pytest.mark.parametrize(
    "fault",
    ["tag", "ordinal", "authorization", "wrong-run", "third-dispatch"],
)
def test_incorrect_or_replayed_claim_fails_closed(verifier, monkeypatch, fault):
    routes, claim = _fixture(verifier)
    monkeypatch.setattr(verifier.native, "lf_digest", lambda *_: verifier.CONTRACT_SHA)
    monkeypatch.setattr(
        verifier, "RECEIPT_SHA", claim["qualification_receipt_sha256"]
    )
    if fault == "tag":
        routes["git/ref/tags/dal-r2-issue158-attempt2"]["object"]["sha"] = "0" * 40
    elif fault == "ordinal":
        claim["attempt_ordinal"] = 3
    elif fault == "authorization":
        claim["execution_authorization_sha256"] = "0" * 64
    elif fault == "wrong-run":
        routes["actions/runs/" + str(verifier.ATTEMPT_RUN)]["run_attempt"] = 2
    else:
        routes["actions/workflows/study1-sg000031-r2-attempt2.yml/runs?per_page=100"][
            "total_count"
        ] = 2
    routes["git/tags/" + verifier.ATTEMPT_TAG]["message"] = json.dumps(claim)
    with pytest.raises(ValueError):
        verifier.verify_consumed_claim(ROOT, lambda path: routes[path])


@pytest.mark.parametrize("event", ["workflow_dispatch", "schedule", "repository_dispatch"])
def test_scientific_entrypoints_never_run_postconsumption_preflight(
    verifier, monkeypatch, event
):
    monkeypatch.setenv("GITHUB_REPOSITORY", verifier.native.REPOSITORY)
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    with pytest.raises(ValueError, match="not a scientific dispatch entrypoint"):
        verifier.qualify(ROOT)
