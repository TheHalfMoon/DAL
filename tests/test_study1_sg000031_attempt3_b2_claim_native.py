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
) -> None:
    monkeypatch.setattr(gate.b1_qual, "check_environment", lambda: "pull_request")

    def forbidden_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("native qualifier must not access the network here")

    monkeypatch.setattr(socket.socket, "connect", forbidden_network)
    assert not (ROOT / ".github/workflows/study1-sg000031-attempt3-b2-claim.yml").exists()
    with pytest.raises(FileNotFoundError):
        gate.qualify(ROOT)
