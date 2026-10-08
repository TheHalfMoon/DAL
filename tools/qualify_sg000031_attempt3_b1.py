"""Native exact-head, authenticated GET-only qualification of UNARMED Gate B1."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_b1 import (
    B1_BASE,
    B1_COMMENT,
    FrozenAttempt3Controller,
    check_policy,
    load_contract,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))
import qualify_sg000031_attempt3_readiness as readiness  # noqa: E402
import study1_sg000031_r2_admission as native  # type: ignore  # noqa: E402

SCHEMA = "dal-sg000031-attempt3-b1-native-qualification-v1"


def check_environment() -> str:
    if os.environ.get("GITHUB_REPOSITORY") != native.REPOSITORY:
        raise ValueError("wrong canonical repo for B1")
    event = os.environ.get("GITHUB_EVENT_NAME")
    if event not in ("push", "pull_request"):
        raise ValueError("B1 rejects all manual/scientific dispatch events")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise ValueError("B1 automatic CI rerun cannot qualify")
    if not os.environ.get("EXPECTED_CHECKOUT_SHA"):
        raise ValueError("missing exact B1 checkout")
    return event


def verify_founder_record(api: Callable[..., Any] = native.api) -> dict[str, Any]:
    issue = api("issues/171")
    if issue.get("number") != 171 or issue.get("state") != "open":
        raise ValueError("B1 founder issue closed/changed before qualification")
    record = api("issues/comments/" + str(B1_COMMENT))
    body = record.get("body", "")
    if not all(
        part in body
        for part in (
            "FOUNDER DECISION",
            "GATE B1 APPROVED",
            "transcription",
            "NOT permit scientific dispatch",
            "Return for a separate explicit Gate B2 authorization",
        )
    ):
        raise ValueError("documented bounded founder B1 consent absent")
    if record.get("issue_url") != native.REPOSITORY_API + "/issues/171":
        raise ValueError("B1 founder-comment issue mismatch")
    return {
        "issue": 171,
        "comment_id": B1_COMMENT,
        "provenance": "assistant_transcribed_chat_instruction",
        "direct_founder_github_signature": False,
        "scope": "UNARMED_ENGINEERING_ONLY",
    }


def validate_git(event: str, contract: dict[str, Any]) -> dict[str, Any]:
    actual = native.git("rev-parse", "HEAD")
    if actual != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("B1 wrong checkout SHA")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("B1 shallow local history")
    base = contract["authorized_base"]
    if native.git("rev-parse", base["sha"] + "^{tree}") != base["tree"]:
        raise ValueError("B1 base tree drift")
    if event == "pull_request":
        if native.git("merge-base", base["sha"], actual) != base["sha"]:
            raise ValueError("B1 candidate not from authorized base")
    else:
        parents = native.git("show", "-s", "--format=%P", actual).split()
        if len(parents) != 2 or parents[0] != B1_BASE:
            raise ValueError("B1 requires normal merge and exact original base")
    # Historical consumed Attempt-2 ancestry remains part of the science firewall.
    historical = readiness.read_contract(ROOT)["historical_attempts"][1]
    parents = native.git("show", "-s", "--format=%P", historical["canonical_main"]).split()
    if (
        parents != historical["merge_parents"]
        or native.git("rev-parse", historical["canonical_main"] + "^{tree}")
        != historical["canonical_tree"]
    ):
        raise ValueError("consumed Attempt-2 ordered parents/tree mismatch")
    return {"checkout_sha": actual, "baseline_sha": base["sha"]}


def validate_live(
    event: str,
    ancestry: dict[str, Any],
    *,
    api: Callable[..., Any] = native.api,
) -> dict[str, Any]:
    live = api("git/ref/heads/main")["object"]["sha"]
    checkout = ancestry["checkout_sha"]
    if event == "pull_request":
        if live != B1_BASE or os.environ.get("EXPECTED_BASE_SHA") != B1_BASE:
            raise ValueError("candidate B1 base changed")
        number = int(os.environ["PR_NUMBER"])
        pr = api("pulls/" + str(number))
        if (
            pr["head"]["sha"] != checkout
            or pr["base"]["sha"] != live
            or pr["state"] != "open"
            or pr["merged"] is True
        ):
            raise ValueError("B1 candidate PR exact-head/base/status mismatch")
    elif live != checkout:
        raise ValueError("B1 canonical main changed")
    else:
        matches = api("commits/" + checkout + "/pulls")
        qualified = [
            p
            for p in matches
            if (
                p.get("merged_at") is not None
                and p.get("merge_commit_sha") == checkout
                and p.get("base", {}).get("ref") == "main"
            )
        ]
        if len(qualified) != 1:
            raise ValueError("B1 canonical merged PR identity ambiguous")
        pr = api("pulls/" + str(qualified[0]["number"]))
        true_second_parent = native.git("show", "-s", "--format=%P", checkout).split()[1]
        if (
            pr.get("head", {}).get("sha") != true_second_parent
            or pr.get("merge_commit_sha") != checkout
        ):
            raise ValueError("B1 canonical normal-merge PR does not match")
    return {"phase": "candidate" if event == "pull_request" else "post-main", "live_main": live}


def qualify(root: Path = ROOT) -> dict[str, Any]:
    event = check_environment()
    contract = load_contract(root)
    local = check_policy(root, contract)
    simulation = FrozenAttempt3Controller(root, contract).rehearse()
    ancestry = validate_git(event, contract)
    # Existing proven GET-only context uses a deny-by-default HTTP mutation audit.
    with native.native_read_only_preflight() as request_audit:
        founder = verify_founder_record()
        live = validate_live(event, ancestry)
        history = readiness.check_history(root, readiness.read_contract(root))
    if any(req["method"] != "GET" for req in request_audit):
        raise ValueError("B1 native verifier must never mutate GitHub")
    return {
        "schema_version": SCHEMA,
        "engineering_qualification": "PASS",
        **local,
        **ancestry,
        **live,
        "founder": founder,
        "historical_runs": history,
        "synthetic_rehearsal": simulation,
        "request_audit": request_audit,
        "scientific_execution_authorization_sha256": None,
        "scientific_dispatches": 0,
        "model_http_posts": 0,
        "rows_replayed": 0,
        "permanent_scientific_claim": False,
        "final_content_access": False,
        "training": False,
        "d4": False,
        "r2": "BLOCKED",
        "founder_cost_usd": 0,
        "next_gate": "Separate explicit founder Gate B2 authorization",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="UNARMED B1 only; no scientific execution")
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
                "r2": "BLOCKED",
                "scientific_execution_authorization_sha256": None,
                "model_http_posts": 0,
                "rows_replayed": 0,
                "error_sha256": native.digest(str(exc)),
            },
        )
        raise SystemExit("Gate B1 qualification failed closed; SCIENCE NOT AUTHORIZED") from None
    native.write_exclusive(args.output, report)
    print("DAL_B1=PASS; ATTEMPT3_SCIENTIFIC_EXECUTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
