"""Read-only post-consumption qualification of the bounded R2 worker ancestry repair.

This mode does not admit, claim, dispatch, retry, score or generate any scientific row.
It verifies the *consumed* historical Attempt-2 identity and the amended checkout.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import study1_sg000031_r2_admission as native  # noqa: E402

ATTEMPT_RUN = 37653806159
ATTEMPT_MAIN = "8fcf29f2e0c1b6cf78661acd2f5e1340a578ac03"
ATTEMPT_TREE = "430da88b2cd85a32b41cac5d6d2951fb8ebfb944"
ATTEMPT_TAG = "14a92834c3e9e28f83dd6cb696d7c3e78bea9c17"
REPAIR_MAIN = "0e298850b3392eafedeacc995e36c1e15391a15c"
REPAIR_HEAD = "9dcb0a63de888d2258d982c695e49cff3d04266d"
CONTRACT_SHA = "0f5e8ac550ca578afae69cdb948f0b9199a729b038071c7777b55b1e4d567105"
AUTH_SHA = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
LINEAGE_SHA = "361dc916c5066c04c8c008ceb772442ebc54ebbbf0d412c817e9e7f9fc75eb3c"
R1_SHA = "220c676df241d8dc1ac8ccd83e81d54554e7618fc5acf016eaa32ec6302ca2b0"
POPULATION_SHA = "0755fcb62129037e05557d73863574b399503458b48b2c5a906546575aa1679f"
PRODUCER_SHA = "4794eef60d9a7ec3e82d21390127bbfbc4156f7abfeb311313c13bef9b7c1860"
WORKFLOW = ".github/workflows/study1-sg000031-r2-attempt2-worker.yml"
CONTRACT = "registry/study1_sg000031_attempt2_admission_contract.json"
EXECUTION_WORKFLOW = ".github/workflows/study1-sg000031-r2-attempt2.yml"
FROZEN_PARENTS = [REPAIR_MAIN, REPAIR_HEAD]


def verify_worker_and_ancestry(root: Path, git=native.git) -> None:
    worker = (root / WORKFLOW).read_text(encoding="utf-8")
    checkout = worker.split("      - name: Checkout exact canonical execution main\n", 1)[1]
    checkout, rest = checkout.split("      - name: Set up Python\n", 1)
    if (
        checkout.count("fetch-depth: 0") != 1
        or "ref: " + "$" + "{{ github.sha }}" not in checkout
        or "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
        not in checkout
        or "      - name: Verify permanent exact-run R2 claim before infrastructure setup"
        not in rest
    ):
        raise ValueError("bounded worker checkout/claim step changed")
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("shallow checkout cannot prove frozen merge ancestry")
    if git("rev-parse", ATTEMPT_MAIN + "^{tree}") != ATTEMPT_TREE:
        raise ValueError("immutable Attempt-2 merge tree mismatch")
    if git("show", "-s", "--format=%P", ATTEMPT_MAIN).split() != FROZEN_PARENTS:
        raise ValueError("immutable Attempt-2 normal merge parents mismatch")


def verify_consumed_claim(root: Path, api=native.api) -> dict:
    if native.lf_digest(root / CONTRACT) != CONTRACT_SHA:
        raise ValueError("canonical Attempt-2 contract changed")
    ref = api("git/ref/tags/dal-r2-issue158-attempt2")
    if ref["object"]["sha"] != ATTEMPT_TAG:
        raise ValueError("consumed Attempt-2 tag ref changed")
    tag = api("git/tags/" + ATTEMPT_TAG)
    if tag["object"] != {"sha": ATTEMPT_MAIN, "type": "commit",
                          "url": native.REPOSITORY_API + "/git/commits/" + ATTEMPT_MAIN}:
        raise ValueError("Attempt-2 tag target changed")
    claim = json.loads(tag["message"])
    required = {
        "schema_version": "study1-r2-attempt2-claim-v1",
        "attempt_ordinal": 2,
        "predecessor_attempt_ordinal": 1,
        "run_id": ATTEMPT_RUN,
        "run_attempt": 1,
        "main_sha": ATTEMPT_MAIN,
        "tree": ATTEMPT_TREE,
        "contract_sha256": CONTRACT_SHA,
        "execution_authorization_sha256": AUTH_SHA,
        "attempt1_lineage_sha256": LINEAGE_SHA,
        "qualification_receipt_sha256":
            "ed2df6e8e3c96bbd59234260d0b646a7be8b2ce766c94f45bc29e0348ff7fe25",
        "engineering_qualified": True,
        "zero_cost_infrastructure_verified": True,
    }
    for field, value in required.items():
        if type(claim.get(field)) is not type(value) or claim[field] != value:
            raise ValueError("consumed Attempt-2 claim mismatch: " + field)
    receipt = claim["qualification_receipt"]
    for field, value in {
        "r1_manifest_sha256": R1_SHA,
        "population_sha256": POPULATION_SHA,
        "producer_identity_sha256": PRODUCER_SHA,
        "main_sha": ATTEMPT_MAIN,
        "tree": ATTEMPT_TREE,
        "base_sha": REPAIR_MAIN,
        "head_sha": REPAIR_HEAD,
    }.items():
        if receipt.get(field) != value:
            raise ValueError("frozen Attempt-2 receipt mismatch: " + field)
    if native.digest(native.json_bytes(receipt)) != claim["qualification_receipt_sha256"]:
        raise ValueError("consumed qualification receipt digest mismatch")
    run = api("actions/runs/" + str(ATTEMPT_RUN))
    if (
        run["id"] != ATTEMPT_RUN
        or run["run_attempt"] != 1
        or run["head_sha"] != ATTEMPT_MAIN
        or run["path"] != EXECUTION_WORKFLOW
        or run["event"] != "workflow_dispatch"
        or run["status"] != "completed"
        or run["conclusion"] != "failure"
    ):
        raise ValueError("retained failed scientific dispatch identity changed")
    history = api("actions/workflows/study1-sg000031-r2-attempt2.yml/runs?per_page=100")
    if history["total_count"] != 1 or len(history["workflow_runs"]) != 1:
        raise ValueError("new or duplicate Attempt-2 dispatch detected")
    if history["workflow_runs"][0]["id"] != ATTEMPT_RUN:
        raise ValueError("unexpected Attempt-2 dispatch history")
    return claim


def qualify(root: Path = ROOT) -> dict:
    if os.environ["GITHUB_REPOSITORY"] != native.REPOSITORY:
        raise ValueError("wrong repository")
    if os.environ["GITHUB_RUN_ATTEMPT"] != "1":
        raise ValueError("engineering rerun does not inherit proof")
    event = os.environ["GITHUB_EVENT_NAME"]
    if event not in {"pull_request", "push"}:
        raise ValueError("post-consumption mode is not a scientific dispatch entrypoint")
    checkout = native.git("rev-parse", "HEAD")
    if checkout != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("exact checked-out head mismatch")
    if event == "pull_request":
        expected_pr = os.environ.get("PR_NUMBER", "")
        if expected_pr != "164":
            raise ValueError("unexpected repair PR")
    else:
        if os.environ["GITHUB_REF"] != "refs/heads/main":
            raise ValueError("post-main qualification must run on main")
    verify_worker_and_ancestry(root)
    with native.native_read_only_preflight() as audit:
        if event == "pull_request":
            pr = native.api("pulls/164")
            if (
                pr["head"]["sha"] != checkout
                or pr["base"]["sha"] != os.environ["EXPECTED_BASE_SHA"]
                or pr["merged"] is not False
            ):
                raise ValueError("current PR head or base changed")
        else:
            if native.api("git/ref/heads/main")["object"]["sha"] != checkout:
                raise ValueError("current main differs from qualified checkout")
        claim = verify_consumed_claim(root)
    return {
        "schema_version": "study1-r2-postconsumption-worker-ancestry-preflight-v1",
        "phase": "candidate" if event == "pull_request" else "post-main",
        "engineering_preflight_state": "PASS",
        "R2_scientific_state": "BLOCKED",
        "checkout_sha": checkout,
        "attempt_ordinal": 2,
        "historical_scientific_run_id": ATTEMPT_RUN,
        "historical_scientific_run_failed": True,
        "execution_authorization_consumed": True,
        "authorization_sha256": AUTH_SHA,
        "historical_claim_tag_sha": ATTEMPT_TAG,
        "historical_claim_receipt_sha256": claim["qualification_receipt_sha256"],
        "historical_generation_count": 0,
        "historical_physical_model_POSTs": 0,
        "development_rows_unattempted": 1463,
        "new_scientific_dispatches": 0,
        "new_model_calls": 0,
        "new_claim_created": False,
        "REST_mutations_permitted": False,
        "native_requests": audit,
        "final_content_access": False,
        "final_rows_materialized": 0,
        "D4": False,
        "training": False,
        "founder_cost_usd": 0,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = qualify()
    except Exception as error:
        native.write_exclusive(
            args.output,
            {
                "schema_version": "study1-r2-postconsumption-worker-ancestry-preflight-v1",
                "engineering_preflight_state": "FAILED",
                "R2_scientific_state": "BLOCKED",
                "error_sha256": native.digest(str(error)),
                "new_execution_authorized": False,
                "new_model_calls": 0,
            },
        )
        raise SystemExit("post-consumption repair qualification failed; no inference allowed") from None
    native.write_exclusive(args.output, report)
    print("POSTCONSUMPTION_ANCESTRY_PREFLIGHT=PASS; ATTEMPT3=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
