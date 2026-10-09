"""Unarmed Attempt-3 synthetic GitHub atomic-tag protocol tests."""

from __future__ import annotations

import copy
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from gaxbench.study1_attempt3_b2_claim import (
    BASE_MAIN,
    PREVIOUS_CONSUMED,
    REF,
    ClaimProtocolSimulator,
    SimulatedGitHubREST,
    SyntheticAuthority,
    rehearsal,
    verify_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture(run: int = 11) -> SyntheticAuthority:
    return SyntheticAuthority("a" * 40, "b" * 40, run, "c" * 64)


def test_b2_claim_contract_never_arms_science():
    c = verify_plan(ROOT)
    assert c["founder_decision"]["signed_single_run_authority_sha256"] is None
    assert c["protocol"]["create_ref_only"] is True
    assert c["scope"]["real_github_transport_connected"] is False
    assert c["scope"]["model_http_post_permitted"] is False


def test_tag_then_ref_once_and_duplicate_denied():
    api = SimulatedGitHubREST()
    c = ClaimProtocolSimulator(api)
    tag = c.try_claim_synthetic(fixture())
    assert c.verify_synthetic(tag)
    assert api.tag_posts == 1 and api.ref_posts == 1
    with pytest.raises(PermissionError):
        c.try_claim_synthetic(fixture(22))
    assert api.tag_posts == 1 and api.ref_posts == 1


def test_twelve_racing_writers_only_one_wins():
    api = SimulatedGitHubREST()
    barrier = Barrier(12)

    def runner(n: int) -> bool:
        barrier.wait(timeout=15)
        try:
            ClaimProtocolSimulator(api).try_claim_synthetic(fixture(n + 1))
            return True
        except PermissionError:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(runner, range(12)))
    assert sum(results) == 1
    assert len(api.references) == 1


def test_orphan_tag_does_not_create_claim():
    api = SimulatedGitHubREST()
    api.fail_between_tag_and_ref = True
    with pytest.raises(PermissionError):
        ClaimProtocolSimulator(api).try_claim_synthetic(fixture())
    assert len(api.tag_objects) == 1
    assert api.get_ref(REF) is None
    # The original authorization must remain unusable after an ambiguous failure.
    api.fail_between_tag_and_ref = False
    with pytest.raises(PermissionError, match="NO RETRY"):
        ClaimProtocolSimulator(api).try_claim_synthetic(fixture())
    with pytest.raises(PermissionError, match="NO RETRY"):
        ClaimProtocolSimulator(api).try_claim_synthetic(fixture(44))
    assert api.tag_posts == 1
    assert api.ref_posts == 1


def test_new_synthetic_authority_is_distinct_after_orphan_failure():
    api = SimulatedGitHubREST()
    api.fail_between_tag_and_ref = True
    with pytest.raises(PermissionError):
        ClaimProtocolSimulator(api).try_claim_synthetic(fixture())
    api.fail_between_tag_and_ref = False
    separate_mock = SyntheticAuthority("a" * 40, "b" * 40, 22, "d" * 64)
    tag = ClaimProtocolSimulator(api).try_claim_synthetic(separate_mock)
    assert api.get_ref(REF) == tag
    assert len(api.reserved_synthetic_signatures) == 2
    assert len(api.references) == 1


def test_pre_model_failure_still_consumes_ref():
    api = SimulatedGitHubREST()
    ClaimProtocolSimulator(api).try_claim_synthetic(fixture())
    with pytest.raises(PermissionError):
        ClaimProtocolSimulator(api).try_claim_synthetic(fixture(99))
    assert len(api.references) == 1


