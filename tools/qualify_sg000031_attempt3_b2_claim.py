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
    )
    if not all(any(re.fullmatch(pattern, line) for line in lines) for pattern in required):
        raise PermissionError("native B2 workflow required structure not active")
    # An unreviewed top-level key can materially alter native execution
    # (e.g. a global env or concurrency cancel), despite safe-looking steps.
    # Use only the minimal workflow surface in the approved native template.
    top_level = [line for line in lines if not line.startswith(" ")]
    allowed_top = {"on:", "permissions:", "jobs:"}
    if any(
        line not in allowed_top
        and not re.fullmatch(r"name: [A-Za-z0-9 _-]+", line)
        for line in top_level
    ):
        raise PermissionError("unreviewed B2 top-level workflow setting prohibited")
    if sum(line.startswith("name: ") for line in top_level) > 1:
        raise PermissionError("duplicate B2 top-level name prohibited")
    # Restrict permission scope to a single top-level minimal read-only block.
    # This is a conservative static guard, not a YAML parser or a native run receipt.
    if any(lines.count(top) != 1 for top in ("on:", "permissions:", "jobs:")):
        raise PermissionError("native B2 workflow duplicate or missing top-level block")
    if any(line.lstrip().startswith("permissions:") and line != "permissions:" for line in lines):
        raise PermissionError("native B2 workflow permissions override prohibited")
    permission_start = lines.index("permissions:")
    permission_end = next(
        (n for n in range(permission_start + 1, len(lines)) if not lines[n].startswith(" ")),
        len(lines),
    )
    permission_lines = lines[permission_start + 1 : permission_end]
    allowed_scopes = {"  contents: read", "  issues: read", "  pull-requests: read"}
    if len(permission_lines) != len(allowed_scopes) or set(permission_lines) != allowed_scopes:
        raise PermissionError("native B2 workflow permissions require exact GET-only read scopes")
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
    unexpected_events = [
        line for line in lines[start + 1 : end]
        if line.startswith("  ") and not line.startswith("    ")
        and line not in ("  pull_request:", "  push:")
    ]
    if sorted(events) != ["pull_request", "push"] or unexpected_events:
        raise PermissionError("native B2 workflow event scope expanded or invalid")

    # Both events must be restricted to main and the approved B2 source set.
    allowed_paths = {
        ".github/workflows/study1-sg000031-attempt3-b2-claim.yml",
        "docs/study1-sg000031-attempt3-b2-claim.md",
        "registry/study1_sg000031_attempt3_b2_claim_engineering_contract.json",
        "src/gaxbench/study1_attempt3_b2_claim.py",
        "tests/test_study1_sg000031_attempt3_b2_claim.py",
        "tests/test_study1_sg000031_attempt3_b2_claim_native.py",
        "tools/qualify_sg000031_attempt3_b2_claim.py",
    }
    for event_name in ("pull_request", "push"):
        first = lines.index("  " + event_name + ":")
        last = next(
            (i for i in range(first + 1, end) if lines[i].startswith("  ")
             and not lines[i].startswith("    ")),
            end,
        )
        details = lines[first + 1 : last]
        if details[:2] != ["    branches: [main]", "    paths:"]:
            raise PermissionError("B2 events require scoped main and paths")
        paths = [line.removeprefix("      - ") for line in details[2:]]
        if (
            not paths or len(paths) != len(set(paths))
            or any(line != "      - " + path for line, path in zip(details[2:], paths, strict=True))
            or set(paths) != allowed_paths
            or ".github/workflows/study1-sg000031-attempt3-b2-claim.yml" not in paths
        ):
            raise PermissionError("B2 events contain unapproved paths")
    forbidden = r"^\s*(?:workflow_dispatch|workflow_call|schedule|repository_dispatch):"
    writes = r"\b[a-z][a-z-]*:\s*write(?:\s|[,}]|$)"
    write_all = r"^\s*permissions:\s*write-all(?:\s|$)"
    unsafe_checkout = r"^\s*persist-credentials: (?!false$)\S+"
    disabled = r"^\s*(?:- )?(?:if|continue-on-error):"
    if any(re.match(disabled, line) for line in lines):
        raise PermissionError("conditional or failure-tolerant B2 verification prohibited")
    if any(
        re.match(forbidden, line)
        or re.search(writes, line)
        or re.match(write_all, line)
        or re.match(unsafe_checkout, line)
        for line in lines
    ):
        raise PermissionError("native B2 workflow writes or dispatches prohibited")

    # Do not allow an unreviewed job, a paid/private runner, a container,
    # or YAML merges to change the meaning of the checked steps.
    jobs_start = lines.index("jobs:")
    jobs_end = next(
        (n for n in range(jobs_start + 1, len(lines))
         if not lines[n].startswith(" ")),
        len(lines),
    )
    job_lines = lines[jobs_start + 1 : jobs_end]
    job_headers = [line for line in job_lines if re.fullmatch(r"  [a-z][\w-]*:", line)]
    if len(job_headers) != 1:
        raise PermissionError("B2 requires exactly one verification job")
    # Explicitly reject alternate job strategies, dependencies, environments,
    # and all other unreviewed job-level keys. Such keys could suppress native
    # qualification while leaving superficially correct run-command text.
    approved_job_keys = {"name", "runs-on", "timeout-minutes", "steps", "env"}
    job_settings = [
        line.strip() for line in job_lines
        if line.startswith("    ") and not line.startswith("      ")
    ]
    setting_keys = [line.split(":", 1)[0] for line in job_settings]
    if any(key not in approved_job_keys for key in setting_keys):
        raise PermissionError("unreviewed B2 job setting prohibited")
    if len(setting_keys) != len(set(setting_keys)):
        raise PermissionError("duplicate B2 job setting prohibited")
    if "timeout-minutes" in setting_keys and "timeout-minutes: 25" not in job_settings:
        raise PermissionError("B2 job timeout must be 25 minutes")
    if job_lines.count("    steps:") != 1:
        raise PermissionError("B2 requires exactly one active steps list")
    steps_position = job_lines.index("    steps:")
    for index, line in enumerate(job_lines):
        if not line.startswith("      - "):
            continue
        if index <= steps_position:
            raise PermissionError("B2 step outside steps list")
        section = job_lines[steps_position + 1 : index]
        if any(
            previous.startswith("    ") and not previous.startswith("      ")
            for previous in section
        ):
            raise PermissionError("B2 step detached from steps list")
    if sum(line.strip() == "runs-on: ubuntu-latest" for line in job_lines) != 1:
        raise PermissionError("B2 requires a single GitHub-hosted Ubuntu runner")
    if any(
        re.match(r"^\s+runs-on:", line) and line.strip() != "runs-on: ubuntu-latest"
        for line in lines
    ):
        raise PermissionError("unexpected B2 job runner")
    if any(
        re.match(r"^\s*(?:container|services|shell|working-directory|defaults):", line)
        or line.strip().startswith("<<:")
        or re.search(r"(?<!\$)(?:^|\s)[&*][A-Za-z_][A-Za-z_0-9-]*", line)
        for line in lines
    ):
        raise PermissionError("workflow container, shell, YAML alias or overrides prohibited")

    # Only the native read-only preflight variables may be exported. This is
    # a static restriction in addition to the independent GitHub runner check.
    allowed_env = {
        "GH_TOKEN": "${{ github.token }}",
        "EXPECTED_CHECKOUT_SHA": "${{ github.event.pull_request.head.sha || github.sha }}",
        "EXPECTED_BASE_SHA": "${{ github.event.pull_request.base.sha }}",
        "PR_NUMBER": "${{ github.event.pull_request.number }}",
    }
    for index, line in enumerate(lines):
        if line.strip() != "env:":
            continue
        indent = len(line) - len(line.lstrip(" "))
        entries = []
        for following in lines[index + 1 :]:
            depth = len(following) - len(following.lstrip(" "))
            if depth <= indent:
                break
            if depth != indent + 2:
                raise PermissionError("B2 environment nesting not allowed")
            entries.append(following.strip())
        if not entries or len(entries) != len(set(entries)) or any(
            ":" not in entry
            or entry.split(":", 1)[0] not in allowed_env
            or entry.split(":", 1)[1].strip()
            != allowed_env[entry.split(":", 1)[0]]
            for entry in entries
        ):
            raise PermissionError("unapproved B2 workflow environment variables")

    # Bind the checkout hardening to the actual pinned checkout action, not an
    # unrelated step's YAML. This remains static defense, not an execution proof.
    # The native workflow is limited to independently reviewed first-party
    # actions. A SHA alone does not make an arbitrary action safe.
    approved_actions = {
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    }
    uses = [line for line in lines if re.match(r"^\s+(?:- )?uses:", line)]
    if any(
        not re.fullmatch(r"^\s+(?:- )?uses: ([^\s]+)$", line)
        or line.strip().removeprefix("- uses: ") not in approved_actions
        for line in uses
    ):
        raise PermissionError("GitHub Actions must be independently pinned and approved")
    checkout = [
        (index, re.match(r"^(\s*)- uses: actions/checkout@[0-9a-f]{40}$", line))
        for index, line in enumerate(lines)
    ]
    checkout = [(index, match) for index, match in checkout if match]
    if len(checkout) != 1:
        raise PermissionError("single SHA-pinned checkout step required")
    position, checkout_match = checkout[0]
    assert checkout_match is not None
    step_indent = len(checkout_match.group(1))
    step_lines: list[str] = []
    for line in lines[position + 1 :]:
        if len(line) - len(line.lstrip(" ")) <= step_indent:
            break
        step_lines.append(line)
    approved_checkout = {
        "with:",
        "fetch-depth: 0",
        "persist-credentials: false",
        "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
    }
    for required_checkout in (
        "with:",
        "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
        "fetch-depth: 0",
        "persist-credentials: false",
    ):
        if sum(line.strip() == required_checkout for line in step_lines) != 1:
            raise PermissionError("checkout missing required exact-head security settings")
    if any(line.strip() not in approved_checkout for line in step_lines):
        raise PermissionError("checkout source or configuration not authorized")

    # Confirm the qualifier is an executable run command, not a step name or
    # `echo` text. Support both inline and folded YAML command syntax.
    run_commands: list[str] = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"^(?:      - run:|        run:) (.+)$", line)
        if not match:
            continue
        if line.startswith("        run:"):
            preceding_step = next(
                (previous for previous in reversed(lines[:index])
                 if re.match(r"^      - ", previous)),
                "",
            )
            if not preceding_step.startswith("      - name:"):
                raise PermissionError("native qualifier must be a real named run step")
        value = match.group(1)
        if value in (">", ">-", "|", "|-"):
            indent = len(line) - len(line.lstrip(" "))
            folded = []
            for following in lines[index + 1 :]:
                if len(following) - len(following.lstrip(" ")) <= indent:
                    break
                folded.append(following.strip())
            value = " ".join(folded)
        run_commands.append(value)
    # Never pass command substitution, variable expansion, or shell operators
    # through the receipt path. The runner temp expansion is the only permitted
    # variable reference, and only in this exact quoted form.
    receipt = r'(?:[A-Za-z0-9_.-]+\.json|"\$RUNNER_TEMP/[A-Za-z0-9_.-]+\.json")'
    qualifier = re.compile(
        r'^python tools/qualify_sg000031_attempt3_b2_claim\.py '
        rf'--output {receipt}$'
    )
    if sum(bool(qualifier.fullmatch(command)) for command in run_commands) != 1:
        raise PermissionError("exactly one executable B2 native qualifier command required")
    # Only synthetic tests, dependency installation, and the read-only native
    # qualifier may be shell steps. Any other shell step is out of scope.
    test_path = r"tests/(?:[A-Za-z0-9_-]+/)*test_[A-Za-z0-9_-]+\.py"
    safe = re.compile(
        r"(?:python -m pip install -e ['\"]?\.\[dev\]['\"]?|"
        rf"python -m pytest -q(?:\s+{test_path})+)"
    )
    if any(not qualifier.fullmatch(command) and not safe.fullmatch(command)
           for command in run_commands):
        raise PermissionError("non-allowlisted shell command in native B2 workflow")
    # The authentic native job must actually run both synthetic claim and
    # founder-signature/ref-denial regression suites before qualification.
    # Merely allowing test commands is insufficient: the prior envelope
    # accepted a qualifier-only job and skipped all of these security tests.
    required_suites = {
        "tests/test_study1_sg000031_attempt3_b2_claim.py",
        "tests/test_study1_sg000031_attempt3_b2_claim_native.py",
    }
    executed_suites = {
        path
        for command in run_commands
        if command.startswith("python -m pytest -q ")
        for path in command.split()[4:]
    }
    if not required_suites.issubset(executed_suites):
        raise PermissionError("native B2 workflow must run both synthetic security suites")


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
