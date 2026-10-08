"""Gate B2 progression: immutable scientific authority / capacity denial checks.

No HTTP transport, FHIR patient loader, claim writer, model or dispatch imports.
A ChatGPT founder go-ahead authorizes work, not a cryptographically signed
single-run execution token. Every real scientific action is fail-closed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_b1 import lf_sha256, read_json
from gaxbench.study1_attempt3_b1_durable import verify_contract as verify_b1

PATH = "registry/study1_sg000031_attempt3_b2_readiness_contract.json"
BASE_MAIN = "1e2eb0970678ef86bcd25bb0a7a5f1b3dc1f7e6d"
BASE_TREE = "9e8e0a5ecb8d2b708f5a194c2eccd919f107b373"
B1_SHA = "70d257f0056d6d50d4a8a8eef6c53108124fff3ad17bd03765d42b7edbc2cb3a"
B1_DURABLE_SHA = "d46c5a36547b8bde4bd47fc16a0d067361ce35516386e22dd7403634f8481f79"
A2_CONSUMED_SHA = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
GIB = 1024**3


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def contract_at(root: Path) -> dict[str, Any]:
    return read_json(root, PATH)


def verify_readiness(root: Path, candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    prior = verify_b1(root)
    orig = read_json(root, "registry/study1_sg000031_attempt3_b1_contract.json")
    c = contract_at(root) if candidate is None else candidate
    require(
        set(c)
        == {
            "schema_version",
            "specgrain",
            "engineering_issue",
            "founder",
            "engineering_baseline",
            "frozen_predecessor",
            "frozen_science",
            "execution_authority",
            "capacity_preflight",
            "claim",
            "firewall",
            "next_action",
        },
        "B2 schema unauthorized fields",
    )
    require(
        (c["schema_version"], c["specgrain"], c["engineering_issue"])
        == ("dal-sg000031-a3-b2-readiness-unarmed-v1", "SG-000031-A3-B2-PREFLIGHT", 175),
        "B2 schema/issue drift",
    )
    require(
        c["founder"]
        == {
            "decision_issue": 171,
            "assistant_transcribed_chat_comment_id": 6069470401,
            "verbatim_reply": "i approve move on",
            "evidence_provenance": (
                "assistant_transcription_of_user_chat_not_founder_github_signature"
            ),
            "approval_scope": "PROGRESSION_AND_CONDITIONAL_ONE_SHOT_ENGINEERING",
        },
        "founder B2 provenance or scope misrepresented",
    )
    require(
        c["engineering_baseline"]
        == {
            "main_sha": BASE_MAIN,
            "tree_sha": BASE_TREE,
            "b1_pr": 174,
            "b1_issue": 173,
            "b1_receipt_comment_id": 6068669337,
            "b1_receipt_sha256": "12d870788ae059d0107b7442907a6006d8d5700b677fa62a2865f5c26005e7b7",
        },
        "B1 canonical engineering ancestry drift",
    )
    require(
        c["frozen_predecessor"]
        == {
            "b1_contract_path": "registry/study1_sg000031_attempt3_b1_contract.json",
            "b1_contract_sha256": B1_SHA,
            "b1_durable_path": "registry/study1_sg000031_attempt3_b1_durable_contract.json",
            "b1_durable_sha256": B1_DURABLE_SHA,
        },
        "B2 predecessor identity drift",
    )
    require(
        lf_sha256(root / c["frozen_predecessor"]["b1_contract_path"]) == B1_SHA
        and lf_sha256(root / c["frozen_predecessor"]["b1_durable_path"]) == B1_DURABLE_SHA,
        "canonical B1 predecessor bytes changed",
    )
    sf = orig["frozen_science"]
    require(
        c["frozen_science"]
        == {
            "r1_manifest_sha256": sf["r1_manifest_sha256"],
            "population_sha256": sf["population_sha256"],
            "producer_identity_sha256": sf["producer"]["producer_identity_sha256"],
            "development_rows": 1463,
            "calibration_rows": 341,
            "validation_rows": 1122,
            "shards": 8,
            "sealed_final_patients": 40,
            "sealed_final_rows": 173,
        },
        "scientific identity or population drift",
    )
    require(
        c["execution_authority"]
        == {
            "status": "CHAT_APPROVED_CONDITIONAL_SIGNED_TOKEN_ABSENT",
            "founder_signed_execution_authorization_sha256": None,
            "authenticated_github_founder_signature": None,
            "run_id": None,
            "canonical_execution_main_sha": None,
            "canonical_execution_tree_sha": None,
            "one_real_attempt_allowed": False,
            "git_ref_creation_allowed": False,
            "model_http_post_allowed": False,
            "scientific_workflow_dispatch_allowed": False,
        },
        "unsigned/invalid B2 authority must never arm science",
    )
    require(
        c["capacity_preflight"]
        == {
            "status": "UNQUALIFIED",
            "free_ram_floor_gib": 10,
            "free_disk_floor_gib": 8,
            "threshold_role": "conservative_diagnostic_floor_not_empirical_performance_proof",
            "host_device": "Abdulaziz",
            "hardware_observation_timestamp": "2026-10-09",
            "hardware_observed_ram_gib": 15.73,
            "hardware_observed_free_ram_gib": 2.58,
            "hardware_observed_free_disk_gib": 6.23,
            "host_snapshot_is_sufficient": False,
            "frozen_model_download_and_cpu_inference_qualified": False,
            "no_paid_providers": True,
        },
        "B2 runtime capacity incorrectly qualified",
    )
    require(
        c["claim"]
        == {
            "tag_ref": prior["durable_claim"]["ref"],
            "atomic_one_shot_required": True,
            "permanent_claim_existed_at_baseline": False,
            "consumed_prior_attempt2_authorization_sha256": A2_CONSUMED_SHA,
            "real_claim_created": False,
        },
        "B2 claim namespace or historic attempt consumption drift",
    )
    require(
        c["firewall"]
        == {
            "r2": "BLOCKED",
            "historic_exposed_pass": 224,
            "historic_exposed_blockers": 1239,
            "final": "SEALED",
            "scientific_row_replays": 0,
            "model_posts": 0,
            "permanent_scientific_claims": 0,
            "founder_cost_usd": 0,
            "no_training": True,
            "no_d4": True,
            "no_final_access": True,
        }
        and c["next_action"]
        == (
            "REQUIRE_CRYPTOGRAPHIC_FOUNDER_EXECUTION_TOKEN_AND_EMPIRICALLY_"
            "QUALIFIED_ZERO_COST_RUNTIME_BEFORE_ARMING"
        ),
        "B2 immutable science firewall or gate drift",
    )
    require(
        not (root / orig["claim_namespace"]["scientific_workflow"]).exists()
        and not (root / orig["claim_namespace"]["scientific_worker"]).exists(),
        "B2 cannot silently introduce scientific workflow or worker",
    )
    return c


def capacity_diagnostic(
    *,
    available_memory_bytes: int,
    available_disk_bytes: int,
    pinned_model_verified: bool = False,
    zero_paid_services: bool = True,
) -> dict[str, Any]:
    """Conservative floors are NOT proof of model ability; never return dispatchable."""
    require(
        type(available_memory_bytes) is int and available_memory_bytes >= 0,
        "invalid memory inventory",
    )
    require(
        type(available_disk_bytes) is int and available_disk_bytes >= 0, "invalid disk inventory"
    )
    ram_floor = 10 * GIB
    disk_floor = 8 * GIB
    ram_ok = available_memory_bytes >= ram_floor
    disk_ok = available_disk_bytes >= disk_floor
    return {
        "free_ram_bytes": available_memory_bytes,
        "free_disk_bytes": available_disk_bytes,
        "diagnostic_ram_floor_bytes": ram_floor,
        "diagnostic_disk_floor_bytes": disk_floor,
        "ram_floor_met": ram_ok,
        "disk_floor_met": disk_ok,
        "pinned_model_verified": pinned_model_verified,
        "zero_paid_services": zero_paid_services,
        "empirical_runtime_qualification": False,
        "scientific_dispatch_allowed": False,
        "status": "BLOCKED_MISSING_SIGNED_AUTHORITY_AND_EMPIRICAL_CAPACITY",
    }


class SignedExecutionGate:
    """No authority signer, HTTP client or GitHub mutation adapter exists in this grain."""

    def authorize(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("signed founder execution authority is absent")

    def claim(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("no real GitHub Attempt-3 claim before signed authority")

    def load_rows(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("sealed science execution forbidden before qualification")

    def send_model_post(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("model inference forbidden before qualification")

    def dispatch(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("science workflow dispatch forbidden before qualification")
