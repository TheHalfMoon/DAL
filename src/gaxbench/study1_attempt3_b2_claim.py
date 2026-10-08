"""Future GitHub two-step annotated-tag claim protocol: isolated synthetic qualification.

Real GitHub tag/ref operations and single-use scientific admission are DENIED.
The transport accepts ONLY an exact in-memory fake. This supplies a testable
protocol design for a distinct future signed/qualified production grain.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_b1 import lf_sha256, read_json
from gaxbench.study1_attempt3_b2_readiness import verify_readiness

PATH = "registry/study1_sg000031_attempt3_b2_claim_engineering_contract.json"
BASE_MAIN = "e460e766566d233c79b1270d6e425cb2005d9514"
BASE_TREE = "e109f0f963e787b94909dcabbdda61bda4bd06fd"
READINESS_SHA = "36ce48e0c5e5d9301fe9dd22d3a3268c1235bf817d2dd65d0763127a013064a1"
B1_SHA = "70d257f0056d6d50d4a8a8eef6c53108124fff3ad17bd03765d42b7edbc2cb3a"
DURABLE_SHA = "d46c5a36547b8bde4bd47fc16a0d067361ce35516386e22dd7403634f8481f79"
PREVIOUS_CONSUMED = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
REF = "refs/tags/dal-r2-issue166-attempt3"
TAG = "dal-r2-issue166-attempt3"
SYNTHETIC = "TEST_ONLY_NO_SCIENTIFIC_AUTHORITY"
MAIN_FILE = "registry/study1_sg000031_attempt3_b2_readiness_contract.json"
B1_FILE = "registry/study1_sg000031_attempt3_b1_contract.json"
DURABLE_FILE = "registry/study1_sg000031_attempt3_b1_durable_contract.json"


def exact(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def canonical(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def verify_plan(root: Path, candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    original = verify_readiness(root)
    c = read_json(root, PATH) if candidate is None else candidate
    exact(
        set(c)
        == {
            "schema_version",
            "specgrain",
            "issue",
            "engineering_baseline",
            "founder_decision",
            "protocol",
            "identity",
            "scope",
            "files",
            "next",
        },
        "atomic claim schema",
    )
    exact(
        (c["schema_version"], c["specgrain"], c["issue"])
        == (
            "dal-sg000031-a3-b2-atomic-claim-engineering-v1",
            "SG-000031-A3-B2-CLAIM-ENGINEERING",
            175,
        ),
        "atomic version/issue drift",
    )
    exact(
        c["engineering_baseline"]
        == {
            "main_sha": BASE_MAIN,
            "tree_sha": BASE_TREE,
            "pr": 176,
            "b2_readiness_sha256": READINESS_SHA,
            "b1_contract_sha256": B1_SHA,
            "b1_durable_sha256": DURABLE_SHA,
        },
        "prior canonical B2 identity drift",
    )
    exact(
        lf_sha256(root / MAIN_FILE) == READINESS_SHA
        and lf_sha256(root / B1_FILE) == B1_SHA
        and lf_sha256(root / DURABLE_FILE) == DURABLE_SHA,
        "source bytes drift",
    )
    exact(
        c["founder_decision"]
        == {
            "issue": 171,
            "comment_id": 6069470401,
            "source": "assistant_transcription_of_direct_chat_reply",
            "reply": "i approve move on",
            "scope": "B2_ENGINEERING_PROGRESSION_CONDITIONAL_ONLY",
            "signed_single_run_authority_sha256": None,
            "pinned_founder_public_key_sha256": None,
            "cryptographic_signature_verified": False,
        },
        "founder chat cannot impersonate signed real scientific authority",
    )
    exact(
        c["protocol"]
        == {
            "http_tag_create": "POST /repos/TheHalfMoon/DAL/git/tags",
            "http_ref_create": "POST /repos/TheHalfMoon/DAL/git/refs",
            "http_ref_read": "GET /repos/TheHalfMoon/DAL/git/ref/tags/dal-r2-issue166-attempt3",
            "ref": REF,
            "annotated_tag_name": TAG,
            "object_type": "commit",
            "create_ref_only": True,
            "no_ref_update": True,
            "no_ref_delete": True,
            "collision": "STOP_NO_RETRY",
            "orphan_tag": "NOT_CLAIMED_MUST_NOT_RETRY_WITHOUT_NEW_FOUNDER_DECISION",
            "tag_created_but_ref_missing": "NO_CONSUMPTION_PROOF_STOP",
            "ref_created": "CONSUMED_IMMEDIATELY_EVEN_WITH_ZERO_MODEL_POSTS",
        },
        "tag create/ref atomic policy drift",
    )
    frozen = original["frozen_science"]
    exact(
        c["identity"]
        == {
            "r1_sha256": frozen["r1_manifest_sha256"],
            "population_sha256": frozen["population_sha256"],
            "producer_sha256": frozen["producer_identity_sha256"],
            "development_rows": 1463,
            "calibration_rows": 341,
            "validation_rows": 1122,
            "shards": 8,
            "sealed_final_rows": 173,
            "attempt_ordinal": 3,
            "attempt2_authority_consumed_sha256": PREVIOUS_CONSUMED,
        },
        "frozen experimental identity drift",
    )
    exact(
        c["scope"]
        == {
            "real_github_transport_connected": False,
            "real_github_api_mutation_permitted": False,
            "real_claim_exists": False,
            "model_http_post_permitted": False,
            "scientific_workflow_available": False,
            "empirically_qualified_free_compute": False,
            "founder_cost_usd": 0,
            "training": False,
            "d4": False,
            "final_content_access": False,
            "science": "BLOCKED",
        },
        "B2 one-shot still NOT deployable",
    )
    exact(
        c["files"]
        == {
            "module": "src/gaxbench/study1_attempt3_b2_claim.py",
            "tests": "tests/test_study1_sg000031_attempt3_b2_claim.py",
            "qualifier": "tools/qualify_sg000031_attempt3_b2_claim.py",
            "workflow": ".github/workflows/study1-sg000031-attempt3-b2-claim.yml",
            "documentation": "docs/study1-sg000031-attempt3-b2-claim.md",
        }
        and c["next"]
        == (
            "COMPLETE_INDEPENDENT_SIGNED_ONE_SHOT_AUTHORITY_AND_VERIFIED_"
            "REAL_RUNTIME_BEFORE_ANY_CLAIM"
        ),
        "bounded unarmed file inventory drift",
    )
    return c


class RefConflict(Exception):
    """GitHub 422 equivalent. Never reattempt the same authorization."""


class SimulatedGitHubREST:
    """No actual network or credentials; model annotated tag object then atomic ref creation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.tag_objects: dict[str, dict[str, Any]] = {}
        self.references: dict[str, str] = {}
        # Ephemeral TEST fixture guard, not a substitute for a durable real run ledger.
        self.reserved_synthetic_signatures: set[str] = set()
        self.tag_posts = 0
        self.ref_posts = 0
        self.failed_ref_creations = 0
        self.fail_between_tag_and_ref = False

    def reserve_synthetic_signature(self, signature_digest: str) -> None:
        """Deny re-entry under the same test authority, including after an orphan tag."""
        with self._lock:
            if signature_digest in self.reserved_synthetic_signatures:
                raise PermissionError("synthetic authority already attempted; NO RETRY")
            self.reserved_synthetic_signatures.add(signature_digest)

    def post_tag(self, payload: dict[str, Any]) -> str:
        if set(payload) != {"tag", "message", "object", "type", "tagger"}:
            raise ValueError("annotated-tag API schema mismatch")
        if payload["tag"] != TAG or payload["type"] != "commit":
            raise ValueError("wrong attempt tag/target type")
        if not re.fullmatch("[0-9a-f]{40}", payload["object"]):
            raise ValueError("GitHub commit SHA invalid")
        with self._lock:
            self.tag_posts += 1
            # SHA1 is a synthetic Git object identity in this fake ONLY.
            sha = hashlib.sha1(canonical(payload)).hexdigest()
            self.tag_objects[sha] = payload
        return sha

    def post_ref(self, ref: str, sha: str) -> None:
        if ref != REF:
            raise ValueError("unauthorized real attempt namespace")
        with self._lock:
            self.ref_posts += 1
            if self.fail_between_tag_and_ref:
                self.failed_ref_creations += 1
                raise OSError("synthetic failure between tag and ref")
            if ref in self.references:
                self.failed_ref_creations += 1
                raise RefConflict("422: existing permanent ref")
            if sha not in self.tag_objects:
                raise ValueError("unrecognized annotated tag object")
            self.references[ref] = sha

    def get_ref(self, ref: str) -> str | None:
        with self._lock:
            return self.references.get(ref)

    def patch_ref(self, *_args: object) -> None:
        raise PermissionError("no ref mutation")

    def delete_ref(self, *_args: object) -> None:
        raise PermissionError("no ref deletion")


