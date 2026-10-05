"""Native authenticated admission qualification only; never claims, plans or infers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import study1_sg000031_r2_admission as admission  # noqa: E402

HISTORICAL_RECEIPT_COMMENT = 5995901646
HISTORICAL_RUNNER_MAIN = "73e98360863aaa1cd039ffaa5cef2e4311dcfafa"
FAILED_ATTEMPT = 37320473498
FAILURE_MAIN = "3ebf58ef10a42db6ee31d96451ea80fe98432b4c"


def qualify(root):
    repair_path = root / "registry/study1_sg000031_admission_repair_contract.json"
    repair = json.loads(repair_path.read_bytes())
    if repair["authorization_base_main"] != FAILURE_MAIN or repair["new_execution_authorized"]:
        raise ValueError("admission repair scope drift")
    for path, expected in repair["immutable_file_lf_sha256"].items():
        if admission.lf_digest(root / path) != expected:
            raise ValueError("admission repair immutable evidence/control drift")
    if admission.lf_digest(root / repair["authorization_path"]) != repair["authorization_sha256"]:
        raise ValueError("repair-only founder authorization drift")
    if os.environ["GITHUB_REPOSITORY"] != admission.REPOSITORY:
        raise ValueError("native preflight repository drift")
    checkout = admission.git("rev-parse", "HEAD")
    if checkout != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("native preflight checkout drift")
    with admission.native_read_only_preflight() as audit:
        receipt, tree, units = admission.qualify_canonical_receipt(
            root, HISTORICAL_RECEIPT_COMMENT, HISTORICAL_RUNNER_MAIN, live_main=False
        )
        # Historical validation does not admit execution on this new repair checkout.
        live_main = admission.api("git/ref/heads/main")["object"]["sha"]
        failure = admission.api(f"actions/runs/{FAILED_ATTEMPT}")
        if (
            failure["run_attempt"] != 1
            or failure["status"] != "completed"
            or failure["conclusion"] != "failure"
            or failure["head_sha"] != HISTORICAL_RUNNER_MAIN
            or failure["path"] != admission.WORKFLOW
        ):
            raise ValueError("retained failed attempt drift")
    if not audit or audit[0]["url"] != admission.REPOSITORY_API or audit[0]["status"] != 200:
        raise ValueError("corrected native repository lookup not qualified")
    source_files = [
        "scripts/study1_sg000031_r2_admission.py",
        "tools/qualify_sg000031_admission.py",
        "tests/test_study1_sg000031_admission_repair.py",
        ".github/workflows/study1-sg000031-admission-preflight.yml",
    ]
    return {
        "schema_version": "study1-r2-native-admission-preflight-v1",
        "engineering_preflight_state": "PASS",
        "R2_scientific_state": "BLOCKED",
        "checkout_sha": checkout,
        "live_main_observed": live_main,
        "repair_authorization_base": FAILURE_MAIN,
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
        "authentication_context": (
            "workflow-github-token-in-GH_TOKEN; same native request headers/opener"
        ),
        "repair_contract_sha256": admission.lf_digest(repair_path),
        "immutable_files_verified": len(repair["immutable_file_lf_sha256"]),
        "historical_receipt_comment_id": HISTORICAL_RECEIPT_COMMENT,
        "historical_receipt_sha256": admission.digest(admission.json_bytes(receipt)),
        "historical_receipt_main": HISTORICAL_RUNNER_MAIN,
        "historical_receipt_tree": tree,
        "historical_jev_units_verified": units,
        "historical_validation_is_not_live_execution_admission": True,
        "real_admit_requires_live_main": True,
        "retained_failed_attempt": FAILED_ATTEMPT,
        "native_requests": audit,
        "source_lf_sha256": {path: admission.lf_digest(root / path) for path in source_files},
        "REST_mutations_permitted": False,
        "attempt_claim_created": False,
        "row_ledger_created": False,
        "benchmark_downloaded": False,
        "first_turn_generations": 0,
        "physical_model_POSTs": 0,
        "final_rows_materialized": 0,
        "final_content_access": False,
        "founder_cost_usd": 0,
        "new_execution_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = qualify(ROOT)
    except Exception as error:
        admission.write_exclusive(
            args.output,
            {
                "engineering_preflight_state": "FAILED",
                "R2_scientific_state": "BLOCKED",
                "error_sha256": admission.digest(str(error)),
                "new_execution_authorized": False,
            },
        )
        raise SystemExit("Native admission qualification failed; no execution authorized") from None
    admission.write_exclusive(args.output, report)
    print("NATIVE_ADMISSION_PREFLIGHT=PASS; R2=BLOCKED; MODEL_POSTS=0")


if __name__ == "__main__":
    main()