def test_absent_or_modified_receipt_fails_verification():
    api = SimulatedGitHubREST()
    ctrl = ClaimProtocolSimulator(api)
    tag = ctrl.try_claim_synthetic(fixture())
    assert ctrl.verify_synthetic(tag)
    assert not ctrl.verify_synthetic("d" * 40)
    assert not ctrl.verify_synthetic("bad")
    with pytest.raises(PermissionError):
        api.patch_ref(REF, "e" * 40)
    with pytest.raises(PermissionError):
        api.delete_ref(REF)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("engineering_baseline", "main_sha", "f" * 40),
        ("engineering_baseline", "tree_sha", "f" * 40),
        ("engineering_baseline", "b2_readiness_sha256", "0" * 64),
        ("founder_decision", "comment_id", 0),
        ("founder_decision", "signed_single_run_authority_sha256", "c" * 64),
        ("founder_decision", "pinned_founder_public_key_sha256", "c" * 64),
        ("founder_decision", "cryptographic_signature_verified", True),
        ("protocol", "http_ref_create", "PATCH /git/refs"),
        ("protocol", "create_ref_only", False),
        ("protocol", "no_ref_update", False),
        ("protocol", "no_ref_delete", False),
        ("protocol", "ref", "refs/tags/other"),
        ("protocol", "collision", "RETRY"),
        ("protocol", "orphan_tag", "RETRY"),
        ("identity", "attempt_ordinal", 2),
        ("identity", "development_rows", 1462),
        ("identity", "shards", 9),
        ("identity", "population_sha256", "f" * 64),
        ("identity", "producer_sha256", "f" * 64),
        ("identity", "sealed_final_rows", 174),
        ("identity", "attempt2_authority_consumed_sha256", "f" * 64),
        ("scope", "real_github_transport_connected", True),
        ("scope", "real_github_api_mutation_permitted", True),
        ("scope", "real_claim_exists", True),
        ("scope", "model_http_post_permitted", True),
        ("scope", "scientific_workflow_available", True),
        ("scope", "empirically_qualified_free_compute", True),
        ("scope", "training", True),
        ("scope", "d4", True),
        ("scope", "final_content_access", True),
        ("scope", "founder_cost_usd", 1),
        ("scope", "science", "PASS"),
    ],
)
def test_mutation_of_frozen_claim_contract_is_rejected(section, field, value):
    data = copy.deepcopy(verify_plan(ROOT))
    data[section][field] = value
    with pytest.raises(ValueError):
        verify_plan(ROOT, data)


@pytest.mark.parametrize(
    "mutation",
    [
        {"commit_sha": "bad"},
        {"commit_sha": BASE_MAIN},
        {"tree_sha": "bad"},
        {"run_id": 0},
        {"run_id": True},
        {"signature_digest": PREVIOUS_CONSUMED},
        {"signature_digest": "not-sha"},
        {"marker": "not-a-test-fixture"},
    ],
)
def test_non_synthetic_or_invalid_input_denied_before_tag(mutation):
    data = fixture().__dict__.copy()
    data.update(mutation)
    api = SimulatedGitHubREST()
    with pytest.raises(PermissionError):
        ClaimProtocolSimulator(api).try_claim_synthetic(SyntheticAuthority(**data))
    assert api.tag_posts == 0


def test_production_entrypoints_are_sealed():
    api = SimulatedGitHubREST()
    c = ClaimProtocolSimulator(api)
    for action in (c.claim_real, c.replay, c.dispatch):
        with pytest.raises(PermissionError):
            action(fixture())
    with pytest.raises(PermissionError):
        ClaimProtocolSimulator(object())


def test_impossible_ref_or_tag_shape_is_refused():
    api = SimulatedGitHubREST()
    with pytest.raises(ValueError):
        api.post_ref(REF, "a" * 40)
    with pytest.raises(ValueError):
        api.post_ref("refs/tags/unrelated", "a" * 40)
    with pytest.raises(ValueError):
        api.post_tag({"tag": "unrelated"})


def test_end_to_end_rehearsal_requires_no_network(monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError("unarmed synthetic test cannot connect")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    report = rehearsal(ROOT)
    assert report["synthetic_claim_consumed_once"]
    assert report["duplicate_denied"]
    assert report["real_api_calls"] == 0
    assert report["model_posts"] == 0
    assert report["rows_replayed"] == 0
    assert report["science"] == "BLOCKED"
