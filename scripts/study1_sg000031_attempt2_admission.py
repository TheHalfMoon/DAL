"""Versioned Attempt-2 admission around unchanged scientific controls; no inference."""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

import study1_sg000031_r2_admission as legacy

CONTRACT_PATH = "registry/study1_sg000031_attempt2_admission_contract.json"
REPAIR_MAIN = "0e298850b3392eafedeacc995e36c1e15391a15c"
REPAIR_TREE = "ed53eaf2c6577ff76b88e453c87c2370969393d3"
EXECUTION_AUTH_SHA = "64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48"
ENGINEERING_AUTH_SHA = "8e0e2db1ddbe340a8fe53741fbfbffbed648ec857dd5bf4801a86ddf530fd08c"
REPAIR_RECORD_SHA = "3c481be6c23016c2a789d215fe65f12d19ec4f2f27b20e3c18164984f3cc30a4"
LINEAGE_SHA = "361dc916c5066c04c8c008ceb772442ebc54ebbbf0d412c817e9e7f9fc75eb3c"
INSPECTION_MARKER = "DAL_R2_ATTEMPT2_ALIBABA_INSPECTION_V1"
ATTEMPT_REF = "tags/dal-r2-issue158-attempt2"
LEDGER_BRANCH = "codex/sg000031-r2-attempt2-journal"
LEDGER_ROOT = "evidence/study1-r2-attempt2"
WORKFLOW = ".github/workflows/study1-sg000031-r2-attempt2.yml"
PREFLIGHT = ".github/workflows/study1-sg000031-attempt2-admission-preflight.yml"
MARKERS = {
    "candidate": "DAL_R2_ATTEMPT2_CANDIDATE_ADMISSION_V1",
    "post-merge": "DAL_R2_ATTEMPT2_POSTMERGE_PREFLIGHT_V1",
    "canonical": "DAL_R2_ATTEMPT2_CANONICAL_ADMISSION_V1",
}
PATHS = {
    "ci": ".github/workflows/gaxbench.yml",
    "manuscript": ".github/workflows/paper.yml",
    "alibaba": ".github/workflows/review-gates.yml",
    "jev": ".github/workflows/jev-review-target.yml",
    "sdk": ".github/workflows/study1-sg000031-sdk-qualification.yml",
    "repair_native": ".github/workflows/study1-sg000031-admission-preflight.yml",
    "native": PREFLIGHT,
}
SOURCE_PATHS = [
    "scripts/study1_sg000031_r2_admission.py",
    "scripts/study1_sg000031_attempt2_admission.py",
    "tools/qualify_sg000031_attempt2_admission.py",
    "tests/test_study1_sg000031_attempt2_admission.py",
    ".github/workflows/study1-sg000031-attempt2-admission-preflight.yml",
    WORKFLOW,
    ".github/workflows/study1-sg000031-r2-attempt2-worker.yml",
]


def git_bytes(*args):
    return subprocess.check_output(["git", *args])


