"""Fail-closed, read-only prospective R2 Attempt-3 engineering readiness.

This tool can never create a scientific claim or admit a model request.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import study1_sg000031_r2_admission as native  # noqa: E402

CONTRACT = "registry/study1_sg000031_attempt3_readiness_contract.json"
A2_CONTRACT = "registry/study1_sg000031_attempt2_admission_contract.json"
A1_CLOSEOUT = "registry/study1_sg000031_attempt1_closeout.json"
A2_CLOSEOUT = "registry/study1_sg000031_r2_attempt2_closeout.json"
QUALIFICATION_WORKFLOW = ".github/workflows/study1-sg000031-attempt3-readiness.yml"
EXPECTED_SCHEMA = "dal-r2-attempt3-engineering-readiness-v1"
A1_RUN = 37320473498
A2_RUN = 37653806159


def read_contract(root: Path) -> dict:
    return json.loads((root / CONTRACT).read_text(encoding="utf-8"))


def check_policy(root: Path, contract: dict) -> None:
    if contract.get("schema_version") != EXPECTED_SCHEMA or type(
        contract.get("attempt_ordinal")
    ) is not int or contract["attempt_ordinal"] != 3:
        raise ValueError("Attempt-3 readiness identity invalid")
    auth = contract["execution_authorization"]
    if auth != {
        "status": "NOT_AUTHORIZED",
        "sha256": None,
        "dispatch_permitted": False,
        "claim_permitted": False,
    }:
        raise ValueError("Attempt-3 scientific authorization must remain absent")
    engineering = contract["engineering_authorization"]
    if engineering != {
        "issue": 166,
        "comment_id": 6050120310,
        "scope": "readiness-only",
        "model_calls_permitted": False,
    }:
        raise ValueError("engineering authorization does not permit inference")
    readiness = contract["readiness"]
    if readiness != {
        "qualification_workflow": QUALIFICATION_WORKFLOW,
        "actual_scientific_workflow_created": False,
        "actual_scientific_worker_created": False,
        "model_or_rows_executed": False,
        "r2_state": "BLOCKED",
        "final_role": "SEALED",
        "final_content_access": False,
        "final_rows_materialized": 0,
        "d4": False,
        "training": False,
        "founder_cost_usd": 0,
    }:
        raise ValueError("readiness may not imply scientific readiness or final access")
    if contract["governance"] != {
        "automatic_retry": False,
        "attempt3_dispatches_allowed": 0,
        "scientific_r2_pass_claim_allowed": False,
        "preflight_http_mutations_allowed": False,
        "third_execution_requires_separate_founder_authorization": True,
        "post_readiness_stop": True,
    }:
        raise ValueError("science firewall or authorization gate weakened")
    namespaces = contract["reserved_namespace"]
    expected = {
        "scientific_workflow": ".github/workflows/study1-sg000031-r2-attempt3.yml",
        "worker": ".github/workflows/study1-sg000031-r2-attempt3-worker.yml",
        "permanent_ref": "refs/tags/dal-r2-issue166-attempt3",
        "ledger_branch": "codex/sg000031-r2-attempt3-journal",
        "ledger_root": "evidence/study1-r2-attempt3",
        "receipt_marker": "DAL_R2_ATTEMPT3_CANONICAL_ADMISSION_V1",
    }
    if namespaces != expected:
        raise ValueError("fresh Attempt-3 namespace required")
    if (root / expected["scientific_workflow"]).exists() or (
        root / expected["worker"]
    ).exists():
        raise ValueError("unarmed engineering grain may not create science workflows")
    if contract["canonical_base"] != {
        "sha": "6b345396d16f4e827d6339fdd850ec86c6a9a399",
        "tree": "233f0303d230458debc1e812045766e25c8fa323",
    }:
        raise ValueError("preparation baseline changed")
    historical = contract["historical_attempts"]
    if len(historical) != 2 or [x["ordinal"] for x in historical] != [1, 2]:
        raise ValueError("the two immutable predecessors are mandatory")
    if [x["run_id"] for x in historical] != [A1_RUN, A2_RUN]:
        raise ValueError("historical scientific dispatch identity mismatch")
    if any(
        x["run_attempt"] != 1
        or x["conclusion"] != "failure"
        or x["model_posts"] != 0
        or x["unattempted_rows"] != 1463
        or x["consumed"] is not True
        for x in historical
    ):
        raise ValueError("historical failure and consumption cannot be rewritten")
    if native.lf_digest(root / A2_CONTRACT) != historical[1]["contract_sha256"]:
        raise ValueError("canonical Attempt-2 admission contract digest drift")
    a2 = json.loads((root / A2_CONTRACT).read_text(encoding="utf-8"))
    close1 = json.loads((root / A1_CLOSEOUT).read_text(encoding="utf-8"))
    close2 = json.loads((root / A2_CLOSEOUT).read_text(encoding="utf-8"))
    freeze = contract["scientific_freeze"]
    if freeze != {
        "r1_manifest_sha256": a2["canonical_r1"]["manifest_sha256"],
        "producer_identity_sha256": a2["producer_identity_sha256"],
        "population_identity_sha256": a2["development"][
            "question_role_assignments_sha256"
        ],
        "development_rows": 1463,
        "calibration_rows": 341,
        "validation_rows": 1122,
        "sealed_final_patients": 40,
        "sealed_final_rows": 173,
    }:
        raise ValueError("R1/producer/population or final freeze changed")
    if native.lf_digest(root / "registry/study1_sg000030_r1_manifest.json") != (
        freeze["r1_manifest_sha256"]
    ):
        raise ValueError("real frozen R1 manifest drift")
    for file, digest in a2["immutable_file_lf_sha256"].items():
        if native.lf_digest(root / file) != digest:
            raise ValueError("scientific protected file drift: " + file)
    if close1["run"]["id"] != A1_RUN or close1["scientific_state"] != "BLOCKED":
        raise ValueError("Attempt 1 historical record changed")
    if (
        close2["dispatch_run_id"] != A2_RUN
        or close2["scientific_state"] != "BLOCKED"
        or close2["execution_authorization_consumed"] is not True
        or close2["attempt3_authorized"] is not False
        or close2["accounting"]["physical_model_POSTs"] != 0
        or close2["accounting"]["first_turn_generations"] != 0
        or close2["accounting"]["rows_unattempted"] != 1463
    ):
        raise ValueError("Attempt 2 closeout and consumption mismatch")
    expected2 = historical[1]
    if (
        expected2["execution_authorization_sha256"]
        != close2["execution_authorization_sha256"]
        or expected2["contract_sha256"] != close2["admission_contract_sha256"]
        or expected2["canonical_main"] != close2["execution_main"]
        or expected2["canonical_tree"] != close2["execution_tree"]
    ):
        raise ValueError("Attempt-2 immutable lineage mismatch")
    workflow = (root / QUALIFICATION_WORKFLOW).read_text(encoding="utf-8")
    if (
        "workflow_dispatch:" in workflow
        or "pull_request:" not in workflow
        or "push:" not in workflow
        or "fetch-depth: 0" not in workflow
        or "persist-credentials: false" not in workflow
        or "tools/qualify_sg000031_attempt3_readiness.py" not in workflow
        or "tests/test_study1_sg000031_attempt3_readiness.py" not in workflow
    ):
        raise ValueError("read-only CI qualification wiring changed")


def check_history(root: Path, contract: dict, *, api=native.api) -> dict:
    for predecessor in contract["historical_attempts"]:
        run = api("actions/runs/" + str(predecessor["run_id"]))
        if (
            run["id"] != predecessor["run_id"]
            or run["run_attempt"] != 1
            or run["status"] != "completed"
            or run["conclusion"] != "failure"
            or run["event"] != "workflow_dispatch"
        ):
            raise ValueError("historical scientific execution run changed")
    ref = api("git/ref/tags/dal-r2-issue158-attempt2")
    tag_sha = contract["historical_attempts"][1]["claim_tag_object"]
    if ref["object"]["sha"] != tag_sha:
        raise ValueError("consumed Attempt-2 tag rewritten")
    tag = api("git/tags/" + tag_sha)
    if (
        tag["object"]["sha"] != contract["historical_attempts"][1]["canonical_main"]
        or json.loads(tag["message"]).get("execution_authorization_sha256")
        != contract["historical_attempts"][1]["execution_authorization_sha256"]
        or json.loads(tag["message"]).get("run_id") != A2_RUN
        or json.loads(tag["message"]).get("contract_sha256")
        != contract["historical_attempts"][1]["contract_sha256"]
    ):
        raise ValueError("Attempt-2 permanent claim mutated")
    for path, run_id in (
        ("study1-sg000031-r2-recovery.yml", A1_RUN),
        ("study1-sg000031-r2-attempt2.yml", A2_RUN),
    ):
        history = api("actions/workflows/" + path + "/runs?per_page=100")
        if history["total_count"] != 1 or len(history["workflow_runs"]) != 1:
            raise ValueError("new or duplicate historical dispatch")
        if history["workflow_runs"][0]["id"] != run_id:
            raise ValueError("historical attempt run mismatch")
    try:
        api("git/ref/tags/dal-r2-issue166-attempt3")
    except HTTPError as err:
        if err.code != 404:
            raise
    else:
        raise ValueError("unexpected Attempt-3 scientific claim/tag")
    return {"attempt1_run": A1_RUN, "attempt2_run": A2_RUN, "attempt3_tag_present": False}


def qualify(root: Path = ROOT) -> dict:
    if os.environ["GITHUB_REPOSITORY"] != native.REPOSITORY:
        raise ValueError("wrong repository")
    if os.environ["GITHUB_EVENT_NAME"] not in ("pull_request", "push"):
        raise ValueError("only automated engineering CI qualification permitted")
    if os.environ["GITHUB_RUN_ATTEMPT"] != "1":
        raise ValueError("automatic CI rerun cannot substitute for exact qualification")
    head = native.git("rev-parse", "HEAD")
    if head != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("wrong checkout SHA")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("full history required for actual parent checks")
    contract = read_contract(root)
    check_policy(root, contract)
    parents = native.git(
        "show", "-s", "--format=%P",
        contract["historical_attempts"][1]["canonical_main"],
    ).split()
    if parents != contract["historical_attempts"][1]["merge_parents"]:
        raise ValueError("historical exact merge ancestry mismatch")
    if native.git("rev-parse", contract["historical_attempts"][1]["canonical_main"]
                  + "^{tree}") != contract["historical_attempts"][1]["canonical_tree"]:
        raise ValueError("historical exact tree mismatch")
    with native.native_read_only_preflight() as audit:
        live_main = native.api("git/ref/heads/main")["object"]["sha"]
        if os.environ["GITHUB_EVENT_NAME"] == "pull_request":
            expected_base = os.environ["EXPECTED_BASE_SHA"]
            if live_main != expected_base or expected_base != (
                contract["canonical_base"]["sha"]
            ):
                raise ValueError("PR base drift")
            pr = native.api("pulls/" + os.environ["PR_NUMBER"])
            if pr["head"]["sha"] != head or pr["base"]["sha"] != live_main:
                raise ValueError("PR exact-head mismatch")
        elif live_main != head:
            raise ValueError("post-main checkout drift")
        history = check_history(root, contract)
    return {
        "schema_version": "dal-r2-attempt3-readiness-preflight-v1",
        "phase": "candidate" if os.environ["GITHUB_EVENT_NAME"] == "pull_request"
        else "post-main",
        "engineering_readiness": "PASS",
        "attempt3_execution_authorized": False,
        "R2_scientific_state": "BLOCKED",
        "execution_authorization_sha256": None,
        "checked_out_sha": head,
        "protected_files_verified": len(
            json.loads((root / A2_CONTRACT).read_text(encoding="utf-8"))[
                "immutable_file_lf_sha256"
            ]
        ),
        "historical_runs": history,
        "new_scientific_dispatches": 0,
        "new_model_calls": 0,
        "final_content_access": False,
        "final_rows_materialized": 0,
        "REST_mutations_permitted": False,
        "request_audit": audit,
        "founder_cost_usd": 0,
        "next_gate": "new explicit founder scientific execution authorization",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = qualify()
    except Exception as exc:
        native.write_exclusive(
            args.output,
            {
                "engineering_readiness": "FAILED",
                "R2_scientific_state": "BLOCKED",
                "attempt3_execution_authorized": False,
                "new_model_calls": 0,
                "error_sha256": native.digest(str(exc)),
            },
        )
        raise SystemExit("Attempt-3 readiness failed closed; no dispatch permitted") from None
    native.write_exclusive(args.output, report)
    print("ATTEMPT3_READINESS=PASS; SCIENTIFIC_DISPATCH=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
