"""Negative-only checks for the prospective B2 native GitHub read-only gate.

The dedicated native workflow is absent. This test MUST NOT be substituted for
a genuine workflow run or a signed one-shot scientific execution authority.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))

import qualify_sg000031_attempt3_b2_claim as gate  # noqa: E402


def test_existing_real_ref_always_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate.native, "api", lambda _: {"object": {"sha": "a" * 40}})
    with pytest.raises(PermissionError, match="actual Attempt-3"):
        gate.check_real_ref_absent()


def test_404_means_ref_absence_not_claim_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent(_path: str) -> None:
        raise HTTPError("https://api.github.com", 404, "Not Found", None, None)

    monkeypatch.setattr(gate.native, "api", absent)
    assert gate.check_real_ref_absent() is None


def test_403_or_transport_error_is_not_interpreted_as_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(_path: str) -> None:
        raise HTTPError("https://api.github.com", 403, "Access denied", None, None)

    monkeypatch.setattr(gate.native, "api", forbidden)
    with pytest.raises(HTTPError) as exc:
        gate.check_real_ref_absent()
    assert exc.value.code == 403


def test_chat_transcription_cannot_become_signed_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def data(path: str) -> dict[str, object]:
        if path == "issues/175":
            return {"state": "open"}
        return {
            "issue_url": gate.native.REPOSITORY_API + "/issues/171",
            "body": 'User said "i approve move on"; assistant-written NOT signed',
        }

    monkeypatch.setattr(gate.native, "api", data)
    receipt = gate.verify_founder_transcription()
    assert receipt["cryptographically_verified"] is False


def test_fake_chat_signature_or_closed_governance_gate_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def data(path: str) -> dict[str, object]:
        if path == "issues/175":
            return {"state": "closed"}
        return {
            "issue_url": gate.native.REPOSITORY_API + "/issues/171",
            "body": 'User said "i approve move on"; assistant-written NOT signed',
        }

    monkeypatch.setattr(gate.native, "api", data)
    with pytest.raises(ValueError, match="closed"):
        gate.verify_founder_transcription()


def test_missing_native_workflow_must_fail_closed_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Prove workflow absence fails closed without assuming the repository lacks it."""
    monkeypatch.setattr(gate.b1_qual, "check_environment", lambda: "pull_request")
    monkeypatch.setattr(gate, "verify_plan", lambda _root: {"scope": {"science": "BLOCKED"}})
    monkeypatch.setattr(
        gate,
        "rehearsal",
        lambda _root: {
            "real_github_mutations": 0,
            "model_posts": 0,
            "rows_replayed": 0,
            "duplicate_denied": True,
            "synthetic_claim_consumed_once": True,
        },
    )

    def forbidden_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("native qualifier must not access network in offline test")

    monkeypatch.setattr(socket.socket, "connect", forbidden_network)
    assert not (tmp_path / ".github/workflows/study1-sg000031-attempt3-b2-claim.yml").exists()
    with pytest.raises(FileNotFoundError):
        gate.qualify(tmp_path)


def test_workflow_envelope_comments_do_not_count_as_configuration() -> None:
    """Historical substring-only checks incorrectly accepted comment-only YAML."""
    good = (
        "on:\n"
        "  pull_request:\n"
        "  push:\n"
        "permissions:\n"
        "  contents: read\n"
        "jobs:\n"
        "  verify:\n"
        "    steps:\n"
        "      - uses: actions/checkout@0123456789abcdef\n"
        "        with:\n"
        "          persist-credentials: false\n"
        "      - run: python tools/qualify_sg000031_attempt3_b2_claim.py\n"
    )
    assert gate.verify_workflow_envelope(good) is None
    commented = "\n".join("# " + line for line in good.splitlines())
    with pytest.raises(PermissionError, match="required structure"):
        gate.verify_workflow_envelope(commented)
    with pytest.raises(PermissionError, match="required structure"):
        gate.verify_workflow_envelope(good.replace("  push:", "# push:"))
    with pytest.raises(PermissionError, match="event scope"):
        gate.verify_workflow_envelope(good.replace("  push:", "  push:\n  workflow_run:"))
    with pytest.raises(PermissionError, match="prohibited"):
        gate.verify_workflow_envelope(good + "  contents: write\n")
    with pytest.raises(PermissionError, match="prohibited"):
        gate.verify_workflow_envelope(
            good.replace("persist-credentials: false", "persist-credentials: true")
            + "          persist-credentials: false\n"
        )