def load_contract(root):
    scientific = legacy.verify_frozen_controls(root)
    contract = json.loads((root / CONTRACT_PATH).read_bytes())
    if (
        contract["schema_version"] != "study1-r2-attempt2-admission-contract-v1"
        or type(contract["attempt_ordinal"]) is not int
        or contract["attempt_ordinal"] != 2
        or type(contract["predecessor_attempt_ordinal"]) is not int
        or contract["predecessor_attempt_ordinal"] != 1
        or contract["execution_authorization_sha256"] != EXECUTION_AUTH_SHA
        or contract["engineering_authorization_sha256"] != ENGINEERING_AUTH_SHA
        or contract["canonical_r1"] != scientific["canonical_r1"]
        or contract["producer"] != scientific["producer"]
        or contract["development"] != scientific["development"]
        or contract["sealed_final"] != scientific["sealed_final"]
        or contract["repair_origin"]["main"] != REPAIR_MAIN
        or contract["repair_origin"]["tree"] != REPAIR_TREE
        or contract["repair_origin"]["qualification_sha256"] != REPAIR_RECORD_SHA
        or contract["admission_identity"]["permanent_attempt_ref"] != ATTEMPT_REF
        or contract["admission_identity"]["ledger_branch"] != LEDGER_BRANCH
        or contract["admission_identity"]["ledger_root"] != LEDGER_ROOT
        or contract["admission_identity"]["workflow"] != WORKFLOW
        or contract["admission_identity"]["contract_path"] != CONTRACT_PATH
        or contract["admission_identity"]["canonical_receipt_marker"] != MARKERS["canonical"]
        or contract["admission_identity"]["candidate_receipt_marker"] != MARKERS["candidate"]
        or contract["admission_identity"]["post_merge_receipt_marker"] != MARKERS["post-merge"]
        or contract["admission_identity"]["preflight_workflow"] != PREFLIGHT
        or contract["admission_identity"]["worker"]
        != ".github/workflows/study1-sg000031-r2-attempt2-worker.yml"
        or contract["attempt1"]["lineage_sha256"] != LINEAGE_SHA
        or contract["attempt1"]["run_id"] != 37320473498
        or contract["attempt1"]["workflow_run_attempt"] != 1
        or contract["attempt1"]["scientific_state"] != "BLOCKED"
        or contract["attempt1"]["first_turn_generations"] != 0
        or contract["attempt1"]["physical_model_POSTs"] != 0
        or contract["attempt1"]["unattempted_rows"] != 1463
        or contract["scientific_contract_path"] != "registry/study1_sg000031_r2_contract.json"
        or contract["protocol_path"] != "registry/study1_sg000029_recovery_protocol.json"
        or contract["attempt2_scientific_dispatches_per_authorization"] != 1
        or contract["automatic_retry"] is not False
        or contract["model_retry"] is not False
        or contract["engineering_scope_dispatch_allowed"] is not False
        or contract["stop_before_dispatch_after_canonical_qualification"] is not True
        or contract["execution_authorization_remains_unconsumed_during_qualification"] is not True
        or contract["founder_cost_usd"] != 0
        or contract["model_calls_during_qualification"] != 0
        or any(contract[key] is not False for key in ("final_access", "D4", "training", "scoring"))
    ):
        raise ValueError("Attempt-2 contract identity drift")
    for prefix in (
        "execution_authorization",
        "engineering_authorization",
        "scientific_contract",
        "protocol",
    ):
        if legacy.lf_digest(root / contract[prefix + "_path"]) != contract[prefix + "_sha256"]:
            raise ValueError("Attempt-2 authorization/scientific binding drift")
    for prefix, field in (
        ("execution_authorization", "verbatim_statement"),
        ("engineering_authorization", "verbatim_statement"),
    ):
        record = json.loads((root / contract[prefix + "_path"]).read_bytes())
        if legacy.digest(record[field]) != record["statement_utf8_lf_sha256"]:
            raise ValueError("Attempt-2 direct founder statement drift")
    repair = json.loads(
        (root / "registry/study1_sg000031_admission_repair_contract.json").read_bytes()
    )
    if contract["immutable_file_lf_sha256"] != repair["immutable_file_lf_sha256"]:
        raise ValueError("Attempt-2 immutable inventory drift")
    for path, expected in contract["immutable_file_lf_sha256"].items():
        if legacy.lf_digest(root / path) != expected:
            raise ValueError("Attempt-2 immutable predecessor/control drift")
    for path, expected in contract["attempt1"]["lineage_file_lf_sha256"].items():
        if legacy.lf_digest(root / path) != expected:
            raise ValueError("Attempt-1 lineage drift")
    if (
        legacy.digest(legacy.json_bytes(contract["attempt1"]["lineage_file_lf_sha256"]))
        != contract["attempt1"]["lineage_sha256"]
        or legacy.digest(legacy.json_bytes(contract["producer"]))
        != contract["producer_identity_sha256"]
        or legacy.lf_digest(root / contract["repair_origin"]["qualification_path"])
        != REPAIR_RECORD_SHA
    ):
        raise ValueError("Attempt-2 structural identity drift")
    return contract


