"""Isolated fake GitHub ref and synthetic worker contract negative tests."""

from __future__ import annotations

import copy
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from gaxbench.study1_attempt3_b1_durable import (
    A2_CONSUMED_SHA,
    CLAIM_REF,
    MARKER,
    InMemoryGitHubRefService,
    SimulatedB2Envelope,
    UnarmedDurableClaimDesign,
    UnarmedWorkerBlueprint,
    canonical,
    synthetic_durable_rehearsal,
    verify_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture(run_id: int = 101) -> SimulatedB2Envelope:
    return SimulatedB2Envelope(
        base_main="a" * 40,
        base_tree="b" * 40,
        run_id=run_id,
        authorization_sha256="c" * 64,
    )


def native_module():
    path = ROOT / "tools/qualify_sg000031_attempt3_b1_durable.py"
    spec = importlib.util.spec_from_file_location("dal_b1_durable_native", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_durable_contract_binds_real_predecessor_and_prompt_schema():
    c = verify_contract(ROOT)
    assert c["authority"]["authorization_sha256"] is None
    assert c["founder_gate"]["scope"] == "ENGINEERING_ONLY_UNARMED"
    assert c["safety"]["science_state"] == "BLOCKED"
    assert c["durable_claim"]["real_mutation_allowed"] is False


@pytest.mark.parametrize(
    "name,value",
    [
        ("authorization_sha256", A2_CONSUMED_SHA),
        ("verified_signature", True),
        ("real_dispatch_permitted", True),
        ("approval_record", "approved"),
        ("main_sha", "a" * 40),
        ("main_tree", "b" * 40),
        ("live_run_id", 101),
    ],
)
def test_durable_policy_rejects_actual_authorization_in_b1(name, value):
    original = verify_contract(ROOT)
    bad = copy.deepcopy(original)
    bad["authority"][name] = value
    with pytest.raises(ValueError, match="scientific execution authorization"):
        verify_contract(ROOT, bad)


def test_synthetic_claim_is_atomic_and_consumed_immediately():
    svc = InMemoryGitHubRefService()
    one = UnarmedDurableClaimDesign(svc)
    sha = one.claim_synthetic(fixture())
    assert one.verify_synthetic(sha)
    assert svc.accepted == 1
    assert svc.attempts == 1
    with pytest.raises(PermissionError, match="no retries"):
        UnarmedDurableClaimDesign(svc).claim_synthetic(fixture(run_id=102))
    assert svc.accepted == 1
    assert svc.attempts == 2


def test_claim_race_exactly_one_wins_across_controller_instances():
    svc = InMemoryGitHubRefService()
    barrier = Barrier(12)

    def attempt(n: int) -> bool:
        c = UnarmedDurableClaimDesign(svc)
        barrier.wait(timeout=15)
        try:
            c.claim_synthetic(fixture(run_id=n + 1))
            return True
        except PermissionError:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(attempt, range(12)))
    assert sum(outcomes) == 1
    assert svc.attempts == 12
    assert svc.accepted == 1
    assert svc.read_ref(CLAIM_REF) is not None


def test_pre_model_failure_consumes_tag_no_retry():
    svc = InMemoryGitHubRefService()
    sha = UnarmedDurableClaimDesign(svc).claim_synthetic(fixture())
    # Simulated failure before a worker could possibly run; no recovery/retry.
    assert UnarmedDurableClaimDesign(svc).verify_synthetic(sha)
    with pytest.raises(PermissionError, match="no retries"):
        UnarmedDurableClaimDesign(svc).claim_synthetic(fixture())
    assert svc.accepted == 1


def test_interrupted_shard_keeps_tag_consumed():
    svc = InMemoryGitHubRefService()
    first = UnarmedDurableClaimDesign(svc)
    digest = first.claim_synthetic(fixture())
    worker = UnarmedWorkerBlueprint(ROOT)
    proof = worker.rehearse_after_claim(first, digest)
    assert proof["shard_counts"] == [183] * 7 + [182]
    with pytest.raises(PermissionError, match="Gate B2"):
        worker.execute(shard_index=4)
    with pytest.raises(PermissionError, match="no retries"):
        first.claim_synthetic(fixture(run_id=200))
    assert svc.accepted == 1


def test_worker_rejects_every_real_execution_surface():
    worker = UnarmedWorkerBlueprint(ROOT)
    for call in (worker.execute, worker.send_model_http, worker.replay_rows, worker.access_final):
        with pytest.raises(PermissionError):
            call("do-not-do-science")


def test_worker_cannot_accept_unclaimed_or_tampered_receipt():
    svc = InMemoryGitHubRefService()
    design = UnarmedDurableClaimDesign(svc)
    worker = UnarmedWorkerBlueprint(ROOT)
    with pytest.raises(PermissionError, match="no valid synthetic"):
        worker.rehearse_after_claim(design, "0" * 64)
    digest = design.claim_synthetic(fixture())
    assert worker.rehearse_after_claim(design, digest)["model_posts"] == 0
    with pytest.raises(PermissionError, match="no valid synthetic"):
        worker.rehearse_after_claim(design, "f" * 64)


@pytest.mark.parametrize(
    "mutation",
    [
        {"fixture_marker": "FOUNDER_B2_APPROVED"},
        {"base_main": "not-a-sha"},
        {"base_main": "eee686d05332ed5fad93a52c75ca50dbee9cb877"},
        {"base_tree": "not-a-sha"},
        {"run_id": 0},
        {"run_id": True},
        {"authorization_sha256": "0"},
        {"authorization_sha256": A2_CONSUMED_SHA},
    ],
)
def test_synthetic_fixture_must_not_masquerade_as_execution_authorization(mutation):
    params = fixture().__dict__.copy()
    params.update(mutation)
    svc = InMemoryGitHubRefService()
    with pytest.raises(PermissionError):
        UnarmedDurableClaimDesign(svc).claim_synthetic(SimulatedB2Envelope(**params))
    assert svc.accepted == 0


def test_real_adapter_or_real_claim_is_impossible():
    with pytest.raises(PermissionError, match="real GitHub writer"):
        UnarmedDurableClaimDesign(object())
    with pytest.raises(PermissionError, match="Gate B2"):
        UnarmedDurableClaimDesign(InMemoryGitHubRefService()).claim_real(fixture())


def test_no_ref_overwrite_or_delete_and_no_second_mutation():
    svc = InMemoryGitHubRefService()
    design = UnarmedDurableClaimDesign(svc)
    first = design.claim_synthetic(fixture())
    with pytest.raises(PermissionError, match="immutable"):
        svc.update_ref(CLAIM_REF, "a" * 40)
    with pytest.raises(PermissionError, match="immutable"):
        svc.delete_ref(CLAIM_REF)
    assert design.verify_synthetic(first)


def test_payload_is_non_sensitive_canonical_json():
    payload = fixture().as_dict()
    data = canonical(payload)
    assert b"question" not in data
    assert b"patient" not in data
    assert b"true_answer" not in data
    assert MARKER.encode() in data


def test_synthetic_end_to_end_no_network_or_science(monkeypatch):
    # Network is disabled completely while constructing claim and worker plan.
    import socket

    def forbidden(*args, **kwargs):
        raise AssertionError("network access forbidden in B1 simulation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    report = synthetic_durable_rehearsal(ROOT)
    assert report["simulated_ref_created_once"]
    assert report["simulated_duplicate_denied"]
    assert report["real_github_mutations"] == 0
    assert report["model_posts"] == 0
    assert report["rows_replayed"] == 0
    assert report["permanent_scientific_claim"] is False
    assert report["B2_authorized"] is False
    assert report["r2"] == "BLOCKED"
    assert report["founder_cost_usd"] == 0


def test_native_v2_qualification_has_no_real_claim_or_dispatch():
    q = native_module()
    assert q.SCHEMA.endswith("durable-native-v1")
    assert q.MAIN_BASE == "eee686d05332ed5fad93a52c75ca50dbee9cb877"
    assert q.FOUNDER_COMMENT == 6066751157


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("founder_gate", "scope", "SCIENTIFIC_EXECUTION"),
        ("base", "main", "0" * 40),
        ("frozen_predecessor", "sha256", "0" * 64),
        ("producer", "system_prompt_sha256", "0" * 64),
        ("producer", "tool_schema_sha256", "0" * 64),
        ("durable_claim", "real_mutation_allowed", True),
        ("durable_claim", "no_delete", False),
        ("durable_claim", "no_update", False),
        ("durable_claim", "ref", "refs/tags/dal-r2-issue158-attempt2"),
        ("runtime", "shards", 9),
        ("runtime", "rows", 1462),
        ("runtime", "model_retry", 1),
        ("runtime", "persistent_row_write", True),
        ("runtime", "final_access", True),
        ("transport", "http_post_allowed", True),
        ("transport", "api_credentials_allowed", True),
        ("safety", "science_state", "PASS"),
        ("safety", "permanent_scientific_claim", True),
        ("safety", "founder_cost_usd", 1),
    ],
)
def test_durable_contract_fails_closed_on_science_or_mutation_scope(section, key, value):
    contract = copy.deepcopy(verify_contract(ROOT))
    contract[section][key] = value
    with pytest.raises(ValueError):
        verify_contract(ROOT, contract)


def test_simulated_gh_concurrent_clients_share_one_durable_ref():
    store = InMemoryGitHubRefService()
    client_one = UnarmedDurableClaimDesign(store)
    client_two = UnarmedDurableClaimDesign(store)
    sha = client_one.claim_synthetic(fixture())
    assert client_two.verify_synthetic(sha)
    with pytest.raises(PermissionError, match="no retries"):
        client_two.claim_synthetic(fixture(run_id=999))


def test_read_only_native_b1_runtime_rejects_existing_attempt3_ref(monkeypatch):
    q = native_module()
    monkeypatch.setattr(q.native, "api", lambda *_: {"object": {"sha": "a" * 40}})
    with pytest.raises(PermissionError, match="already exists"):
        q.no_permanent_attempt3_ref()
