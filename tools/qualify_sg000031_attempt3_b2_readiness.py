"""Read-only prospective B2 founder progression and infrastructure qualifier."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from gaxbench.study1_attempt3_b2_readiness import (
    BASE_MAIN,
    BASE_TREE,
    capacity_diagnostic,
    verify_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import qualify_sg000031_attempt3_b1 as b1_qual  # noqa: E402
import study1_sg000031_r2_admission as native  # type: ignore  # noqa: E402

SCHEMA = "dal-sg000031-b2-readonly-progression-native-v1"
APPROVAL_COMMENT = 6069470401
CLAIM_REF_PATH = "git/ref/tags/dal-r2-issue166-attempt3"


def verify_git_main_binding(event: str, expected_head: str) -> dict[str, Any]:
    if native.git("rev-parse", "HEAD") != expected_head:
        raise ValueError("wrong exact-head checkout")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("full merge ancestry required")
    if native.git("rev-parse", BASE_MAIN + "^{tree}") != BASE_TREE:
        raise ValueError("B1 qualified engineering tree drift")
    live = native.api("git/ref/heads/main")["object"]["sha"]
    if event == "pull_request":
        if live != BASE_MAIN or os.environ.get("EXPECTED_BASE_SHA") != BASE_MAIN:
            raise ValueError("new B2 candidate must be based on B1 canonical main")
        if native.git("merge-base", BASE_MAIN, expected_head) != BASE_MAIN:
            raise ValueError("B2 ancestry mismatch")
        pr = native.api("pulls/" + str(int(os.environ["PR_NUMBER"])))
        if (
            pr["state"] != "open"
            or pr["head"]["sha"] != expected_head
            or pr["base"]["sha"] != live
            or pr["merged"] is not False
        ):
            raise ValueError("B2 candidate head/base PR mismatch")
        return {"phase": "candidate", "live_main": live}
    parents = native.git("show", "-s", "--format=%P", expected_head).split()
    if len(parents) != 2 or parents[0] != BASE_MAIN or live != expected_head:
        raise ValueError("B2 engineering can only qualify guarded normal merge")
    if native.git("rev-parse", expected_head + "^{tree}") != native.git(
        "rev-parse", parents[1] + "^{tree}"
    ):
        raise ValueError("merged tree mismatch")
    matches = native.api("commits/" + expected_head + "/pulls")
    matched = [
        p
        for p in matches
        if p.get("merged_at") is not None
        and p.get("merge_commit_sha") == expected_head
        and p.get("base", {}).get("ref") == "main"
    ]
    if len(matched) != 1:
        raise ValueError("normal merge identity ambiguous")
    pr = native.api("pulls/" + str(matched[0]["number"]))
    if (
        pr["merge_commit_sha"] != expected_head
        or pr["head"]["sha"] != parents[1]
        or pr["merged"] is not True
    ):
        raise ValueError("post-main PR ancestry drift")
    return {"phase": "post-main", "live_main": live}


def verify_chat_founder_decision() -> dict[str, Any]:
    issue = native.api("issues/171")
    gate = native.api("issues/175")
    if issue["state"] != "open" or gate["state"] != "open":
        raise ValueError("B2 governance issue state changed")
    text = native.api("issues/comments/" + str(APPROVAL_COMMENT))
    body = text.get("body", "")
    required = (
        '"i approve move on"',
        "assistant-written",
        "NOT",
        "cryptographic",
        "PRE_DISPATCH_BLOCKED",
    )
    if not all(s in body for s in required):
        raise ValueError("B2 founder approval transcript provenance missing")
    if text.get("issue_url") != native.REPOSITORY_API + "/issues/171":
        raise ValueError("B2 approval transcript wrong issue")
    return {
        "founder_direct_statement": "i approve move on",
        "comment_id": APPROVAL_COMMENT,
        "source": "assistant-transcribed-human-chat",
        "cryptographically_signed_execution_authorization": False,
    }


def assert_no_real_attempt3_claim() -> None:
    try:
        native.api(CLAIM_REF_PATH)
    except HTTPError as error:
        if error.code == 404:
            return
        raise
    raise PermissionError("real Attempt-3 claim exists; readiness STOP")


def runner_capacity_diagnostic() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT).free
    sysconf = getattr(os, "sysconf", None)
    if sysconf is None:
        available_memory = 0
    else:
        try:
            pages = int(sysconf("SC_AVPHYS_PAGES"))
            page_bytes = int(sysconf("SC_PAGE_SIZE"))
            available_memory = pages * page_bytes
        except (OSError, ValueError):
            available_memory = 0
    return capacity_diagnostic(
        available_memory_bytes=available_memory,
        available_disk_bytes=disk,
        pinned_model_verified=False,
        zero_paid_services=True,
    )


def qualify(root: Path = ROOT) -> dict[str, Any]:
    event = b1_qual.check_environment()
    c = verify_readiness(root)
    expected_head = os.environ["EXPECTED_CHECKOUT_SHA"]
    workflow = (root / ".github/workflows/study1-sg000031-attempt3-b2-readiness.yml").read_text(
        encoding="utf-8"
    )
    if not all(
        s in workflow
        for s in (
            "pull_request:",
            "push:",
            "persist-credentials: false",
            "qualify_sg000031_attempt3_b2_readiness.py",
        )
    ) or any(
        s in workflow
        for s in (
            "workflow_dispatch:",
            "workflow_call:",
            "contents: write",
            "repository_dispatch:",
            "schedule:",
        )
    ):
        raise PermissionError("B2 readiness workflow may not dispatch/write science")
    with native.native_read_only_preflight() as trace:
        founder = verify_chat_founder_decision()
        git_state = verify_git_main_binding(event, expected_head)
        assert_no_real_attempt3_claim()
    if any(req["method"] != "GET" for req in trace):
        raise PermissionError("B2 readiness must never mutate GitHub")
    capacity = runner_capacity_diagnostic()
    if (
        capacity["scientific_dispatch_allowed"]
        or c["execution_authority"]["one_real_attempt_allowed"]
    ):
        raise ValueError("unsigned Gate B2 cannot become dispatchable")
    return {
        "schema_version": SCHEMA,
        "engineering_qualification": "PASS",
        "execution_readiness": "BLOCKED_PENDING_SIGNED_TOKEN_AND_EMPIRICAL_CAPACITY",
        "exact_head": expected_head,
        **git_state,
        "founder": founder,
        "read_only_requests": trace,
        "protected_files": 43,
        "permanent_attempt3_claim_present": False,
        "capacity": capacity,
        "model_posts": 0,
        "rows_replayed": 0,
        "founder_cost_usd": 0,
        "scientific_execution_authority_sha256": None,
        "r2": "BLOCKED",
        "final": "SEALED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="B2 authorization/capacity read-only check")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = qualify()
    except Exception as err:
        native.write_exclusive(
            args.output,
            {
                "schema_version": SCHEMA,
                "engineering_qualification": "FAIL_CLOSED",
                "execution_readiness": "BLOCKED",
                "error_sha256": native.digest(str(err)),
                "scientific_execution_authority_sha256": None,
                "model_posts": 0,
                "rows_replayed": 0,
            },
        )
        raise SystemExit("B2 readiness failed closed; scientific execution forbidden") from None
    native.write_exclusive(args.output, report)
    print("B2_ENGINEERING=PASS; SIGNED_EXECUTION_TOKEN=ABSENT; SCIENCE=BLOCKED")


if __name__ == "__main__":
    main()