def binding_fields(root, contract):
    return {
        "schema_version": "study1-r2-attempt2-admission-receipt-v1",
        "attempt_ordinal": 2,
        "predecessor_attempt_ordinal": 1,
        "contract_sha256": legacy.lf_digest(root / CONTRACT_PATH),
        "execution_authorization_sha256": EXECUTION_AUTH_SHA,
        "engineering_authorization_sha256": ENGINEERING_AUTH_SHA,
        "repair_main": REPAIR_MAIN,
        "repair_tree": REPAIR_TREE,
        "r1_manifest_sha256": contract["canonical_r1"]["manifest_sha256"],
        "producer_identity_sha256": contract["producer_identity_sha256"],
        "population_sha256": contract["development"]["question_role_assignments_sha256"],
        "attempt1_lineage_sha256": contract["attempt1"]["lineage_sha256"],
    }


def validate_receipt_identity(root, receipt, *, phase="canonical"):
    contract = load_contract(root)
    fields = binding_fields(root, contract)
    if set(receipt) != set(fields) | {
        "phase",
        "base_sha",
        "head_sha",
        "main_sha",
        "tree",
        "pull_request",
        "runs",
        "reviews",
    }:
        raise ValueError("Attempt-2 receipt structure mismatch")
    if receipt["phase"] != phase or receipt["base_sha"] != REPAIR_MAIN:
        raise ValueError("Attempt-2 receipt phase/base mismatch")
    for key, expected in fields.items():
        if type(receipt[key]) is not type(expected) or receipt[key] != expected:
            raise ValueError("Attempt-2 receipt binding drift: " + key)
    for key in ("head_sha", "tree"):
        if not isinstance(receipt[key], str) or not re.fullmatch(r"[0-9a-f]{40}", receipt[key]):
            raise ValueError("Attempt-2 receipt Git identity malformed")
    if type(receipt["pull_request"]) is not int or receipt["pull_request"] <= 0:
        raise ValueError("Attempt-2 receipt PR identity malformed")
    if phase == "candidate":
        if receipt["main_sha"] is not None:
            raise ValueError("candidate receipt cannot admit canonical execution")
    elif not isinstance(receipt["main_sha"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", receipt["main_sha"]
    ):
        raise ValueError("Attempt-2 receipt canonical main malformed")
    return contract


def parse_receipt(comment, *, phase="canonical"):
    if (
        comment["issue_url"] != legacy.REPOSITORY_API + "/issues/158"
        or comment["user"]["login"] != "TheHalfMoon"
    ):
        raise ValueError("Attempt-2 receipt source mismatch")
    body = comment["body"].replace("\r\n", "\n")
    if (
        not body.startswith(MARKERS[phase] + "\n")
        or body.count("```json\n") != 1
        or body.count("```") != 2
        or not body.rstrip().endswith("\n```")
    ):
        raise ValueError("Attempt-2 receipt format mismatch")

    def unique_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("ambiguous duplicate Attempt-2 receipt key")
            value[key] = item
        return value

    def reject_constant(_value):
        raise ValueError("non-finite Attempt-2 receipt JSON")

    return json.loads(
        body.split("```json\n", 1)[1].split("```", 1)[0],
        object_pairs_hook=unique_pairs,
        parse_constant=reject_constant,
    )


def inspection_identity(receipt):
    return {
        "base_sha": receipt["base_sha"],
        "head_sha": receipt["head_sha"],
        "run_id": receipt["runs"]["alibaba"],
        "report_sha256": receipt["reviews"]["alibaba"]["report_sha256"],
        "delegated_inspection_no_blocking_findings": True,
    }


def verify_inspection(receipt):
    review = receipt["reviews"]["alibaba"]
    comment_id = review["inspection_comment_id"]
    if type(comment_id) is not int or comment_id <= 0:
        raise ValueError("Alibaba inspection comment identity malformed")
    comment = legacy.api(f"issues/comments/{comment_id}")
    if (
        comment["issue_url"] != legacy.REPOSITORY_API + "/issues/158"
        or comment["user"]["login"] != "TheHalfMoon"
    ):
        raise ValueError("Alibaba delegated inspection source mismatch")
    body = comment["body"].replace("\r\n", "\n")
    if (
        not body.startswith(INSPECTION_MARKER + "\n")
        or body.count("```json\n") != 1
        or body.count("```") != 2
    ):
        raise ValueError("Alibaba delegated inspection receipt malformed")
    record = json.loads(body.split("```json\n", 1)[1].split("```", 1)[0])
    actual = legacy.artifact_documents(review, receipt["runs"]["alibaba"])["ocr-evidence.json"]
    expected = {**inspection_identity(receipt), "rules_sha256": actual["rules_sha256"]}
    if record != expected or any(
        type(record[key]) is not type(value) for key, value in expected.items()
    ):
        raise ValueError("Alibaba delegated inspection not bound to actual exact-head rules")


def artifact_report(review, run_id, filename):
    artifact = legacy.api(f"actions/artifacts/{int(review['artifact_id'])}")
    if artifact["expired"] or artifact["workflow_run"]["id"] != run_id:
        raise ValueError("Attempt-2 native artifact provenance mismatch")
    payload = legacy.api(f"actions/artifacts/{artifact['id']}/zip", raw=True)
    actual = "sha256:" + legacy.digest(payload)
    if artifact["digest"] != actual or review["artifact_digest"] != actual:
        raise ValueError("Attempt-2 native ZIP digest mismatch")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if Path(name).name == filename]
        if len(names) != 1 or archive.getinfo(names[0]).file_size > 5_000_000:
            raise ValueError("Attempt-2 native report boundary")
        content = archive.read(names[0])
    if legacy.digest(content) != review["report_sha256"]:
        raise ValueError("Attempt-2 native report digest mismatch")
    return json.loads(content)


