"""Prospective Attempt-3 admission interface: executable engineering rehearsal, never science.

No model, network, file mutation, worker dispatch, or persistent claim API is imported.
A separately governed future implementation and founder authorization are both required
before *any* scientific execution could become possible.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = "registry/study1_sg000031_attempt3_admission_contract.json"
READY_PATH = "registry/study1_sg000031_attempt3_readiness_contract.json"
A2_PATH = "registry/study1_sg000031_attempt2_admission_contract.json"
SCHEMA = "dal-sg000031-attempt3-admission-engineering-v1"
ENGINEERING_SHA = "6caaa5341aa798db66855fb3525c73b7de3327c9"
ENGINEERING_TREE = "c2f48dbd06850b54e364651b0a7552d15e1bf8cf"
AUTH_COMMENT = 6062562405
A2_AUTH = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"


def _require(condition: bool, error: str) -> None:
    if not condition:
        raise ValueError(error)


def _read_json(root: Path, path: str) -> dict[str, Any]:
    source = root / path
    _require(
        not source.is_symlink() and source.is_file(),
        "missing or linked protected evidence: " + path,
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid evidence object: " + path)
    return data


def _lf_sha256(path: Path) -> str:
    _require(path.is_file() and not path.is_symlink(), "missing or linked protected file")
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_contract(root: Path) -> dict[str, Any]:
    return _read_json(root, CONTRACT_PATH)


def check_contract(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Strict local content and scientific firewall qualification (no I/O writes)."""
    expected_keys = {
        "schema_version",
        "specgrain_id",
        "attempt_ordinal",
        "engineering_authorization",
        "engineering_base",
        "readiness_contract",
        "attempt2_contract",
        "execution_authorization",
        "scientific_freeze",
        "historical_attempts",
        "reserved_scientific_namespace",
        "admission",
        "firewall",
    }
    _require(set(contract) == expected_keys, "admission schema changed")
    _require(
        contract["schema_version"] == SCHEMA
        and type(contract["attempt_ordinal"]) is int
        and contract["attempt_ordinal"] == 3
        and contract["specgrain_id"] == "SG-000031-A3-E",
        "attempt-3 admission identity changed",
    )
    _require(
        contract["engineering_authorization"]
        == {
            "issue": 168,
            "transcribed_comment_id": AUTH_COMMENT,
            "provenance": "founder-chat-transcribed-by-assistant",
            "scope": "executable-but-unarmed-admission",
            "scientific_execution_authorized": False,
        },
        "engineering provenance or scope changed",
    )
    _require(
        contract["engineering_base"] == {"sha": ENGINEERING_SHA, "tree": ENGINEERING_TREE},
        "qualified canonical engineering base changed",
    )
    _require(
        contract["readiness_contract"] == READY_PATH and contract["attempt2_contract"] == A2_PATH,
        "upstream contract path drift",
    )
    _require(
        contract["execution_authorization"]
        == {
            "status": "NOT_AUTHORIZED",
            "sha256": None,
            "dispatch_permitted": False,
            "permanent_claim_permitted": False,
            "model_calls_permitted": False,
            "row_replay_permitted": False,
        },
        "execution authorization MUST remain absent",
    )
    ready = _read_json(root, READY_PATH)
    a2 = _read_json(root, A2_PATH)
    _require(
        ready["execution_authorization"]["sha256"] is None
        and ready["execution_authorization"]["status"] == "NOT_AUTHORIZED",
        "prior Attempt-3 readiness is unexpectedly armed",
    )
    _require(
        contract["scientific_freeze"] == ready["scientific_freeze"],
        "immutable scientific freeze mismatch",
    )
    _require(
        contract["reserved_scientific_namespace"] == ready["reserved_namespace"],
        "unique Attempt-3 namespace drift",
    )
    _require(
        contract["historical_attempts"]
        == {
            "attempt1_run": 37320473498,
            "attempt2_run": 37653806159,
            "attempt2_execution_authorization_sha256": A2_AUTH,
            "both_consumed": True,
            "both_infrastructure_failed": True,
            "both_model_posts": 0,
        },
        "historical attempts or consumed authorization rewritten",
    )
    _require(
        a2["execution_authorization_sha256"] == A2_AUTH, "Attempt-2 consumed authorization mismatch"
    )
    _require(
        a2["canonical_r1"]["manifest_sha256"]
        == contract["scientific_freeze"]["r1_manifest_sha256"],
        "frozen R1 manifest identity mismatch",
    )
    _require(
        a2["producer_identity_sha256"] == contract["scientific_freeze"]["producer_identity_sha256"],
        "frozen producer mismatch",
    )
    _require(
        a2["development"]["question_role_assignments_sha256"]
        == contract["scientific_freeze"]["population_identity_sha256"],
        "frozen population mismatch",
    )
    protected = a2["immutable_file_lf_sha256"]
    _require(type(protected) is dict and len(protected) == 43, "protected source inventory changed")
    for relative, digest in protected.items():
        _require(
            _lf_sha256(root / relative) == digest,
            "protected scientific digest mismatch: " + relative,
        )

    _require(
        contract["admission"]
        == {
            "qualification_workflow": (
                ".github/workflows/study1-sg000031-attempt3-admission-qualification.yml"
            ),
            "controller": "tools/study1_sg000031_attempt3_admission.py",
            "validator": "src/gaxbench/study1_attempt3_admission.py",
            "read_only_http": True,
            "synthetic_rehearsal_only": True,
            "all_production_mutations_prohibited": True,
            "worker_runtime_created": False,
            "scientific_workflow_created": False,
            "automatic_retry": False,
            "next_scientific_execution_requires_new_founder_approval": True,
        },
        "admission interlock weakened",
    )
    _require(
        contract["firewall"]
        == {
            "r2_state": "BLOCKED",
            "final_role": "SEALED",
            "final_content_access": False,
            "final_rows_materialized": 0,
            "training": False,
            "fine_tuning": False,
            "d4": False,
            "scientific_dispatches": 0,
            "model_posts": 0,
            "founder_cost_usd": 0,
        },
        "scientific/final/cost firewall weakened",
    )
    namespaces = contract["reserved_scientific_namespace"]
    _require(
        not (root / namespaces["scientific_workflow"]).exists()
        and not (root / namespaces["worker"]).exists(),
        "an executable scientific workflow/worker is forbidden",
    )
    workflow = (root / contract["admission"]["qualification_workflow"]).read_text(encoding="utf-8")
    _require(
        "workflow_dispatch:" not in workflow
        and "repository_dispatch:" not in workflow
        and "schedule:" not in workflow
        and "pull_request:" in workflow
        and "push:" in workflow
        and "fetch-depth: 0" in workflow
        and "persist-credentials: false" in workflow
        and "tools/qualify_sg000031_attempt3_admission.py" in workflow,
        "non-read-only admission workflow configuration",
    )
    return {
        "protected_files": len(protected),
        "freeze_sha256": contract["scientific_freeze"]["r1_manifest_sha256"],
        "contract_sha256": _lf_sha256(root / CONTRACT_PATH),
        "unarmed": True,
    }


class Attempt3AdmissionController:
    """Synthetic qualification only. There is no admission-to-science method."""

    def __init__(self, contract: dict[str, Any]) -> None:
        self._contract = contract

    def rehearse(self, root: Path) -> dict[str, Any]:
        proof = check_contract(root, self._contract)
        return {
            "schema_version": "dal-attempt3-admission-rehearsal-v1",
            "admission_contract_sha256": proof["contract_sha256"],
            "protected_files": proof["protected_files"],
            "attempt_ordinal": 3,
            "engineering_admission": "REHEARSED_UNARMED",
            "scientific_execution_authorized": False,
            "permanent_claim_created": False,
            "model_posts": 0,
            "rows_replayed": 0,
            "final_content_access": False,
            "r2_scientific_state": "BLOCKED",
            "founder_cost_usd": 0,
        }

    def dispatch(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Attempt-3 scientific dispatch is NOT_AUTHORIZED")

    def create_claim(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Attempt-3 permanent scientific claim is NOT_AUTHORIZED")


class Attempt3AdmissionWorker:
    """A structural interface, deliberately not a deployable or callable science worker."""

    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError("Attempt-3 scientific worker is NOT_AUTHORIZED")
