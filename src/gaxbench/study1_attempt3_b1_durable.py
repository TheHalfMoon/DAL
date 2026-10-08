"""Attempt-3 durable claim DESIGN and count-only worker, exclusively simulated.

This module has no GitHub HTTP adapter, no credentials, no model client, no row
reader, and no scientific workflow. The atomic GitHub ref-create semantics are
tested against an isolated, thread-safe, *in-memory* fake. A real adapter must
never be wired in without a distinct founder Gate B2 approval and qualification.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_b1 import (
    check_policy,
    lf_sha256,
    load_contract,
    partition_denominator,
    read_json,
)

PATH = "registry/study1_sg000031_attempt3_b1_durable_contract.json"
SOURCE_SHA = "70d257f0056d6d50d4a8a8eef6c53108124fff3ad17bd03765d42b7edbc2cb3a"
SDK_SHA = "c2fbcecab00f957a49c59af38875de095cfbf9e9176e06293ab5840838bbab1e"
A2_CONSUMED_SHA = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
MARKER = "SYNTHETIC_TEST_FIXTURE_NOT_VALID_FOR_SCIENCE"
CLAIM_REF = "refs/tags/dal-r2-issue166-attempt3"
MAIN_BASE = "eee686d05332ed5fad93a52c75ca50dbee9cb877"
TREE_BASE = "c3df431eff7b81218e6bae91ff797446bb6a860e"


def reject_if_not(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def canonical(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def verify_contract(root: Path, candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    baseline = load_contract(root)
    verified = check_policy(root, baseline)
    c = read_json(root, PATH) if candidate is None else candidate
    reject_if_not(
        set(c)
        == {
            "schema_version",
            "specgrain",
            "authorized_issue",
            "founder_gate",
            "base",
            "frozen_predecessor",
            "producer",
            "durable_claim",
            "authority",
            "runtime",
            "transport",
            "paths",
            "safety",
            "next_gate",
        },
        "durable schema changed",
    )
    reject_if_not(
        (c["schema_version"], c["specgrain"], c["authorized_issue"])
        == ("dal-sg000031-attempt3-b1-durable-design-v1", "SG-000031-A3-B1-DURABLE", 173),
        "durable version or issue drift",
    )
    reject_if_not(
        c["founder_gate"]
        == {
            "issue": 171,
            "assistant_transcribed_comment": 6066751157,
            "scope": "ENGINEERING_ONLY_UNARMED",
        },
        "founder scope drift",
    )
    reject_if_not(
        c["base"] == {"main": MAIN_BASE, "tree": TREE_BASE, "pr": 172},
        "independent durable engineering baseline changed",
    )
    fp = c["frozen_predecessor"]
    reject_if_not(
        fp
        == {
            "path": "registry/study1_sg000031_attempt3_b1_contract.json",
            "sha256": SOURCE_SHA,
            "sdk_path": "registry/study1_sg000031_sdk_qualification.json",
            "sdk_sha256": SDK_SHA,
        },
        "historical source evidence references changed",
    )
    reject_if_not(
        lf_sha256(root / fp["path"]) == SOURCE_SHA and lf_sha256(root / fp["sdk_path"]) == SDK_SHA,
        "protected predecessor/source checksum drift",
    )
    sdk = read_json(root, fp["sdk_path"])
    reject_if_not(
        c["producer"]
        == {
            "system_prompt_sha256": sdk["system_prompt_sha256"],
            "tool_schema_sha256": sdk["tool_schema_sha256"],
        }
        and sdk["state"] == "PASS"
        and sdk["model_inference_performed"] is False
        and sdk["synthetic_HTTP_server_only"] is True,
        "frozen prompt/tool schema or synthetic SDK identity drift",
    )
    reject_if_not(
        c["durable_claim"]
        == {
            "method": "POST /repos/TheHalfMoon/DAL/git/refs",
            "ref": CLAIM_REF,
            "create_only": True,
            "existing_ref_conflict": "CONSUMED_STOP_NO_RETRY",
            "atomic_create_ref": True,
            "no_delete": True,
            "no_update": True,
            "bind_to": "unique SHA256 of canonical JSON envelope",
            "simulate_with": "InMemoryGitHubRefService only",
            "real_mutation_allowed": False,
        },
        "durable claim policy drift",
    )
    reject_if_not(
        c["authority"]
        == {
            "scientific_gate": "B2",
            "authorization_sha256": None,
            "approval_record": None,
            "live_run_id": None,
            "main_sha": None,
            "main_tree": None,
            "verified_signature": False,
            "real_dispatch_permitted": False,
        },
        "scientific execution authorization must remain absent",
    )
    reject_if_not(
        c["runtime"]
        == {
            "shards": 8,
            "rows": 1463,
            "calibration_rows": 341,
            "validation_rows": 1122,
            "first_turn_limit_per_row": 1,
            "model_retry": 0,
            "workflow_retry": 0,
            "secondary_reasoning": False,
            "selection_or_scoring": False,
            "persistent_row_write": False,
            "scoring_correctness": False,
            "final_access": False,
        },
        "science budget/worker identity drift",
    )
    reject_if_not(
        c["transport"]
        == {
            "model_id": baseline["frozen_science"]["producer"]["model_id"],
            "url_policy": "loopback_only_when_future_B2",
            "http_post_allowed": False,
            "network_client_available": False,
            "api_credentials_allowed": False,
        },
        "transport unexpectedly armed",
    )
    reject_if_not(
        c["paths"]
        == {
            "blueprint": "docs/study1-sg000031-attempt3-b1-durable.md",
            "module": "src/gaxbench/study1_attempt3_b1_durable.py",
            "test": "tests/test_study1_sg000031_attempt3_b1_durable.py",
            "qualifier": "tools/qualify_sg000031_attempt3_b1.py",
        },
        "B1 runtime file inventory changed",
    )
    reject_if_not(
        c["safety"]
        == {
            "science_state": "BLOCKED",
            "sealed_final": "SEALED",
            "historical_outcomes": "EXPOSED_DEV_NOT_BLIND",
            "physical_model_posts": 0,
            "rows_replayed": 0,
            "permanent_scientific_claim": False,
            "founder_cost_usd": 0,
        }
        and c["next_gate"] == "EXPLICIT_FOUNDER_B2_REQUIRED_AFTER_B1_CANONICAL",
        "B1 firewall changed",
    )
    reject_if_not(
        baseline["claim_namespace"]["permanent_tag"] == CLAIM_REF
        and baseline["history"]["attempt2_authorization_sha256"] == A2_CONSUMED_SHA
        and verified["protected_files_verified"] == 43,
        "Attempt3 namespace or historical consumed approval changed",
    )
    reject_if_not(
        not (root / baseline["claim_namespace"]["scientific_workflow"]).exists()
        and not (root / baseline["claim_namespace"]["scientific_worker"]).exists(),
        "no scientific execution workflow permitted",
    )
    return c


class SimulatedConflict(Exception):
    """Equivalent to GitHub 422 ref-already-exists; never retried."""


class InMemoryGitHubRefService:
    """Thread-safe test double of atomic POST git/refs; NEVER talks to GitHub."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._refs: dict[str, tuple[str, bytes]] = {}
        self.attempts = 0
        self.accepted = 0

    def create_ref_only(self, ref: str, tag_object_sha: str, envelope_bytes: bytes) -> None:
        if ref != CLAIM_REF or not re.fullmatch(r"[0-9a-f]{40}", tag_object_sha):
            raise ValueError("attempt ref/tag object identity drift")
        with self._lock:
            self.attempts += 1
            if ref in self._refs:
                raise SimulatedConflict("already consumed; NO RETRY")
            self._refs[ref] = (tag_object_sha, envelope_bytes)
            self.accepted += 1

    def read_ref(self, ref: str) -> tuple[str, bytes] | None:
        with self._lock:
            return self._refs.get(ref)

    def update_ref(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("update denied; claim immutable")

    def delete_ref(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("delete denied; claim immutable")


@dataclass(frozen=True)
class SimulatedB2Envelope:
    """Unsigned, synthetic-only test fixture. Never acceptable as founder consent."""

    base_main: str
    base_tree: str
    run_id: int
    authorization_sha256: str
    fixture_marker: str = MARKER

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "dal-attempt3-b2-prospective-claim-simulation-v1",
            "attempt": 3,
            "main_sha": self.base_main,
            "main_tree": self.base_tree,
            "run_id": self.run_id,
            "authorization_sha256": self.authorization_sha256,
            "fixture_marker": self.fixture_marker,
            "scientific_execution_authorized": False,
            "development_rows": 1463,
            "shards": 8,
            "permanent_tag": CLAIM_REF,
            "founder_cost_usd": 0,
        }


class UnarmedDurableClaimDesign:
    """GitHub-like atomic create-only ref algorithm, fake adapter mandatory."""

    def __init__(self, service: InMemoryGitHubRefService) -> None:
        if type(service) is not InMemoryGitHubRefService:
            raise PermissionError("real GitHub writer forbidden under Gate B1")
        self._service = service

    def claim_synthetic(self, envelope: SimulatedB2Envelope) -> str:
        if type(envelope) is not SimulatedB2Envelope:
            raise PermissionError("only simulated B2 fixtures permitted")
        if (
            envelope.fixture_marker != MARKER
            or not re.fullmatch(r"[0-9a-f]{40}", envelope.base_main)
            or not re.fullmatch(r"[0-9a-f]{40}", envelope.base_tree)
            or envelope.base_main == MAIN_BASE
            or type(envelope.run_id) is not int
            or envelope.run_id <= 0
            or not re.fullmatch(r"[0-9a-f]{64}", envelope.authorization_sha256)
            or envelope.authorization_sha256 == A2_CONSUMED_SHA
        ):
            raise PermissionError("synthetic test fixture invalid; never valid science consent")
        encoded = canonical(envelope.as_dict())
        fake_annotated_tag_sha = hashlib.sha1(encoded).hexdigest()
        try:
            self._service.create_ref_only(CLAIM_REF, fake_annotated_tag_sha, encoded)
        except SimulatedConflict as exc:
            raise PermissionError("attempt already consumed; no retries") from exc
        # Successful ref creation is immediately consumed, even before any model.
        return hashlib.sha256(encoded).hexdigest()

    def verify_synthetic(self, expected_digest: str) -> bool:
        claim = self._service.read_ref(CLAIM_REF)
        if claim is None:
            return False
        tag, raw = claim
        return (
            re.fullmatch(r"[0-9a-f]{64}", expected_digest) is not None
            and hashlib.sha1(raw).hexdigest() == tag
            and hashlib.sha256(raw).hexdigest() == expected_digest
        )

    def claim_real(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("real permanent GitHub claim requires separate Gate B2")


class UnarmedWorkerBlueprint:
    """Connected frozen shape, but cannot read patient data or send any HTTP."""

    def __init__(self, root: Path) -> None:
        self._contract = verify_contract(root)

    def shard_counts(self) -> tuple[int, ...]:
        limits = self._contract["runtime"]
        return tuple(
            part.number_of_rows for part in partition_denominator(limits["rows"], limits["shards"])
        )

    def rehearse_after_claim(
        self, design: UnarmedDurableClaimDesign, receipt_digest: str
    ) -> dict[str, Any]:
        if not design.verify_synthetic(receipt_digest):
            raise PermissionError("no valid synthetic claim/tag identity")
        counts = self.shard_counts()
        if sum(counts) != 1463 or len(counts) != 8:
            raise PermissionError("invalid frozen development-row coverage")
        return {
            "scientific_dispatches": 0,
            "model_posts": 0,
            "rows_read": 0,
            "final_content_access": False,
            "science_enabled": False,
            "shard_counts": list(counts),
            "r2": "BLOCKED",
        }

    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Gate B2 required before worker execution")

    def send_model_http(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Gate B2 required before any POST")

    def replay_rows(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Gate B2 required before row replay")

    def access_final(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("sealed final role cannot be accessed")


def synthetic_durable_rehearsal(root: Path) -> dict[str, Any]:
    c = verify_contract(root)
    fake = InMemoryGitHubRefService()
    design = UnarmedDurableClaimDesign(fake)
    fixture = SimulatedB2Envelope(
        base_main="a" * 40, base_tree="b" * 40, run_id=1, authorization_sha256="c" * 64
    )
    claim_digest = design.claim_synthetic(fixture)
    counts = UnarmedWorkerBlueprint(root).rehearse_after_claim(design, claim_digest)
    try:
        design.claim_synthetic(fixture)
    except PermissionError:
        denied = True
    else:
        raise AssertionError("fake GitHub tag may never be claimed twice")
    return {
        "schema": "dal-attempt3-b1-durable-synthetic-proof-v1",
        "contract_sha256": lf_sha256(root / PATH),
        "b1_predecessor_sha256": SOURCE_SHA,
        "simulated_github_tag": CLAIM_REF,
        "simulated_ref_created_once": fake.accepted == 1,
        "simulated_duplicate_denied": denied,
        "simulated_claim_receipt_sha256": claim_digest,
        "simulated_run": counts,
        "real_github_mutations": 0,
        "model_posts": 0,
        "rows_replayed": 0,
        "permanent_scientific_claim": False,
        "B2_authorized": False,
        "r2": c["safety"]["science_state"],
        "founder_cost_usd": 0,
    }