def verify_predecessors(root, contract):
    # Historical receipt validation deliberately retains its original main and rules.
    legacy.qualify_canonical_receipt(
        root, 5995901646, "73e98360863aaa1cd039ffaa5cef2e4311dcfafa", live_main=False
    )
    comment = legacy.api("issues/comments/6004000110")
    if (
        comment["issue_url"] != legacy.REPOSITORY_API + "/issues/158"
        or comment["user"]["login"] != "TheHalfMoon"
    ):
        raise ValueError("canonical repair receipt source mismatch")
    body = comment["body"].replace("\r\n", "\n")
    if not body.startswith("DAL_R2_ADMISSION_REPAIR_CANONICAL_QUALIFICATION_V1\n"):
        raise ValueError("canonical repair receipt marker drift")
    repair = json.loads(body.split("```json\n", 1)[1].split("```", 1)[0])
    expected = json.loads((root / contract["repair_origin"]["qualification_path"]).read_bytes())
    if repair != expected:
        raise ValueError("canonical repair receipt identity drift")
    if legacy.git("show", "-s", "--format=%P", REPAIR_MAIN).split() != [
        repair["base_sha"],
        repair["head_sha"],
    ]:
        raise ValueError("canonical repair merge lineage drift")
    if legacy.git("rev-parse", REPAIR_MAIN + "^{tree}") != REPAIR_TREE:
        raise ValueError("canonical repair tree drift")
    failure = legacy.api("actions/runs/37320473498")
    if (
        failure["run_attempt"] != 1
        or failure["conclusion"] != "failure"
        or failure["head_sha"] != "73e98360863aaa1cd039ffaa5cef2e4311dcfafa"
    ):
        raise ValueError("retained Attempt-1 failure identity drift")


