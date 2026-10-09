"""Native read-only exact-head evidence for prospective B2 atomic claim protocol."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from gaxbench.study1_attempt3_b1 import lf_sha256
from gaxbench.study1_attempt3_b2_claim import (
    BASE_MAIN,
    BASE_TREE,
    rehearsal,
    verify_plan,
)
from gaxbench.study1_attempt3_b2_claim import (
    PATH as CONTRACT_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import qualify_sg000031_attempt3_b1 as b1_qual  # noqa: E402
import study1_sg000031_r2_admission as native  # type: ignore  # noqa: E402

SCHEMA = "dal-sg000031-attempt3-b2-claim-engineering-native-v1"
APPROVAL_COMMENT = 6069470401
REF_PATH = "git/ref/tags/dal-r2-issue166-attempt3"


def verify_workflow_envelope(workflow: str) -> None:
    """Fail closed on commented or unrecognized workflow triggers.

    This is a static defense-in-depth check, NOT evidence of a real native
    GitHub Actions run or permission to dispatch science.
    """
    import re

    if not isinstance(workflow, str) or "\t" in workflow:
        raise PermissionError("native workflow envelope invalid")
    lines = [
        line.rstrip()
        for line in workflow.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    required = (
        r"^on:$",
        r"^  pull_request:$",
        r"^  push:$",
        r"^permissions:$",
        r"^  contents: read$",
        r"^\s+persist-credentials: false$",
        r"^\s+[^#]*qualify_sg000031_attempt3_b2_claim\.py(?:\s|$)",
    )
    if not all(any(re.fullmatch(pattern, line) for line in lines) for pattern in required):
        raise PermissionError("native B2 workflow required structure not active")
    start = lines.index("on:")
    end = next(
        (n for n in range(start + 1, len(lines)) if not lines[n].startswith(" ")),
        len(lines),
    )
    events = [
        match.group(1)
        for line in lines[start + 1 : end]
        if (match := re.fullmatch(r"  ([a-z_]+):", line))
    ]
    if sorted(events) != ["pull_request", "push"]:
        raise PermissionError("native B2 workflow event scope expanded or invalid")
    forbidden = r"^\s*(?:workflow_dispatch|workflow_call|schedule|repository_dispatch):"
    writes = r"^\s*[a-z][a-z-]*: write$"
    unsafe_checkout = r"^\s*persist-credentials: (?!false$)\S+"
    if any(
        re.match(forbidden, line) or re.match(writes, line)
        or re.match(unsafe_checkout, line)
        for line in lines
    ):
        raise PermissionError("native B2 workflow writes or dispatches prohibited")


def verify_head(event: str, expected_head: str) -> dict[str, Any]:
    if native.git("rev-parse", "HEAD") != expected_head:
        raise ValueError("wrong exact-head checkout")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("requires genuine full Git ancestry")
    if native.git("rev-parse", BASE_MAIN + "^{tree}") != BASE_TREE:
        raise ValueError("prior certified read-only B2 merge tree changed")
    live = native.api("git/ref/heads/main")["object"]["sha"]
    if event == "pull_request":
        if live != BASE_MAIN or os.environ.get("EXPECTED_BASE_SHA") != BASE_MAIN:
            raise ValueError("B2 claim engineering base main moved")
        if native.git("merge-base", BASE_MAIN, expected_head) != BASE_MAIN:
            raise ValueError("candidate parent ancestry mismatch")
        pr = native.api("pulls/" + str(int(os.environ["PR_NUMBER"])))
        if (
            pr["state"] != "open"
            or pr["merged"] is not False
            or pr["head"]["sha"] != expected_head
            or pr["base"]["sha"] != live
        ):
            raise ValueError("PR exact-head/base mismatch")
        return {"phase": "candidate", "live_main": live}

    parents = native.git("show", "-s", "--format=%P", expected_head).split()
    if live != expected_head or len(parents) != 2 or parents[0] != BASE_MAIN:
        raise ValueError("must be exact-head main normal merge")
    if native.git("rev-parse", expected_head + "^{tree}") != native.git(
        "rev-parse", parents[1] + "^{tree}"
    ):
        raise ValueError("post-main source tree mismatch")
    merges = native.api("commits/" + expected_head + "/pulls")
    prs = [
        item
        for item in merges
        if item.get("merge_commit_sha") == expected_head
        and item.get("merged_at") is not None
        and item.get("base", {}).get("ref") == "main"
    ]
    if len(prs) != 1:
        raise ValueError("unique canonical PR merge required")
    pr = native.api("pulls/" + str(prs[0]["number"]))
    if (
        pr["merged"] is not True
        or pr["head"]["sha"] != parents[1]
        or pr["merge_commit_sha"] != expected_head
    ):
        raise ValueError("merged PR/candidate identity drift")
    return {"phase": "post-main", "live_main": live}


def check_real_ref_absent() -> None:
    try:
        native.api(REF_PATH)
    except HTTPError as error:
        if error.code == 404:
            return
        raise
    raise PermissionError("actual Attempt-3 scientific tag exists: fail closed")


def verify_founder_transcription() -> dict[str, Any]:
    gate = native.api("issues/175")
    if gate["state"] != "open":
        raise ValueError("scientific B2 engineering issue unexpectedly closed")
    comment = native.api("issues/comments/" + str(APPROVAL_COMMENT))
    body = comment.get("body", "")
    if (
        comment["issue_url"] != native.REPOSITORY_API + "/issues/171"
        or '"i approve move on"' not in body
        or "NOT" not in body
        or "assistant-written" not in body
    ):
        raise ValueError("ChatGPT consent record provenance drift")
    return {
        "comment_id": APPROVAL_COMMENT,
        "source": "assistant-chat-transcript-NOT-cryptographic-token",
        "cryptographically_verified": False,
    }


def qualify(root: Path = ROOT) -> dict[str, Any]:
    event = b1_qual.check_environment()
    plan = verify_plan(root)
    proof = rehearsal(root)
    if (
        proof["real_github_mutations"] != 0
        or proof["model_posts"] != 0
        or proof["rows_replayed"] != 0
        or not proof["duplicate_denied"]
        or not proof["synthetic_claim_consumed_once"]
    ):
        raise ValueError("nonisolated or incomplete fake GitHub atomic protocol")
    workflow = (root / ".github/workflows/study1-sg000031-attempt3-b2-claim.yml").read_text(
        encoding="utf-8"
    )
    verify_workflow_envelope(workflow)
    expected = os.environ["EXPECTED_CHECKOUT_SHA"]
    with native.native_read_only_preflight() as audit:
        founder = verify_founder_transcription()
        main = verify_head(event, expected)
        check_real_ref_absent()
    if any(item["method"] != "GET" for item in audit):
        raise PermissionError("live qualifier cannot mutate GitHub")
    return {
        "schema_version": SCHEMA,
        "engineering_qualification": "PASS",
        "scientific_execution": "BLOCKED_SIGNED_TOKEN_AND_EMPIRICAL_CAPACITY_MISSING",
        "exact_head": expected,
        **main,
        "founder_record": founder,
        "synthetic_proof": proof,
        "contract_sha256": lf_sha256(root / CONTRACT_PATH),
        "protected_original_files": 43,
        "git_http_audit": audit,
        "real_ref_exists": False,
        "real_github_mutations": 0,
        "real_model_posts": 0,
        "rows_replayed": 0,
        "final_role_access": False,
        "founder_cost_usd": 0,
        "r2": plan["scope"]["science"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Native B2 atomic claim read-only check")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = qualify()
    except Exception as exc:
        native.write_exclusive(
            args.output,
            {
                "schema_version": SCHEMA,
                "engineering_qualification": "FAIL_CLOSED",
                "error_sha256": native.digest(str(exc)),
                "scientific_execution": "BLOCKED",
                "real_github_mutations": 0,
                "real_model_posts": 0,
                "rows_replayed": 0,
            },
        )
        raise SystemExit("B2 claim engineering failed closed; no scientific execution") from None
    native.write_exclusive(args.output, result)
    print("B2_ATOMIC_PROTOCOL=QUALIFIED_SYNTHETIC_ONLY; SCIENCE=BLOCKED")


if __name__ == "__main__":
    main()
