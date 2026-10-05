"""Main-only admission and permanent single-attempt claim. No model integration here."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import subprocess
import zipfile
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from gaxbench.study1_recovery_execution import (
    ATTEMPT_REF,
    CONTRACT_PATH,
    POPULATION_SHA256,
    R1_MAIN,
    digest,
    json_bytes,
    lf_digest,
    planned_rows,
    population_digest,
    verify_frozen_controls,
    write_exclusive,
)

WORKFLOW = ".github/workflows/study1-sg000031-r2-recovery.yml"
REPOSITORY = "TheHalfMoon/DAL"
LEDGER_BRANCH = "codex/sg000031-r2-attempt1-journal"
LEDGER_ROOT = "evidence/study1-r2-attempt1"
REPOSITORY_API = f"https://api.github.com/repos/{REPOSITORY}"
_PREFLIGHT_AUDIT = ContextVar("r2_native_preflight_audit", default=None)
REVIEW_THREADS_QUERY = (
    'query($number:Int!){repository(owner:"TheHalfMoon",name:"DAL"){'
    "pullRequest(number:$number){reviewThreads(first:100){"
    "pageInfo{hasNextPage}nodes{isResolved isOutdated}}}}}"
)


def repository_url(path):
    """Canonicalize the repository root; reject ambiguous input before credentials or I/O."""
    if not isinstance(path, str) or any(
        ord(char) <= 32 or ord(char) >= 127 or char in "\\%#" for char in path
    ):
        raise ValueError("invalid repository URL characters")
    if path.startswith("https://"):
        parsed = urlsplit(path)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise ValueError("GitHub API authority mismatch")
        boundary = f"/repos/{REPOSITORY}"
        if parsed.path in {boundary, boundary + "/"}:
            suffix = ""
        elif parsed.path.startswith(boundary + "/"):
            suffix = parsed.path[len(boundary) + 1 :]
        else:
            raise ValueError("GitHub API repository boundary")
        query = parsed.query
    else:
        if path.startswith("/") or ":" in path:
            raise ValueError("absolute or ambiguous repository path")
        suffix, separator, query = path.partition("?")
        if not separator:
            query = ""
    if suffix and any(
        not re.fullmatch(r"[A-Za-z0-9_.-]+", segment) or segment in {".", ".."}
        for segment in suffix.split("/")
    ):
        raise ValueError("noncanonical repository path")
    if "?" in path and not query:
        raise ValueError("empty repository query")
    if query and (
        not suffix
        or not re.fullmatch(r"per_page=[1-9][0-9]{0,2}", query)
        or int(query.split("=", 1)[1]) > 100
    ):
        raise ValueError("noncanonical repository query")
    return REPOSITORY_API + ("/" + suffix if suffix else "") + ("?" + query if query else "")


@contextmanager
def native_read_only_preflight():
    """Record canonical request metadata and prohibit all REST mutations before transport."""
    audit = []
    token = _PREFLIGHT_AUDIT.set(audit)
    try:
        yield audit
    finally:
        _PREFLIGHT_AUDIT.reset(token)


class StripCrossHostAuthorization(HTTPRedirectHandler):
    def redirect_request(self, request, *args, **kwargs):
        redirected = super().redirect_request(request, *args, **kwargs)
        if redirected is not None:
            target = urlsplit(redirected.full_url)
            if (
                target.scheme != "https"
                or target.username is not None
                or target.password is not None
                or target.port is not None
                or target.fragment
                or not re.fullmatch(r"[A-Za-z0-9.-]+", target.netloc)
            ):
                raise ValueError("unsafe admission HTTP redirect")
            if target.hostname == "api.github.com":
                repository_url(redirected.full_url)
        if (
            redirected is not None
            and urlsplit(redirected.full_url).netloc != urlsplit(request.full_url).netloc
        ):
            redirected.remove_header("Authorization")
        return redirected


def authenticated_request(url, value=None, method=None):
    return Request(
        url,
        data=json_bytes(value) if value is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DAL-R2-admission",
        },
    )


def native_http(request, *, raw=False, review_query=False):
    audit = _PREFLIGHT_AUDIT.get()
    if review_query:
        body = json.loads(request.data)
        if (
            request.full_url != "https://api.github.com/graphql"
            or request.get_method() != "POST"
            or set(body) != {"query", "variables"}
            or body["query"] != REVIEW_THREADS_QUERY
            or set(body["variables"]) != {"number"}
            or type(body["variables"]["number"]) is not int
            or body["variables"]["number"] <= 0
        ):
            raise ValueError("native preflight permits only the fixed read-only review query")
    if (
        audit is not None
        and (request.get_method() != "GET" or request.data is not None)
        and not review_query
    ):
        raise ValueError("native preflight forbids mutation")
    with build_opener(StripCrossHostAuthorization()).open(request, timeout=60) as response:
        payload = response.read()
        if audit is not None:
            audit.append(
                {
                    "method": request.get_method(),
                    "url": request.full_url,
                    "status": response.status,
                    "response_sha256": digest(payload),
                    "authentication": "GH_TOKEN-bearer",
                    "read_only_review_query": review_query,
                }
            )
    return payload if raw else json.loads(payload)


def api(path, value=None, *, raw=False, method=None):
    url = repository_url(path)
    request = authenticated_request(url, value, method)
    return native_http(request, raw=raw)


def ledger_write(relative, value, previous_sha=None):
    if relative != "plan.json" and not (
        relative.startswith("rows/")
        and relative.endswith(".json")
        and len(relative) == 74
        and all(c in "0123456789abcdef" for c in relative[5:-5])
    ):
        raise ValueError("durable ledger path outside hash-only allowlist")
    data = {
        "message": "Retain R2 single-attempt hash-only checkpoint",
        "branch": LEDGER_BRANCH,
        "content": base64.b64encode(json_bytes(value)).decode(),
    }
    if previous_sha is not None:
        data["sha"] = previous_sha
    result = api(f"contents/{LEDGER_ROOT}/{relative}", data, method="PUT")
    return result["content"]["sha"]


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def environment_guard():
    if (
        os.environ["GITHUB_REPOSITORY"] != REPOSITORY
        or os.environ["GITHUB_REF"] != "refs/heads/main"
        or os.environ["GITHUB_RUN_ATTEMPT"] != "1"
    ):
        raise ValueError("main-only first-run admission required")
    if git("rev-parse", "HEAD") != os.environ["GITHUB_SHA"]:
        raise ValueError("checkout identity mismatch")


def verify_run(run_id, path, sha=None, *, matrix=False):
    run = api(f"actions/runs/{int(run_id)}")
    if run["path"] != path or run["status"] != "completed" or run["conclusion"] != "success":
        raise ValueError("canonical workflow qualification incomplete")
    if sha is not None and run["head_sha"] != sha:
        raise ValueError("workflow head binding mismatch")
    jobs = api(f"actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    if not jobs or any(job["conclusion"] != "success" for job in jobs):
        raise ValueError("qualification jobs incomplete")
    if matrix:
        expected = {
            (platform, version)
            for platform in ("ubuntu-latest", "windows-latest")
            for version in ("3.11", "3.12")
        }
        observed = {
            (platform, version)
            for platform, version in expected
            if any(platform in job["name"] and version in job["name"] for job in jobs)
        }
        if observed != expected or len(jobs) != 4:
            raise ValueError("4/4 CI matrix required")
        for job in jobs:
            steps = [
                step
                for step in job["steps"]
                if any(
                    name in step["name"].lower() for name in ("ruff", "mypy", "pytest", "compile")
                )
            ]
            if len(steps) < 4 or any(step["conclusion"] != "success" for step in steps):
                raise ValueError("matrix required steps incomplete")
    if path == ".github/workflows/paper.yml":
        if not any(
            "arxiv" in step["name"].lower() and step["conclusion"] == "success"
            for job in jobs
            for step in job["steps"]
        ):
            raise ValueError("standalone arXiv manuscript compilation required")
    return run


def artifact_documents(review, run_id):
    artifact = api(f"actions/artifacts/{int(review['artifact_id'])}")
    if artifact["expired"] or artifact["workflow_run"]["id"] != run_id:
        raise ValueError("review artifact provenance mismatch")
    payload = api(f"actions/artifacts/{artifact['id']}/zip", raw=True)
    actual = "sha256:" + hashlib.sha256(payload).hexdigest()
    if artifact["digest"] != actual or review["artifact_digest"] != actual:
        raise ValueError("review artifact digest mismatch")
    archive = zipfile.ZipFile(io.BytesIO(payload))
    documents = {}
    for name in archive.namelist():
        if name.endswith(
            (
                "jev-review.json",
                "ocr-evidence.json",
                "ocr-preview.json",
                "ocr-rules.json",
                "sdk-qualification.json",
            )
        ):
            key = Path(name).name
            if key in documents:
                raise ValueError("duplicate review report")
            content = archive.read(name)
            documents[key] = json.loads(content)
            if key in {"jev-review.json", "ocr-evidence.json", "sdk-qualification.json"}:
                if digest(content) != review["report_sha256"]:
                    raise ValueError("actual report digest mismatch")
    return documents


def verify_reports(receipt):
    base, head = receipt["base_sha"], receipt["head_sha"]
    changed = git("diff", "--name-only", base, head).splitlines()
    expected = {}
    for path in changed:
        patch = subprocess.check_output(
            ["git", "diff", "--no-ext-diff", "--no-color", "--unified=3", base, head, "--", path],
            text=True,
        )
        lines = patch.split("\n")
        start = next(i for i, line in enumerate(lines) if line.startswith("@@ "))
        header = "\n".join(lines[:start])
        hunks = []
        for line in lines[start:]:
            if line.startswith("@@ "):
                hunks.append([line])
            else:
                hunks[-1].append(line)
        units = []
        for index, hunk in enumerate(hunks, 1):
            content = header + "\n" + "\n".join(hunk)
            count = math.ceil((len(content.encode("utf-16-le")) // 2) / 6000)
            units.extend((index, fragment, count) for fragment in range(1, count + 1))
        expected[path] = units
    reviews = receipt["reviews"]
    jev = artifact_documents(reviews["jev"], receipt["runs"]["jev"])["jev-review.json"]
    if (
        (jev["base_sha"], jev["head_sha"]) != (base, head)
        or jev["status"] != "PASSED"
        or jev["blocking_findings"]
        or jev["coverage"]["complete"] is not True
    ):
        raise ValueError("genuine exact-head Jev review incomplete")
    if {file["path"] for file in jev["changed_files"]} != set(changed):
        raise ValueError("Jev file coverage mismatch")
    for path, units in expected.items():
        judgments = [item for item in jev["hunk_judgments"] if item["file"] == path]
        if [(item["hunk"], item["fragment"], item["fragments"]) for item in judgments] != units:
            raise ValueError("Jev independent review-unit coverage mismatch")
    total = sum(len(units) for units in expected.values())
    if (
        jev["coverage"]["expected_hunks"] != total
        or jev["coverage"]["reviewed_hunks"] != total
        or len(jev["hunk_judgments"]) != total
    ):
        raise ValueError("Jev total coverage mismatch")
    ocr_docs = artifact_documents(reviews["alibaba"], receipt["runs"]["alibaba"])
    ocr, preview, rules = (
        ocr_docs[name] for name in ("ocr-evidence.json", "ocr-preview.json", "ocr-rules.json")
    )
    if (
        (ocr["base_sha"], ocr["head_sha"]) != (base, head)
        or ocr["tool"] != "alibaba/open-code-review@v1.12.9"
        or ocr["mode"] != "delegation-accounting"
        or (preview["from"], preview["to"], preview["merge_base"]) != (base, head, base)
        or reviews["alibaba"]["delegated_inspection_no_blocking_findings"] is not True
    ):
        raise ValueError("Alibaba exact-range delegated review incomplete")
    reviewable = [item["path"] for item in preview["reviewable_files"]]
    excluded = [item["path"] for item in preview["excluded_files"]]
    if (
        set(reviewable).intersection(excluded)
        or set(reviewable + excluded) != set(changed)
        or ocr["reviewable_files"] != reviewable
        or {path for group in rules["groups"] for path in group["files"]} != set(reviewable)
    ):
        raise ValueError("Alibaba coverage mismatch")
    if digest(json.dumps(rules, sort_keys=True, separators=(",", ":"))) != ocr["rules_sha256"]:
        raise ValueError("Alibaba actual rules digest mismatch")
    return total


def qualify_canonical_receipt(root, comment_id, main, *, live_main=True):
    """Shared native read-only admission validation. Only admit() can claim an attempt."""
    contract = verify_frozen_controls(root)
    repository = api("")
    if (
        repository["full_name"] != REPOSITORY
        or repository["url"] != REPOSITORY_API
        or repository["private"]
        or repository["default_branch"] != "main"
    ):
        raise ValueError("public zero-cost repository required")
    comment = api(f"issues/comments/{int(comment_id)}")
    if (
        comment["issue_url"] != REPOSITORY_API + "/issues/158"
        or comment["user"]["login"] != "TheHalfMoon"
    ):
        raise ValueError("canonical qualification receipt source mismatch")
    body = comment["body"].replace("\r\n", "\n")
    if not body.startswith("DAL_R2_CANONICAL_QUALIFICATION_V1\n") or body.count("```json\n") != 1:
        raise ValueError("canonical receipt format mismatch")
    receipt = json.loads(body.split("```json\n", 1)[1].split("```", 1)[0])
    if (
        receipt["main_sha"] != main
        or receipt["base_sha"] != R1_MAIN
        or receipt["contract_sha256"] != lf_digest(root / CONTRACT_PATH)
        or receipt["authorization_record_sha256"] != contract["authorization_record_sha256"]
    ):
        raise ValueError("canonical receipt binding drift")
    if live_main and api("git/ref/heads/main")["object"]["sha"] != main:
        raise ValueError("live canonical main changed")
    parents = git("show", "-s", "--format=%P", main).split()
    if parents != [receipt["base_sha"], receipt["head_sha"]]:
        raise ValueError("normal expected-head merge required")
    tree = git("rev-parse", f"{main}^{{tree}}")
    if tree != receipt["tree"] or tree != git("rev-parse", f"{receipt['head_sha']}^{{tree}}"):
        raise ValueError("intended merge tree mismatch")
    pr = api(f"pulls/{int(receipt['pull_request'])}")
    if (
        not pr["merged"]
        or pr["merge_commit_sha"] != main
        or pr["head"]["sha"] != receipt["head_sha"]
    ):
        raise ValueError("qualified pull request merge mismatch")
    for key, path in (
        ("ci", ".github/workflows/gaxbench.yml"),
        ("manuscript", ".github/workflows/paper.yml"),
        ("alibaba", ".github/workflows/review-gates.yml"),
        ("jev", ".github/workflows/jev-review-target.yml"),
        ("post_ci", ".github/workflows/gaxbench.yml"),
        ("post_manuscript", ".github/workflows/paper.yml"),
        ("sdk", ".github/workflows/study1-sg000031-sdk-qualification.yml"),
        ("post_sdk", ".github/workflows/study1-sg000031-sdk-qualification.yml"),
    ):
        sha = main if key.startswith("post_") else receipt["head_sha"]
        verify_run(
            receipt["runs"][key],
            path,
            None if key == "jev" else sha,
            matrix=key in {"ci", "post_ci"},
        )
    units = verify_reports(receipt)
    expected_sdk = json.loads(
        (root / "registry/study1_sg000031_sdk_qualification.json").read_bytes()
    )
    for key in ("sdk", "post_sdk"):
        sdk = artifact_documents(receipt["reviews"][key], receipt["runs"][key])
        if sdk["sdk-qualification.json"] != expected_sdk:
            raise ValueError("actual canonical synthetic SDK report mismatch")
    request = authenticated_request(
        "https://api.github.com/graphql",
        {"query": REVIEW_THREADS_QUERY, "variables": {"number": int(receipt["pull_request"])}},
    )
    data = native_http(request, review_query=True)
    threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]
    if threads["pageInfo"]["hasNextPage"] or any(
        not item["isResolved"] and not item["isOutdated"] for item in threads["nodes"]
    ):
        raise ValueError("active unresolved review threads")
    return receipt, tree, units


def admit(root, comment_id, output):
    environment_guard()
    if os.environ["GITHUB_EVENT_NAME"] != "workflow_dispatch":
        raise ValueError("manual dispatch only")
    run = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}")
    if run["path"] != WORKFLOW:
        raise ValueError("R2 entrypoint mismatch")
    main = os.environ["GITHUB_SHA"]
    receipt, tree, units = qualify_canonical_receipt(root, comment_id, main)
    claim = {
        "schema_version": "study1-r2-attempt-claim-v1",
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "run_attempt": 1,
        "main_sha": main,
        "tree": tree,
        "qualification_comment_id": int(comment_id),
        "qualification_receipt": receipt,
        "contract_sha256": lf_digest(root / CONTRACT_PATH),
        "engineering_qualified": True,
        "zero_cost_infrastructure_verified": True,
        "jev_review_units": units,
        "ledger_branch": LEDGER_BRANCH,
        "ledger_root": LEDGER_ROOT,
    }
    # Atomic ref creation, never update/delete. An existing claim rejects every subsequent run.
    tag = api(
        "git/tags",
        {
            "tag": ATTEMPT_REF.removeprefix("tags/"),
            "message": json_bytes(claim).decode(),
            "object": main,
            "type": "commit",
        },
    )
    api("git/refs", {"ref": "refs/" + ATTEMPT_REF, "sha": tag["sha"]})
    claim["claim_sha"] = tag["sha"]
    write_exclusive(output / "admission.json", claim)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"claim_sha={tag['sha']}\nclaimed=true\n")
    api("git/refs", {"ref": "refs/heads/" + LEDGER_BRANCH, "sha": main})
    print("R2_SINGLE_ATTEMPT_CLAIMED=true")


def verify_claim(claim_sha):
    environment_guard()
    verify_frozen_controls(Path.cwd())
    if api("")["private"]:
        raise ValueError("zero-cost public repository required")
    ref = api(f"git/ref/{ATTEMPT_REF}")
    if ref["object"]["sha"] != claim_sha:
        raise ValueError("permanent attempt identity mismatch")
    claim = json.loads(api(f"git/tags/{claim_sha}")["message"])
    if (
        claim["run_id"] != int(os.environ["GITHUB_RUN_ID"])
        or claim["main_sha"] != os.environ["GITHUB_SHA"]
        or claim["run_attempt"] != 1
        or claim["contract_sha256"] != lf_digest(Path(CONTRACT_PATH))
        or claim["engineering_qualified"] is not True
        or claim["zero_cost_infrastructure_verified"] is not True
    ):
        raise ValueError("attempt is not admitted for this exact run and checkout")
    return claim


def plan(output):
    from gaxbench.fhir_agentbench_qualification import FHIR_AGENTBENCH_RAW_URL
    from gaxbench.study1_query_trace_gate import build_development_trace_inputs

    source = output.parent / "source.csv"
    try:
        with urlopen(
            Request(FHIR_AGENTBENCH_RAW_URL, headers={"User-Agent": "DAL-R2"}), timeout=60
        ) as response:
            source.write_bytes(response.read())
        inputs, audit, _ = build_development_trace_inputs(source, shard_index=0, shard_count=1)
        rows = planned_rows(inputs)
        if (
            len(rows) != 1463
            or population_digest(rows) != POPULATION_SHA256
            or sum(row.role == "calibration" for row in rows) != 341
            or sum(row.role == "validation" for row in rows) != 1122
        ):
            raise ValueError("exact historical development population required")
        value = {
            "custodian_audit": audit.model_dump(mode="json"),
            "rows": [row.model_dump(mode="json") for row in rows],
        }
        write_exclusive(output / "plan.json", value)
        ledger_write("plan.json", value)
    finally:
        source.unlink(missing_ok=True)
    print("R2_PLANNED_DEVELOPMENT_ROWS=1463")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["admit", "plan", "verify"])
    parser.add_argument("--comment-id")
    parser.add_argument("--claim-sha")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "admit":
            admit(Path.cwd(), args.comment_id, args.output_dir)
        elif args.mode == "plan":
            verify_claim(args.claim_sha)
            plan(args.output_dir)
        else:
            verify_claim(args.claim_sha)
            print("R2_EXACT_RUN_CLAIM_VERIFIED=true")
    except Exception as error:
        write_exclusive(
            args.output_dir / f"{args.mode}-failure.json",
            {
                "state": "BLOCKED",
                "code": "r2-infrastructure-or-admission-failed-stop",
                "error_sha256": digest(str(error)),
                "run_id": os.environ.get("GITHUB_RUN_ID"),
                "new_founder_decision_before_new_model_attempt": True,
            },
        )
        raise SystemExit(
            "R2 admission/infrastructure failure retained; no model retry authorized"
        ) from None


if __name__ == "__main__":
    main()