@dataclass(frozen=True)
class SyntheticAuthority:
    """Test-only input. NEVER cryptographic proof of founder approval."""

    commit_sha: str
    tree_sha: str
    run_id: int
    signature_digest: str
    marker: str = SYNTHETIC

    def envelope(self) -> dict[str, Any]:
        return {
            "schema": "dal-a3-b2-claim-test-only-v1",
            "attempt": 3,
            "commit_sha": self.commit_sha,
            "tree_sha": self.tree_sha,
            "run_id": self.run_id,
            "signature_digest": self.signature_digest,
            "marker": self.marker,
            "scientific_execution": False,
            "scientific_rows": 0,
            "model_posts": 0,
            "founder_cost_usd": 0,
        }


class ClaimProtocolSimulator:
    def __init__(self, github: SimulatedGitHubREST) -> None:
        if type(github) is not SimulatedGitHubREST:
            raise PermissionError("real HTTP client forbidden in B2 claim engineering")
        self.github = github

    def try_claim_synthetic(self, auth: SyntheticAuthority) -> str:
        if type(auth) is not SyntheticAuthority or (
            auth.marker != SYNTHETIC
            or not re.fullmatch("[0-9a-f]{40}", auth.commit_sha)
            or not re.fullmatch("[0-9a-f]{40}", auth.tree_sha)
            or auth.commit_sha == BASE_MAIN
            or type(auth.run_id) is not int
            or auth.run_id <= 0
            or not re.fullmatch("[0-9a-f]{64}", auth.signature_digest)
            or auth.signature_digest == PREVIOUS_CONSUMED
        ):
            raise PermissionError("signed founder scientific authority NOT established")
        # SHA256 binds all synthetic claim identity before any POST occurs.
        claim_message = (
            "DAL_SYNTHETIC_B2_NO_SCIENCE_SHA256="
            + hashlib.sha256(canonical(auth.envelope())).hexdigest()
        )
        tag = {
            "tag": TAG,
            "message": claim_message,
            "object": auth.commit_sha,
            "type": "commit",
            "tagger": {
                "name": "Synthetic DAL fixture",
                "email": "invalid@example.invalid",
                "date": "2000-01-01T00:00:00Z",
            },
        }
        if self.github.get_ref(REF) is not None:
            raise PermissionError("consumed, duplicate run forbidden")
        # This models a pre-mutation reservation within one fake process ONLY.
        # Real crash-safe reservation must be independently durable and reviewed.
        self.github.reserve_synthetic_signature(auth.signature_digest)
        tag_sha = self.github.post_tag(tag)
        try:
            self.github.post_ref(REF, tag_sha)
        except (OSError, RefConflict) as error:
            raise PermissionError(
                "claim collision/orphan uncertain; STOP permanently, NO AUTO RETRY"
            ) from error
        if self.github.get_ref(REF) != tag_sha:
            raise PermissionError("claim identity not verifiable; STOP")
        return tag_sha

    def verify_synthetic(self, expected_tag_sha: str) -> bool:
        return bool(re.fullmatch("[0-9a-f]{40}", expected_tag_sha)) and (
            self.github.get_ref(REF) == expected_tag_sha
        )

    def claim_real(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("no signed founder authority or production claim transport")

    def replay(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("no row replay or model access")

    def dispatch(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("scientific Attempt-3 dispatch not qualified")


def rehearsal(root: Path) -> dict[str, Any]:
    verify_plan(root)
    svc = SimulatedGitHubREST()
    design = ClaimProtocolSimulator(svc)
    permit = SyntheticAuthority("a" * 40, "b" * 40, 101, "c" * 64)
    tag = design.try_claim_synthetic(permit)
    try:
        design.try_claim_synthetic(permit)
    except PermissionError:
        denied = True
    else:
        raise AssertionError("duplicate accepted")
    return {
        "schema_version": "dal-sg000031-b2-atomic-protocol-rehearsal-v1",
        "readiness_source_sha256": READINESS_SHA,
        "contract_sha256": lf_sha256(root / PATH),
        "synthetic_tag": tag,
        "synthetic_claim_consumed_once": svc.ref_posts == 1,
        "duplicate_denied": denied,
        "simulated_tag_posts": svc.tag_posts,
        "real_api_calls": 0,
        "real_github_mutations": 0,
        "model_posts": 0,
        "rows_replayed": 0,
        "signed_execution_token": None,
        "science": "BLOCKED",
        "final_content_access": False,
        "founder_cost_usd": 0,
    }


# Offline verification only; this cannot sign a founder token or dispatch a workflow.
FOUNDER_SSH_NAMESPACE = "dal-sg000031-attempt3-b2"
FOUNDER_SSH_IDENTITY = "dal-founder"


def execution_authorization_bytes(
    authorization: dict[str, Any],
    *,
    expected_main: str,
    expected_tree: str,
) -> bytes:
    """Validate one-run frozen scientific scope before any external signature check."""
    if not re.fullmatch(r"[0-9a-f]{40}", expected_main) or not re.fullmatch(
        r"[0-9a-f]{40}", expected_tree
    ):
        raise ValueError("trusted current main and tree must be explicit SHA-1 identities")
    required = {
        "schema_version",
        "attempt_ordinal",
        "main_sha",
        "tree_sha",
        "run_id",
        "run_attempt",
        "ref",
        "population_sha256",
        "r1_manifest_sha256",
        "development_rows",
        "shards",
        "final_role_access",
        "training",
        "d4_activation",
        "founder_cost_usd",
        "retry_permitted",
        "scientific_role",
        "single_use",
    }
    if set(authorization) != required:
        raise ValueError("execution authority cannot add or omit scientific permissions")
    fixed = {
        "schema_version": "dal-sg000031-a3-b2-founder-execution-v1",
        "attempt_ordinal": 3,
        "main_sha": expected_main,
        "tree_sha": expected_tree,
        "run_attempt": 1,
        "ref": REF,
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
    if any(
        type(authorization[key]) is not type(value) or authorization[key] != value
        for key, value in fixed.items()
    ):
        raise ValueError("signed scientific authority scope/identity drift")
    if type(authorization["run_id"]) is not int or authorization["run_id"] <= 0:
        raise ValueError("unique run id must be a real positive integer")
    return canonical(authorization)


def verify_offline_founder_ssh_signature(
    *,
    authorization: dict[str, Any],
    signature: bytes,
    allowed_signers: bytes,
    expected_allowed_signers_sha256: str | None,
    expected_main: str,
    expected_tree: str,
) -> dict[str, Any]:
    """Verify a pinned SSHSIG offline; no unsigned fallback, network or GitHub writes.

    The caller MUST obtain the trusted allowlist SHA256 through independent
    founder governance, not from this payload, an agent-written issue, or test key.
    No such trusted production digest is available in the B2 engineering grain.
    """
    import hmac
    import shutil
    import subprocess
    import tempfile

    content = execution_authorization_bytes(
        authorization, expected_main=expected_main, expected_tree=expected_tree
    )
    if not isinstance(expected_allowed_signers_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_allowed_signers_sha256
    ):
        raise PermissionError("independently pinned founder allowlist digest ABSENT")
    if (
        not isinstance(allowed_signers, bytes)
        or not isinstance(signature, bytes)
        or len(allowed_signers) > 4096
        or len(signature) > 8192
        or not signature.startswith(b"-----BEGIN SSH SIGNATURE-----")
    ):
        raise PermissionError("founder signature format or allowed signer list invalid")
    actual = hashlib.sha256(allowed_signers).hexdigest()
    if not hmac.compare_digest(actual, expected_allowed_signers_sha256):
        raise PermissionError("allowed signers do not match independent founder trust pin")
    lines = allowed_signers.decode("ascii", errors="strict").splitlines()
    if len(lines) != 1 or not lines[0].startswith(
        f'{FOUNDER_SSH_IDENTITY} namespaces="{FOUNDER_SSH_NAMESPACE}" ssh-ed25519 '
    ):
        raise PermissionError("only the pinned founder Ed25519/SSH namespace is accepted")
    ssh_keygen = shutil.which("ssh-keygen")
    if not ssh_keygen:
        raise PermissionError("OpenSSH verifier unavailable; no execution allowed")
    with tempfile.TemporaryDirectory(prefix="dal-a3-b2-sigcheck-") as workdir:
        signers = Path(workdir) / "allowed_signers"
        sigfile = Path(workdir) / "signature"
        signers.write_bytes(allowed_signers)
        sigfile.write_bytes(signature)
        try:
            check = subprocess.run(
                [
                    ssh_keygen,
                    "-Y",
                    "verify",
                    "-f",
                    str(signers),
                    "-I",
                    FOUNDER_SSH_IDENTITY,
                    "-n",
                    FOUNDER_SSH_NAMESPACE,
                    "-s",
                    str(sigfile),
                ],
                input=content,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PermissionError(
                "independent founder signature verification unavailable"
            ) from error
    if check.returncode != 0:
        raise PermissionError("founder SSH signature verification FAILED")
    return {
        "cryptographic_verification": "PASS_ONLY_FOR_SUPPLIED_INDEPENDENT_TRUST_PIN",
        "identity": FOUNDER_SSH_IDENTITY,
        "namespace": FOUNDER_SSH_NAMESPACE,
        "main_sha": expected_main,
        "tree_sha": expected_tree,
        "run_id": authorization["run_id"],
        "authority_sha256": hashlib.sha256(content).hexdigest(),
        "signature_sha256": hashlib.sha256(signature).hexdigest(),
        "trusted_allowlist_sha256": actual,
        "real_attempt_claimed": False,
        "model_posts": 0,
        "founder_cost_usd": 0,
        "scientific_execution_permitted_by_this_check_alone": False,
    }