# Genuine offline SSHSIG verification is tested with throwaway fixture keys only.
# These tests do not create or approve any founder execution authorization.
def authority_fixture() -> dict[str, object]:
    return {
        "schema_version": "dal-sg000031-a3-b2-founder-execution-v1",
        "attempt_ordinal": 3,
        "main_sha": "a" * 40,
        "tree_sha": "b" * 40,
        "run_id": 101,
        "run_attempt": 1,
        "ref": "refs/tags/dal-r2-issue166-attempt3",
        "population_sha256": "0755fcb62129037e05557d73863574b399503458b48b2c5a906546575aa1679f",
        "r1_manifest_sha256": "220c676df241d8dc1ac8ccd83e81d54554e7618fc5acf016eaa32ec6302ca2b0",
        "development_rows": 1463,
        "shards": 8,
        "final_role_access": False,
        "training": False,
        "d4_activation": False,
        "founder_cost_usd": 0,
        "retry_permitted": False,
        "scientific_role": "outcome-exposed-development-only",
        "single_use": True,
    }


def test_signed_auth_requires_independent_trust_pin_before_opening_tools() -> None:
    from gaxbench.study1_attempt3_b2_claim import verify_offline_founder_ssh_signature

    with pytest.raises(PermissionError, match="independently pinned"):
        verify_offline_founder_ssh_signature(
            authorization=authority_fixture(),
            signature=b"fake",
            allowed_signers=b"fake",
            expected_allowed_signers_sha256=None,
            expected_main="a" * 40,
            expected_tree="b" * 40,
        )


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("run_id", 0),
        ("run_id", True),
        ("run_attempt", 2),
        ("main_sha", "f" * 40),
        ("tree_sha", "f" * 40),
        ("attempt_ordinal", 2),
        ("retry_permitted", True),
        ("single_use", False),
        ("final_role_access", True),
        ("founder_cost_usd", 1),
        ("development_rows", 1464),
        ("shards", 9),
        ("scientific_role", "sealed-final"),
    ],
)
def test_signed_manifest_frozen_scope_rejects_mutation(field: str, bad: object) -> None:
    from gaxbench.study1_attempt3_b2_claim import execution_authorization_bytes

    body = authority_fixture()
    body[field] = bad
    with pytest.raises(ValueError, match="scope/identity drift|unique run id"):
        execution_authorization_bytes(body, expected_main="a" * 40, expected_tree="b" * 40)


def test_offline_ed25519_verification_positive_and_tamper_negative(tmp_path: Path) -> None:
    import hashlib
    import os
    import shutil
    import subprocess

    from gaxbench.study1_attempt3_b2_claim import (
        FOUNDER_SSH_NAMESPACE,
        execution_authorization_bytes,
        verify_offline_founder_ssh_signature,
    )

    signer = shutil.which("ssh-keygen")
    if signer is None:
        pytest.skip("OpenSSH unavailable; production verifier would fail closed")
    key_path = tmp_path / "ephemeral-test-only-key"
    keygen = subprocess.run(
        [signer, "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
        capture_output=True,
        timeout=20,
        check=False,
    )
    if keygen.returncode:
        if os.name == "nt":
            pytest.skip("Windows OpenSSH fixture key generation unavailable")
        pytest.fail("Linux OpenSSH fixture key generation unexpectedly failed")
    authority = authority_fixture()
    payload = tmp_path / "test-only-not-an-authorization.json"
    payload.write_bytes(
        execution_authorization_bytes(authority, expected_main="a" * 40, expected_tree="b" * 40)
    )
    signature_cmd = subprocess.run(
        [signer, "-Y", "sign", "-f", str(key_path), "-n", FOUNDER_SSH_NAMESPACE, str(payload)],
        capture_output=True,
        timeout=20,
        check=False,
    )
    if signature_cmd.returncode:
        if os.name == "nt":
            pytest.skip("Windows OpenSSH SSHSIG fixture unavailable")
        pytest.fail("Linux OpenSSH SSHSIG signing unexpectedly failed")
    signature = (tmp_path / (payload.name + ".sig")).read_bytes()
    allowlist = (
        'dal-founder namespaces="'
        + FOUNDER_SSH_NAMESPACE
        + '" '
        + key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
        + "\n"
    ).encode("ascii")
    pin = hashlib.sha256(allowlist).hexdigest()
    args = {
        "authorization": authority,
        "signature": signature,
        "allowed_signers": allowlist,
        "expected_allowed_signers_sha256": pin,
        "expected_main": "a" * 40,
        "expected_tree": "b" * 40,
    }
    verification = verify_offline_founder_ssh_signature(**args)
    assert verification["run_id"] == 101
    assert verification["real_attempt_claimed"] is False
    assert verification["scientific_execution_permitted_by_this_check_alone"] is False
    with pytest.raises(PermissionError):
        verify_offline_founder_ssh_signature(**{**args, "signature": signature + b"tamper"})
    with pytest.raises(PermissionError):
        verify_offline_founder_ssh_signature(
            **{**args, "expected_allowed_signers_sha256": "f" * 64}
        )
    with pytest.raises(ValueError):
        verify_offline_founder_ssh_signature(**{**args, "expected_main": "f" * 40})
