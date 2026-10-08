"""Native read-only exact-head qualification for B1 durable-design continuation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from gaxbench.study1_attempt3_b1 import lf_sha256
from gaxbench.study1_attempt3_b1_durable import (
    MAIN_BASE,
    TREE_BASE,
    synthetic_durable_rehearsal,
    verify_contract,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import qualify_sg000031_attempt3_b1 as old  # noqa: E402
import qualify_sg000031_attempt3_readiness as readiness  # noqa: E402
import study1_sg000031_r2_admission as native  # type: ignore  # noqa: E402

SCHEMA = "dal-sg000031-attempt3-b1-durable-native-v1"
FOUNDER_COMMENT = 6066751157
PROHIBITED_REF = "git/ref/tags/dal-r2-issue166-attempt3"


def live_gate(event: str, sha: str) -> dict[str, Any]:
    """Zero GitHub mutation; enforce exact normal-merge ancestry or candidate head."""
    if native.git("rev-parse", "HEAD") != sha:
        raise ValueError("exact B1 runtime checkout drift")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("B1 runtime requires full Git ancestry")
    if native.git("rev-parse", MAIN_BASE + "^{tree}") != TREE_BASE:
        raise ValueError("prior qualified B1 merge tree drift")
    live = native.api("git/ref/heads/main")["object"]["sha"]
    if event == "pull_request":
        if live != MAIN_BASE or os.environ.get("EXPECTED_BASE_SHA") != MAIN_BASE:
            raise ValueError("B1 runtime candidate base moved")
        if native.git("merge-base", MAIN_BASE, sha) != MAIN_BASE:
            raise ValueError("B1 runtime candidate ancestry missing")
        pr = native.api("pulls/" + str(int(os.environ["PR_NUMBER"])))
        if (
            pr["state"] != "open"
            or pr["merged"] is not False
            or pr["head"]["sha"] != sha
            or pr["base"]["sha"] != MAIN_BASE
        ):
            raise ValueError("B1 runtime candidate PR exact-head mismatch")
    else:
        parents = native.git("show", "-s", "--format=%P", sha).split()
        if live != sha or len(parents) != 2 or parents[0] != MAIN_BASE:
            raise ValueError("B1 runtime requires guarded normal merge")
        if native.git("rev-parse", sha + "^{tree}") != native.git(
            "rev-parse", parents[1] + "^{tree}"
        ):
            raise ValueError("B1 runtime merged source tree mismatch")
        merged = native.api("commits/" + sha + "/pulls")
        approved_prs = [
            item
            for item in merged
            if item.get("merge_commit_sha") == sha
            and item.get("merged_at") is not None
            and item.get("base", {}).get("ref") == "main"
        ]
        if len(approved_prs) != 1:
            raise ValueError("B1 runtime canonical PR ambiguous")
        pr = native.api("pulls/" + str(approved_prs[0]["number"]))
        if (
            pr["head"]["sha"] != parents[1]
            or pr["merge_commit_sha"] != sha
            or pr["merged"] is not True
        ):
            raise ValueError("B1 runtime merge PR parent mismatch")
    return {"phase": "candidate" if event == "pull_request" else "post-main", "live_main": live}


def no_permanent_attempt3_ref() -> None:
    try:
        native.api(PROHIBITED_REF)
    except HTTPError as error:
        if error.code == 404:
            return
        raise
    raise PermissionError("a real Attempt-3 claim already exists: STOP")


def qualify(root: Path = ROOT) -> dict[str, Any]:
    event = old.check_environment()
    expected_sha = os.environ["EXPECTED_CHECKOUT_SHA"]
    contract = verify_contract(root)
    proof = synthetic_durable_rehearsal(root)
    if not (
        proof["simulated_ref_created_once"]
        and proof["simulated_duplicate_denied"]
        and proof["real_github_mutations"] == 0
        and proof["model_posts"] == 0
        and proof["rows_replayed"] == 0
        and proof["B2_authorized"] is False
    ):
        raise PermissionError("B1 fake durable ref simulation is invalid")
    with native.native_read_only_preflight() as trace:
        founder = old.verify_founder_record()
        state = live_gate(event, expected_sha)
        history = readiness.check_history(root, readiness.read_contract(root))
        no_permanent_attempt3_ref()
    if any(req["method"] != "GET" for req in trace):
        raise PermissionError("B1 runtime attempted a GitHub mutation")
    return {
        "schema_version": SCHEMA,
        "engineering_qualification": "PASS",
        "exact_head": expected_sha,
        **state,
        "founder": founder,
        "historical_runs": history,
        "durable_contract_sha256": lf_sha256(
            root / "registry/study1_sg000031_attempt3_b1_durable_contract.json"
        ),
        "predecessor_contract_sha256": contract["frozen_predecessor"]["sha256"],
        "source_lf_sha256": {
            path: lf_sha256(root / path)
            for path in (
                "src/gaxbench/study1_attempt3_b1_durable.py",
                "tools/qualify_sg000031_attempt3_b1_durable.py",
                "tests/test_study1_sg000031_attempt3_b1_durable.py",
                "docs/study1-sg000031-attempt3-b1-durable.md",
                ".github/workflows/study1-sg000031-attempt3-b1.yml",
            )
        },
        "proof": proof,
        "request_audit": trace,
        "protected_files": 43,
        "real_attempt3_ref_absent": True,
        "B2_execution_authorization": None,
        "scientific_dispatches": 0,
        "model_posts": 0,
        "rows_replayed": 0,
        "real_permanent_claim": False,
        "final_content_access": False,
        "d4": False,
        "training": False,
        "R2": "BLOCKED",
        "founder_cost_usd": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail-closed B1 durable runtime qualification")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = qualify()
    except Exception as exc:
        native.write_exclusive(
            args.output,
            {
                "schema_version": SCHEMA,
                "engineering_qualification": "FAILED_CLOSED",
                "error_sha256": native.digest(str(exc)),
                "scientific_dispatches": 0,
                "B2_execution_authorization": None,
                "R2": "BLOCKED",
            },
        )
        raise SystemExit("B1 failed closed; no science authorized") from None
    native.write_exclusive(args.output, report)
    print("B1_DURABLE_DESIGN=QUALIFIED; REAL_CLAIM=ABSENT; GATE_B2=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
