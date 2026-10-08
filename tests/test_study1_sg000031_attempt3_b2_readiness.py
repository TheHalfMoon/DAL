"""B2 founder consent provenance, capacity inventory and no-science negative tests."""

from __future__ import annotations

import copy
import socket
from pathlib import Path

import pytest

from gaxbench.study1_attempt3_b2_readiness import (
    BASE_MAIN,
    GIB,
    SignedExecutionGate,
    capacity_diagnostic,
    verify_readiness,
)

ROOT = Path(__file__).resolve().parents[1]


def test_founder_provenance_keeps_transcribed_chat_distinct_from_signed_token():
    c = verify_readiness(ROOT)
    assert c["founder"]["verbatim_reply"] == "i approve move on"
    assert "assistant_transcription" in c["founder"]["evidence_provenance"]
    assert c["execution_authority"]["founder_signed_execution_authorization_sha256"] is None
    assert c["execution_authority"]["one_real_attempt_allowed"] is False
    assert c["engineering_baseline"]["main_sha"] == BASE_MAIN


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("founder", "verbatim_reply", "I sign a real execution token"),
        ("founder", "evidence_provenance", "direct_founder_github_signature"),
        ("founder", "assistant_transcribed_chat_comment_id", 0),
        ("engineering_baseline", "main_sha", "0" * 40),
        ("engineering_baseline", "tree_sha", "0" * 40),
        ("frozen_predecessor", "b1_durable_sha256", "0" * 64),
        ("frozen_science", "r1_manifest_sha256", "0" * 64),
        ("frozen_science", "development_rows", 1462),
        ("frozen_science", "calibration_rows", 340),
        ("frozen_science", "validation_rows", 1123),
        ("frozen_science", "shards", 7),
        ("frozen_science", "sealed_final_rows", 174),
        ("execution_authority", "status", "SIGNED_AND_DISPATCHABLE"),
        ("execution_authority", "founder_signed_execution_authorization_sha256", "a" * 64),
        ("execution_authority", "authenticated_github_founder_signature", True),
        ("execution_authority", "run_id", 1),
        ("execution_authority", "canonical_execution_main_sha", BASE_MAIN),
        ("execution_authority", "canonical_execution_tree_sha", "a" * 40),
        ("execution_authority", "one_real_attempt_allowed", True),
        ("execution_authority", "git_ref_creation_allowed", True),
        ("execution_authority", "model_http_post_allowed", True),
        ("execution_authority", "scientific_workflow_dispatch_allowed", True),
        ("capacity_preflight", "status", "QUALIFIED"),
        ("capacity_preflight", "host_snapshot_is_sufficient", True),
        ("capacity_preflight", "frozen_model_download_and_cpu_inference_qualified", True),
        ("claim", "real_claim_created", True),
        ("claim", "tag_ref", "refs/tags/dal-r2-issue158-attempt2"),
        ("claim", "consumed_prior_attempt2_authorization_sha256", "0" * 64),
        ("firewall", "r2", "PASS"),
        ("firewall", "final", "OPEN"),
        ("firewall", "scientific_row_replays", 1),
        ("firewall", "model_posts", 1),
        ("firewall", "permanent_scientific_claims", 1),
        ("firewall", "founder_cost_usd", 1),
        ("firewall", "no_training", False),
        ("firewall", "no_d4", False),
        ("firewall", "no_final_access", False),
    ],
)
def test_forged_or_drifted_scope_cannot_become_a_real_execution_authority(section, field, value):
    c = copy.deepcopy(verify_readiness(ROOT))
    c[section][field] = value
    with pytest.raises(ValueError):
        verify_readiness(ROOT, c)


@pytest.mark.parametrize(
    "method", ["authorize", "claim", "load_rows", "send_model_post", "dispatch"]
)
def test_real_execution_surfaces_fail_closed(method):
    with pytest.raises(PermissionError):
        getattr(SignedExecutionGate(), method)("fake-founder-consent")


def test_insufficient_host_resources_are_diagnostics_not_dispatch():
    d = capacity_diagnostic(
        available_memory_bytes=int(2.58 * GIB),
        available_disk_bytes=int(6.23 * GIB),
    )
    assert d["status"].startswith("BLOCKED")
    assert not d["ram_floor_met"] and not d["disk_floor_met"]
    assert d["scientific_dispatch_allowed"] is False


def test_abundant_mock_resources_still_not_a_license_to_dispatch():
    d = capacity_diagnostic(
        available_memory_bytes=64 * GIB,
        available_disk_bytes=128 * GIB,
        pinned_model_verified=True,
    )
    assert d["ram_floor_met"] and d["disk_floor_met"]
    assert not d["empirical_runtime_qualification"]
    assert not d["scientific_dispatch_allowed"]


@pytest.mark.parametrize("ram,disk", [(-1, 5), (5, -1), (True, 0), (float("nan"), 0)])
def test_invalid_capacity_readings_refuse(ram, disk):
    with pytest.raises(ValueError):
        capacity_diagnostic(available_memory_bytes=ram, available_disk_bytes=disk)


def test_no_network_access_needed_for_b2_preflight(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden for static B2 preflight")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    verify_readiness(ROOT)
    assert (
        capacity_diagnostic(available_memory_bytes=0, available_disk_bytes=0)[
            "scientific_dispatch_allowed"
        ]
        is False
    )