def verify_native(review, run_id, sha, *, phase=None):
    filename = (
        "attempt2-native-admission-preflight.json" if phase else "native-admission-preflight.json"
    )
    report = artifact_report(review, run_id, filename)
    if (
        report["checkout_sha"] != sha
        or report["engineering_preflight_state"] != "PASS"
        or report["R2_scientific_state"] != "BLOCKED"
    ):
        raise ValueError("Attempt-2 native preflight report mismatch")
    if (
        any(
            type(report[key]) is not int or report[key] != 0
            for key in ("physical_model_POSTs", "first_turn_generations", "final_rows_materialized")
        )
        or report["final_content_access"] is not False
        or report["new_execution_authorized"] is not False
        or report["founder_cost_usd"] != 0
        or report["REST_mutations_permitted"] is not False
    ):
        raise ValueError("native preflight must remain engineering-only")
    if phase and (
        type(report["attempt_ordinal"]) is not int
        or report["attempt_ordinal"] != 2
        or report["phase"] != phase
        or report["execution_authorization_unconsumed"] is not True
    ):
        raise ValueError("Attempt-2 native preflight phase mismatch")
    expected_sources = (
        SOURCE_PATHS
        if phase
        else [
            "scripts/study1_sg000031_r2_admission.py",
            "tools/qualify_sg000031_admission.py",
            "tests/test_study1_sg000031_admission_repair.py",
            ".github/workflows/study1-sg000031-admission-preflight.yml",
        ]
    )
    if set(report["source_lf_sha256"]) != set(expected_sources):
        raise ValueError("actual native source inventory incomplete")
    for path, expected in report["source_lf_sha256"].items():
        source = git_bytes("show", f"{sha}:{path}").replace(b"\r\n", b"\n")
        if legacy.digest(source) != expected:
            raise ValueError("actual native source provenance mismatch")
    return report


def verify_qualification(root, receipt, *, phase="canonical"):
    contract = validate_receipt_identity(root, receipt, phase=phase)
    repository = legacy.api("")
    if (
        repository["full_name"] != legacy.REPOSITORY
        or repository["url"] != legacy.REPOSITORY_API
        or repository["private"]
        or repository["default_branch"] != "main"
    ):
        raise ValueError("Attempt-2 requires exact public zero-cost repository")
    live = legacy.api("git/ref/heads/main")["object"]["sha"]
    head, main = receipt["head_sha"], receipt["main_sha"]
    if live != (REPAIR_MAIN if phase == "candidate" else main):
        raise ValueError("Attempt-2 live canonical main changed")
    if legacy.git("rev-parse", head + "^{tree}") != receipt["tree"]:
        raise ValueError("Attempt-2 intended head tree mismatch")
    if legacy.git("merge-base", REPAIR_MAIN, head) != REPAIR_MAIN:
        raise ValueError("Attempt-2 repair-origin ancestry mismatch")
    pr = legacy.api(f"pulls/{receipt['pull_request']}")
    if pr["head"]["sha"] != head:
        raise ValueError("Attempt-2 exact PR head changed")
    if phase == "candidate":
        if pr["merged"] or pr["state"] != "open" or pr["base"]["sha"] != REPAIR_MAIN:
            raise ValueError("Attempt-2 candidate PR state mismatch")
    elif (
        not pr["merged"]
        or pr["merge_commit_sha"] != main
        or legacy.git("show", "-s", "--format=%P", main).split() != [REPAIR_MAIN, head]
        or legacy.git("rev-parse", main + "^{tree}") != receipt["tree"]
    ):
        raise ValueError("Attempt-2 normal expected-head merge required")
    verify_predecessors(root, contract)
    required = {"ci", "manuscript", "alibaba", "jev", "sdk", "repair_native"}
    reviews = {"jev", "alibaba", "sdk", "repair_native"}
    if phase != "candidate":
        required |= {"pre_native", "post_ci", "post_manuscript", "post_sdk", "post_repair_native"}
        reviews |= {"pre_native", "post_sdk", "post_repair_native"}
    if phase == "canonical":
        required.add("post_native")
        reviews.add("post_native")
    if set(receipt["runs"]) != required or set(receipt["reviews"]) != reviews:
        raise ValueError("Attempt-2 full qualification inventory mismatch")
    for key in required:
        run_id = receipt["runs"][key]
        if type(run_id) is not int or run_id <= 0:
            raise ValueError("Attempt-2 workflow identity malformed")
        short = key.removeprefix("post_").removeprefix("pre_")
        sha = main if key.startswith("post_") else head
        legacy.verify_run(run_id, PATHS[short], sha, matrix=short == "ci")
    units = legacy.verify_reports(receipt)
    verify_inspection(receipt)
    expected_sdk = json.loads(
        (root / "registry/study1_sg000031_sdk_qualification.json").read_bytes()
    )
    for key in ("sdk", "post_sdk") if phase != "candidate" else ("sdk",):
        docs = legacy.artifact_documents(receipt["reviews"][key], receipt["runs"][key])
        if docs["sdk-qualification.json"] != expected_sdk:
            raise ValueError("Attempt-2 frozen synthetic SDK report drift")
    verify_native(receipt["reviews"]["repair_native"], receipt["runs"]["repair_native"], head)
    if phase != "candidate":
        verify_native(
            receipt["reviews"]["pre_native"], receipt["runs"]["pre_native"], head, phase="candidate"
        )
        verify_native(
            receipt["reviews"]["post_repair_native"], receipt["runs"]["post_repair_native"], main
        )
    if phase == "canonical":
        verify_native(
            receipt["reviews"]["post_native"],
            receipt["runs"]["post_native"],
            main,
            phase="post-merge",
        )
    request = legacy.authenticated_request(
        "https://api.github.com/graphql",
        {"query": legacy.REVIEW_THREADS_QUERY, "variables": {"number": receipt["pull_request"]}},
    )
    threads = legacy.native_http(request, review_query=True)["data"]["repository"]["pullRequest"][
        "reviewThreads"
    ]
    if threads["pageInfo"]["hasNextPage"] or any(
        not row["isResolved"] and not row["isOutdated"] for row in threads["nodes"]
    ):
        raise ValueError("Attempt-2 active unresolved review threads")
    return receipt, units


