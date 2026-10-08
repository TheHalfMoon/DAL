"""Native read-only qualification of the unarmed Attempt-3 admission interface."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gaxbench.study1_attempt3_admission import (
    Attempt3AdmissionController,
    check_contract,
    load_contract,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))
import qualify_sg000031_attempt3_readiness as readiness  # noqa: E402
import study1_sg000031_r2_admission as native  # type: ignore  # noqa: E402

REQUIRED_AUTH_COMMENT = 6062562405
QUALIFICATION_SCHEMA = "dal-sg000031-attempt3-admission-qualification-v1"


def validate_event_environment() -> str:
    """Validate before reading credentials or making requests."""
    if os.environ.get("GITHUB_REPOSITORY") != native.REPOSITORY:
        raise ValueError("wrong admission repository")
    event = os.environ.get("GITHUB_EVENT_NAME")
    if event not in {"pull_request", "push"}:
        raise ValueError("scientific/manual event is forbidden")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise ValueError("workflow reruns cannot qualify an admission")
    if not os.environ.get("EXPECTED_CHECKOUT_SHA"):
        raise ValueError("missing exact checkout identity")
    return event


def check_local_ancestry(event: str, contract: dict[str, Any]) -> dict[str, Any]:
    head = native.git("rev-parse", "HEAD")
    if head != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("wrong exact checkout SHA")
    if native.git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("shallow ancestry cannot qualify")
    base = contract["engineering_base"]
    if native.git("rev-parse", base["sha"] + "^{tree}") != base["tree"]:
        raise ValueError("canonical engineering base tree drift")
    # The historical Attempt-2 normal merge must have actual ordered parents.
    historical = readiness.read_contract(ROOT)["historical_attempts"][1]
    parents = native.git("show", "-s", "--format=%P", historical["canonical_main"]).split()
    if parents != historical["merge_parents"]:
        raise ValueError("Attempt-2 history parent drift")
    if (
        native.git("rev-parse", historical["canonical_main"] + "^{tree}")
        != (historical["canonical_tree"])
    ):
        raise ValueError("Attempt-2 history tree drift")
    if event == "pull_request":
        if native.git("merge-base", base["sha"], head) != base["sha"]:
            raise ValueError("candidate not descended from authorized engineering base")
    else:
        # A native merge (not squash/rebase) with the canonical expected first parent.
        merge_parents = native.git("show", "-s", "--format=%P", head).split()
        if len(merge_parents) != 2 or merge_parents[0] != base["sha"]:
            raise ValueError("post-main normal-merge ancestry mismatch")
    return {"checkout_sha": head, "authorized_engineering_base": base["sha"]}


def check_founder_engineering_scope(
    api: Callable[..., Any] = native.api,
) -> dict[str, Any]:
    issue = api("issues/168")
    if issue.get("number") != 168 or issue.get("state") != "open":
        raise ValueError("engineering founder decision record absent or closed")
    record = api("issues/comments/" + str(REQUIRED_AUTH_COMMENT))
    body = record.get("body", "")
    if not all(
        marker in body
        for marker in (
            "FOUNDER DECISION",
            "OPTION A APPROVED",
            "transcribed from founder instruction",
            "scientific dispatch, model calls, row replay",
            "founder-cost requirement",
        )
    ):
        raise ValueError("recorded engineering authorization is incomplete")
    return {
        "issue": 168,
        "assistant_transcribed_comment_id": REQUIRED_AUTH_COMMENT,
        "original_authorship_independently_attested_on_github": False,
        "scope": "ENGINEERING_ONLY",
    }


def check_live_identity(
    event: str,
    ancestry: dict[str, Any],
    contract: dict[str, Any],
    *,
    api: Callable[..., Any] = native.api,
) -> dict[str, Any]:
    live_main = api("git/ref/heads/main")["object"]["sha"]
    checkout = ancestry["checkout_sha"]
    if event == "pull_request":
        base = contract["engineering_base"]["sha"]
        if live_main != base or os.environ.get("EXPECTED_BASE_SHA") != base:
            raise ValueError("PR base drift against live canonical main")
        number = int(os.environ["PR_NUMBER"])
        if number <= 0:
            raise ValueError("invalid PR number")
        pr = api("pulls/" + str(number))
        if pr["head"]["sha"] != checkout or pr["base"]["sha"] != live_main:
            raise ValueError("PR exact head/base changed")
    elif live_main != checkout:
        raise ValueError("post-main exact checkout mismatch")
    else:
        matches = api("commits/" + checkout + "/pulls")
        qualified = [
            pr
            for pr in matches
            if pr.get("merged_at") is not None
            and pr.get("merge_commit_sha") == checkout
            and pr.get("base", {}).get("ref") == "main"
        ]
        if len(qualified) != 1:
            raise ValueError("post-main merged PR association ambiguous")
        pr = api("pulls/" + str(qualified[0]["number"]))
        if (
            pr.get("merge_commit_sha") != checkout
            or pr.get("base", {}).get("ref") != "main"
            or pr.get("head", {}).get("sha")
            != native.git("show", "-s", "--format=%P", checkout).split()[1]
        ):
            raise ValueError("post-main guarded normal merge mismatch")
    return {
        "live_main": live_main,
        "phase": "candidate" if event == "pull_request" else "post-main",
    }


def qualify(root: Path = ROOT) -> dict[str, Any]:
    event = validate_event_environment()
    contract = load_contract(root)
    local = check_contract(root, contract)
    readiness.check_policy(root, readiness.read_contract(root))
    # Demonstrate executable admission rehearsal without taking a scientific action.
    rehearsal = Attempt3AdmissionController(contract).rehearse(root)
    ancestry = check_local_ancestry(event, contract)
    with native.native_read_only_preflight() as audit:
        auth = check_founder_engineering_scope()
        live = check_live_identity(event, ancestry, contract)
        history = readiness.check_history(root, readiness.read_contract(root))
    if any(item["method"] != "GET" for item in audit):
        raise ValueError("admission preflight attempted HTTP mutation")
    return {
        "schema_version": QUALIFICATION_SCHEMA,
        "engineering_qualification": "PASS",
        **local,
        **ancestry,
        **live,
        "founder_authorization": auth,
        "historical_runs": history,
        "synthetic_rehearsal": rehearsal,
        "read_only_http_requests": audit,
        "execution_authorization_sha256": None,
        "scientific_execution_authorized": False,
        "permanent_claim_created": False,
        "scientific_dispatches": 0,
        "model_posts": 0,
        "development_rows_replayed": 0,
        "final_content_access": False,
        "training_active": False,
        "d4_active": False,
        "r2_state": "BLOCKED",
        "founder_cost_usd": 0,
        "next_gate": "new, independent founder approval for one Attempt-3 scientific execution",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Unarmed Attempt-3 admission qualification only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = qualify()
    except Exception as exc:
        native.write_exclusive(
            args.output,
            {
                "schema_version": QUALIFICATION_SCHEMA,
                "engineering_qualification": "FAILED",
                "scientific_execution_authorized": False,
                "r2_state": "BLOCKED",
                "model_posts": 0,
                "error_sha256": native.digest(str(exc)),
            },
        )
        raise SystemExit("Attempt-3 admission failed closed; SCIENCE=NOT_AUTHORIZED") from None
    native.write_exclusive(args.output, report)
    print("ATTEMPT3_ENGINEERING_ADMISSION=PASS; SCIENCE=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
