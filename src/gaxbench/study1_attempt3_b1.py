"""Scientific-capable Attempt-3 B1 structures, deliberately UNARMED.

Never imports model clients, networking, scientific row loaders, GitHub mutation or
ledger writers. This is a strictly synthetic engineering rehearsal surface.
Gate B2 must separately authorize and implement any real science execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_admission import (
    check_contract as check_a3_contract,
)
from gaxbench.study1_attempt3_admission import (
    load_contract as load_a3_contract,
)

CONTRACT_PATH = "registry/study1_sg000031_attempt3_b1_contract.json"
SCHEMA = "dal-sg000031-attempt3-b1-scientific-capability-unarmed-v1"
B1_BASE = "b2acddbc5a74962124555f87e679c2ca7cecb277"
B1_TREE = "2513e4f8f48c5f3654850fdb60c1b88625549a73"
B1_COMMENT = 6066751157
A2_AUTH_SHA = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
R1_SHA = "220c676df241d8dc1ac8ccd83e81d54554e7618fc5acf016eaa32ec6302ca2b0"
POPULATION_SHA = "0755fcb62129037e05557d73863574b399503458b48b2c5a906546575aa1679f"
EXPECTED_NEXT_GATE = "B2_INDEPENDENT_FOUNDER_SCIENTIFIC_EXECUTION_APPROVAL_REQUIRED"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read_json(root: Path, relative: str) -> dict[str, Any]:
    target = root / relative
    require(target.is_file() and not target.is_symlink(), "missing/linked evidence: " + relative)
    result = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("malformed evidence object: " + relative)
    return result


def lf_sha256(source: Path) -> str:
    require(source.is_file() and not source.is_symlink(), "protected evidence absent")
    return hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_contract(root: Path) -> dict[str, Any]:
    return read_json(root, CONTRACT_PATH)


def check_policy(root: Path, b1: dict[str, Any]) -> dict[str, Any]:
    """Fail closed on any science-changing identity, authorization or capability."""
    require(
        set(b1)
        == {
            "schema_version",
            "specgrain_id",
            "attempt_ordinal",
            "engineering_authorization",
            "authorized_base",
            "predecessor_contracts",
            "execution_authorization",
            "frozen_science",
            "history",
            "claim_namespace",
            "execution_shape",
            "engineering_gate",
            "science_firewall",
            "next_gate",
        },
        "B1 top-level schema invalid",
    )
    require(
        b1["schema_version"] == SCHEMA
        and b1["specgrain_id"] == "SG-000031-A3-B1"
        and type(b1["attempt_ordinal"]) is int
        and b1["attempt_ordinal"] == 3,
        "Attempt-3 B1 schema/ordinal invalid",
    )
    require(
        b1["engineering_authorization"]
        == {
            "issue": 171,
            "assistant_transcribed_comment_id": B1_COMMENT,
            "scope": "B1_SCIENCE_CAPABLE_ENGINEERING_UNARMED",
            "original_founder_github_comment": False,
        },
        "Gate B1 authorization provenance mismatch",
    )
    require(
        b1["authorized_base"]
        == {
            "sha": B1_BASE,
            "tree": B1_TREE,
            "issue168_closeout_comment": 6063077432,
            "issue168_canonical_receipt_sha256": (
                "a9600b2431fc87071e651c9c96c689c949d838e78d2fbecd656efd81f581414e"
            ),
        },
        "B1 exact engineering baseline drift",
    )
    require(
        b1["predecessor_contracts"]
        == [
            "registry/study1_sg000031_attempt2_admission_contract.json",
            "registry/study1_sg000031_attempt3_readiness_contract.json",
            "registry/study1_sg000031_attempt3_admission_contract.json",
        ],
        "B1 predecessor contracts drift",
    )
    require(
        b1["execution_authorization"]
        == {
            "status": "NOT_AUTHORIZED",
            "sha256": None,
            "approved_scientific_execution_issue": None,
            "single_run_token": None,
            "science_dispatch_permitted": False,
            "model_http_post_permitted": False,
            "development_row_replay_permitted": False,
            "permanent_claim_permitted": False,
        },
        "Gate B2 scientific authorization remains ABSENT",
    )
    a2 = read_json(root, b1["predecessor_contracts"][0])
    ready = read_json(root, b1["predecessor_contracts"][1])
    a3 = load_a3_contract(root)
    prior = check_a3_contract(root, a3)
    require(
        prior["protected_files"] == 43 and prior["unarmed"] is True,
        "prior A3 engineering qualification weakened",
    )
    require(
        ready["execution_authorization"]
        == {
            "status": "NOT_AUTHORIZED",
            "sha256": None,
            "dispatch_permitted": False,
            "claim_permitted": False,
        },
        "Attempt-3 readiness authorization unexpectedly armed",
    )
    freeze = b1["frozen_science"]
    require(
        set(freeze)
        == {
            "r1_manifest_sha256",
            "population_sha256",
            "development_rows",
            "calibration_rows",
            "validation_rows",
            "sealed_final_patients",
            "sealed_final_rows",
            "producer",
        },
        "B1 frozen science schema changed",
    )
    require(
        freeze["r1_manifest_sha256"] == R1_SHA
        and a2["canonical_r1"]["manifest_sha256"] == R1_SHA
        and lf_sha256(root / "registry/study1_sg000030_r1_manifest.json") == R1_SHA,
        "R1 manifest freeze mismatch",
    )
    require(
        freeze["population_sha256"] == POPULATION_SHA
        and a2["development"]["question_role_assignments_sha256"] == POPULATION_SHA,
        "frozen row membership identity mismatch",
    )
    require(
        (freeze["development_rows"], freeze["calibration_rows"], freeze["validation_rows"])
        == (1463, 341, 1122),
        "frozen development denominator changed",
    )
    require(
        (freeze["sealed_final_patients"], freeze["sealed_final_rows"]) == (40, 173),
        "sealed final counts changed",
    )
    p = a2["producer"]
    expected_producer = {
        "model_id": p["base_model"],
        "model_revision": p["base_model_revision"],
        "tokenizer_revision": p["tokenizer_revision"],
        "gguf_repository": p["quantized_repo"],
        "gguf_revision": p["quantized_repo_revision"],
        "gguf_filename": p["quantized_file"],
        "gguf_sha256": p["quantized_sha256"],
        "llama_cpp_revision": p["llama_cpp_revision"],
        "fhir_agentbench_revision": p["fhir_agentbench_revision"],
        "patched_core_utils_sha256": p["patched_core_utils_sha256"],
        "transport_patch_sha256": p["transport_patch_sha256"],
        "strategy": p["agent_strategy"],
        "temperature": p["temperature"],
        "agent_context_tokens": p["context_tokens"],
        "producer_identity_sha256": a2["producer_identity_sha256"],
    }
    require(
        freeze["producer"] == expected_producer,
        "frozen model/tokenizer/transport/prompt-tool producer drift",
    )
    require(
        b1["history"]
        == {
            "attempt1_run": 37320473498,
            "attempt2_run": 37653806159,
            "attempt2_authorization_sha256": A2_AUTH_SHA,
            "attempt1_state": "INFRASTRUCTURE_FAILURE_CONSUMED",
            "attempt2_state": "INFRASTRUCTURE_FAILURE_CONSUMED",
            "attempt1_physical_posts": 0,
            "attempt2_physical_posts": 0,
            "exposed_development_historical_PASS": 224,
            "exposed_development_historical_blockers": 1239,
        }
        and a2["execution_authorization_sha256"] == A2_AUTH_SHA,
        "historical failure or consumed attempt authorization drift",
    )
    # Compare explicitly, rather than ever copying the old Attempt-2 namespace.
    ns = a3["reserved_scientific_namespace"]
    require(
        b1["claim_namespace"]
        == {
            "permanent_tag": ns["permanent_ref"],
            "ledger_branch": ns["ledger_branch"],
            "ledger_root": ns["ledger_root"],
            "scientific_workflow": ns["scientific_workflow"],
            "scientific_worker": ns["worker"],
            "scientific_receipt_marker": ns["receipt_marker"],
        },
        "unique Attempt-3 claims/worker namespace drift",
    )
    require(
        b1["execution_shape"]
        == {
            "shards": 8,
            "first_turn_generations_per_row": 1,
            "maximum_first_turn_generations": 1463,
            "automatic_retries": 0,
            "second_turn_reasoning": False,
            "answer_correctness_scoring": False,
            "selective_row_omission": False,
            "final_role_access": False,
            "d4": False,
            "training": False,
            "fine_tuning": False,
            "model_switching": False,
            "founder_cost_usd": 0,
            "claim_consumption": "ATOMIC_SINGLE_USE_EVEN_IF_PRE_MODEL_FAILURE",
        },
        "one-shot execution budget or science firewall changed",
    )
    require(
        b1["engineering_gate"]
        == {
            "controller": "tools/study1_sg000031_attempt3_b1.py",
            "worker": "src/gaxbench/study1_attempt3_b1.py",
            "native_qualifier": "tools/qualify_sg000031_attempt3_b1.py",
            "workflow": ".github/workflows/study1-sg000031-attempt3-b1.yml",
            "workflow_dispatch_created": False,
            "scientific_worker_workflow_created": False,
            "credentialed_transport_created": False,
            "raw_row_loader_created": False,
            "production_claim_writer_created": False,
            "production_http_client_created": False,
            "admission_mode": "SYNTHETIC_REHEARSAL_ONLY",
        },
        "B1 engineering admission unexpectedly armed",
    )
    require(
        b1["science_firewall"]
        == {
            "r2": "BLOCKED",
            "scientific_execution_authorized": False,
            "model_posts": 0,
            "rows_replayed": 0,
            "permanent_claim_created": False,
            "final_role": "SEALED",
            "final_rows_materialized": 0,
            "final_content_access": False,
            "d4": False,
            "training": False,
            "founder_cost_usd": 0,
        }
        and b1["next_gate"] == EXPECTED_NEXT_GATE,
        "R2 science firewall or B2 founder gate weakened",
    )
    require(
        not (root / ns["scientific_workflow"]).exists() and not (root / ns["worker"]).exists(),
        "actual Attempt-3 science workflow/worker forbidden before Gate B2",
    )
    workflow = (root / b1["engineering_gate"]["workflow"]).read_text(encoding="utf-8")
    require(
        all(
            token in workflow
            for token in (
                "pull_request:",
                "push:",
                "fetch-depth: 0",
                "persist-credentials: false",
                "qualify_sg000031_attempt3_b1.py",
            )
        )
        and not any(
            token in workflow
            for token in (
                "workflow_dispatch:",
                "workflow_call:",
                "repository_dispatch:",
                "schedule:",
                "contents: write",
            )
        ),
        "B1 CI must remain read-only and untriggerable for scientific execution",
    )
    return {
        "protected_files_verified": 43,
        "unarmed": True,
        "contract_sha256": lf_sha256(root / CONTRACT_PATH),
        "producer_identity_sha256": p["producer_identity_sha256"]
        if "producer_identity_sha256" in p
        else a2["producer_identity_sha256"],
    }


class ClaimState(Enum):
    UNUSED = "UNUSED"
    CONSUMED = "CONSUMED"


@dataclass
class SyntheticSingleUseClaim:
    """Nonpersistent proof-of-concept; not a Git tag or scientific authorization."""

    state: ClaimState = ClaimState.UNUSED
    failed_before_model: bool = False

    def consume_once(self, *, inject_pre_model_failure: bool = False) -> str:
        if self.state is ClaimState.CONSUMED:
            raise PermissionError("single-use synthetic attempt already consumed")
        self.state = ClaimState.CONSUMED
        if inject_pre_model_failure:
            self.failed_before_model = True
            return "CONSUMED_PRE_MODEL_FAILURE"
        return "CONSUMED_SYNTHETIC_ONLY"


@dataclass(frozen=True)
class ShardPlan:
    ordinal: int
    number_of_rows: int
    max_first_turn_generations: int
    science_enabled: bool = False


def partition_denominator(total: int, shards: int) -> tuple[ShardPlan, ...]:
    require(
        type(total) is int and total == 1463 and type(shards) is int and shards == 8,
        "no alternate scientific population or shard count",
    )
    quotient, remainder = divmod(total, shards)
    planned = tuple(
        ShardPlan(i, quotient + (1 if i < remainder else 0), quotient + (1 if i < remainder else 0))
        for i in range(shards)
    )
    require(
        sum(x.number_of_rows for x in planned) == 1463,
        "complete development denominator not accounted",
    )
    return planned


class FrozenScientificTransport:
    """Structural future transport interface; cannot send HTTP under B1."""

    def post(self, *args: object, **kwargs: object) -> None:
        raise PermissionError("Gate B2 authorization missing: model HTTP POST forbidden")


class FrozenAttempt3Worker:
    """Shards are counts, not patient records; science execution is impossible in B1."""

    def plan(self, contract: dict[str, Any]) -> tuple[ShardPlan, ...]:
        return partition_denominator(
            contract["frozen_science"]["development_rows"],
            contract["execution_shape"]["shards"],
        )

    def run(self, *args: object, **kwargs: object) -> None:
        raise PermissionError("Gate B2 authorization missing: worker run forbidden")

    def load_development_rows(self, *args: object, **kwargs: object) -> None:
        raise PermissionError("Gate B2 authorization missing: row replay forbidden")

    def load_sealed_final(self, *args: object, **kwargs: object) -> None:
        raise PermissionError("sealed final role is inaccessible")


class FrozenAttempt3Controller:
    """Versioned science-capable configuration: no operational scientific entrypoint."""

    def __init__(self, root: Path, contract: dict[str, Any]) -> None:
        self.root = root
        self.contract = contract

    def rehearse(self) -> dict[str, Any]:
        proof = check_policy(self.root, self.contract)
        shards = FrozenAttempt3Worker().plan(self.contract)
        # The claim test mutates only this freshly allocated in-memory dummy.
        claim = SyntheticSingleUseClaim()
        failure = claim.consume_once(inject_pre_model_failure=True)
        try:
            claim.consume_once()
        except PermissionError:
            replay_denied = True
        else:
            raise AssertionError("synthetic one-shot gate did not reject replay")
        return {
            "schema_version": "dal-sg000031-attempt3-b1-rehearsal-v1",
            "admission": "SCIENTIFIC_CAPABILITY_ENGINEERING_UNARMED",
            "contract_sha256": proof["contract_sha256"],
            "protected_files_verified": proof["protected_files_verified"],
            "frozen_producer_sha256": proof["producer_identity_sha256"],
            "attempt_ordinal": 3,
            "shard_row_counts": [item.number_of_rows for item in shards],
            "shard_count": len(shards),
            "development_denominator": sum(item.number_of_rows for item in shards),
            "first_turn_generation_limit": 1463,
            "synthetic_claim_failure": failure,
            "synthetic_claim_replay_denied": replay_denied,
            "permanent_scientific_claim_created": False,
            "execution_authorization_sha256": None,
            "scientific_dispatches": 0,
            "model_http_posts": 0,
            "rows_materialized": 0,
            "final_content_access": False,
            "training": False,
            "d4": False,
            "founder_cost_usd": 0,
            "r2_state": "BLOCKED",
            "next_gate": EXPECTED_NEXT_GATE,
        }

    def dispatch(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Gate B2 is required before scientific dispatch")

    def create_permanent_claim(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Gate B2 is required before scientific claim")