def qualify_canonical_receipt(root, comment_id, main):
    receipt = parse_receipt(legacy.api(f"issues/comments/{int(comment_id)}"))
    if receipt["main_sha"] != main:
        raise ValueError("Attempt-2 canonical receipt main binding drift")
    return verify_qualification(root, receipt)


def execution_history():
    name = WORKFLOW.rsplit("/", 1)[1]
    history = legacy.api(f"actions/workflows/{name}/runs?per_page=100")
    if history["total_count"] != len(history["workflow_runs"]):
        raise ValueError("Attempt-2 execution history incomplete")
    return history["workflow_runs"]


def admit(root, comment_id, output):
    legacy.environment_guard()
    if os.environ["GITHUB_EVENT_NAME"] != "workflow_dispatch" or legacy.WORKFLOW != WORKFLOW:
        raise ValueError("Attempt-2 main-only manual admission required")
    run_id = int(os.environ["GITHUB_RUN_ID"])
    history = execution_history()
    # Dispatch, including a failed pre-claim dispatch, consumes this authorization.
    if (
        len(history) != 1
        or history[0]["id"] != run_id
        or history[0]["path"] != WORKFLOW
        or history[0]["run_attempt"] != 1
    ):
        raise ValueError("Attempt-2 dispatch already consumed or wrong workflow")
    main = os.environ["GITHUB_SHA"]
    receipt, units = qualify_canonical_receipt(root, comment_id, main)
    contract = load_contract(root)
    claim = {
        "schema_version": "study1-r2-attempt2-claim-v1",
        "attempt_ordinal": 2,
        "predecessor_attempt_ordinal": 1,
        "run_id": run_id,
        "run_attempt": 1,
        "main_sha": main,
        "tree": receipt["tree"],
        "qualification_comment_id": int(comment_id),
        "qualification_receipt": receipt,
        "qualification_receipt_sha256": legacy.digest(legacy.json_bytes(receipt)),
        "contract_sha256": legacy.lf_digest(root / CONTRACT_PATH),
        "execution_authorization_sha256": EXECUTION_AUTH_SHA,
        "attempt1_lineage_sha256": contract["attempt1"]["lineage_sha256"],
        "engineering_qualified": True,
        "zero_cost_infrastructure_verified": True,
        "jev_review_units": units,
        "ledger_branch": LEDGER_BRANCH,
        "ledger_root": LEDGER_ROOT,
    }
    tag = legacy.api(
        "git/tags",
        {
            "tag": ATTEMPT_REF.removeprefix("tags/"),
            "message": legacy.json_bytes(claim).decode(),
            "object": main,
            "type": "commit",
        },
    )
    legacy.api("git/refs", {"ref": "refs/" + ATTEMPT_REF, "sha": tag["sha"]})
    claim["claim_sha"] = tag["sha"]
    legacy.write_exclusive(output / "admission.json", claim)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"claim_sha={tag['sha']}\nclaimed=true\n")
    legacy.api("git/refs", {"ref": "refs/heads/" + LEDGER_BRANCH, "sha": main})
    print("R2_ATTEMPT_ORDINAL=2; SINGLE_ATTEMPT_CLAIMED=true")


def verify_claim(claim_sha):
    legacy.environment_guard()
    root = Path.cwd()
    contract = load_contract(root)
    if legacy.api("")["private"]:
        raise ValueError("Attempt-2 requires zero-cost public repository")
    if legacy.api(f"git/ref/{ATTEMPT_REF}")["object"]["sha"] != claim_sha:
        raise ValueError("Attempt-2 permanent claim identity mismatch")
    claim = json.loads(legacy.api(f"git/tags/{claim_sha}")["message"])
    if (
        claim["schema_version"] != "study1-r2-attempt2-claim-v1"
        or type(claim["attempt_ordinal"]) is not int
        or claim["attempt_ordinal"] != 2
        or type(claim["predecessor_attempt_ordinal"]) is not int
        or claim["predecessor_attempt_ordinal"] != 1
        or type(claim["run_id"]) is not int
        or type(claim["run_attempt"]) is not int
        or claim["run_id"] != int(os.environ["GITHUB_RUN_ID"])
        or claim["run_attempt"] != 1
        or claim["main_sha"] != os.environ["GITHUB_SHA"]
        or claim["contract_sha256"] != legacy.lf_digest(root / CONTRACT_PATH)
        or claim["execution_authorization_sha256"] != EXECUTION_AUTH_SHA
        or claim["attempt1_lineage_sha256"] != contract["attempt1"]["lineage_sha256"]
        or claim["ledger_branch"] != LEDGER_BRANCH
        or claim["ledger_root"] != LEDGER_ROOT
        or claim["engineering_qualified"] is not True
        or claim["zero_cost_infrastructure_verified"] is not True
        or legacy.digest(legacy.json_bytes(claim["qualification_receipt"]))
        != claim["qualification_receipt_sha256"]
    ):
        raise ValueError("Attempt-2 claim is not bound to exact run/main/authorization")
    receipt = claim["qualification_receipt"]
    validate_receipt_identity(root, receipt)
    if receipt["main_sha"] != claim["main_sha"] or receipt["tree"] != claim["tree"]:
        raise ValueError("Attempt-2 claim receipt identity drift")
    if legacy.git("rev-parse", claim["main_sha"] + "^{tree}") != claim["tree"] or legacy.git(
        "show", "-s", "--format=%P", claim["main_sha"]
    ).split() != [REPAIR_MAIN, receipt["head_sha"]]:
        raise ValueError("Attempt-2 claim normal merge/tree mismatch")
    if legacy.api("git/ref/heads/main")["object"]["sha"] != claim["main_sha"]:
        raise ValueError("Attempt-2 live main changed after claim")
    history = execution_history()
    if len(history) != 1 or history[0]["id"] != claim["run_id"] or history[0]["run_attempt"] != 1:
        raise ValueError("Attempt-2 retry or additional dispatch forbidden")
    return claim
