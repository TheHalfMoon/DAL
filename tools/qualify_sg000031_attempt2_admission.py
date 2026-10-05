"""Actual native authenticated qualification; never dispatches, claims, plans or infers."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import study1_sg000031_attempt2_admission as grain  # noqa: E402
import study1_sg000031_r2_admission as native  # noqa: E402


def wait_runs(sha, keys, *, timeout=720):
    deadline = time.monotonic() + timeout
    current = int(os.environ.get("GITHUB_RUN_ID", "0"))
    while True:
        runs = native.api("actions/runs?per_page=100")["workflow_runs"]
        result = {}
        for key in keys:
            short = key.removeprefix("post_").removeprefix("pre_")
            matches = [
                run
                for run in runs
                if run["path"] == grain.PATHS[short]
                and run["head_sha"] == sha
                and run["id"] != current
            ]
            if not matches:
                continue
            latest = max(matches, key=lambda run: run["id"])
            if latest["status"] == "completed":
                if latest["conclusion"] != "success":
                    raise ValueError("exact-head engineering workflow failed: " + key)
                result[key] = latest["id"]
        if set(result) == set(keys):
            return result
        if time.monotonic() >= deadline:
            raise ValueError("exact-head engineering qualification still incomplete")
        # Read-only progress polling; never retries a workflow or model request.
        time.sleep(15)


def review(run_id, filename):
    artifacts = native.api(f"actions/runs/{run_id}/artifacts")
    if artifacts["total_count"] != 1 or len(artifacts["artifacts"]) != 1:
        raise ValueError("engineering artifact inventory incomplete")
    artifact = artifacts["artifacts"][0]
    # Read the actual ZIP to determine the report hash; verify it again in admission.
    payload = native.api(f"actions/artifacts/{artifact['id']}/zip", raw=True)
    if "sha256:" + native.digest(payload) != artifact["digest"] or artifact["expired"]:
        raise ValueError("actual engineering artifact ZIP identity mismatch")
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if Path(name).name == filename]
        if len(names) != 1 or archive.getinfo(names[0]).file_size > 5_000_000:
            raise ValueError("actual engineering report boundary")
        report = archive.read(names[0])
    return {
        "artifact_id": artifact["id"],
        "artifact_digest": artifact["digest"],
        "report_sha256": native.digest(report),
    }


def wait_inspection(receipt, *, timeout=720):
    """Require actual delegated inspection evidence; workflow success cannot assert it."""
    deadline = time.monotonic() + timeout
    while True:
        comments = native.api("issues/158/comments?per_page=100")
        matches = []
        expected = grain.inspection_identity(receipt)
        for comment in comments:
            if comment["user"]["login"] != "TheHalfMoon":
                continue
            body = comment["body"].replace("\r\n", "\n")
            if not body.startswith(grain.INSPECTION_MARKER + "\n"):
                continue
            try:
                record = json.loads(body.split("```json\n", 1)[1].split("```", 1)[0])
            except (ValueError, IndexError):
                continue
            if all(record.get(key) == value for key, value in expected.items()):
                matches.append(comment["id"])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError("ambiguous exact-head Alibaba inspection receipts")
        if time.monotonic() >= deadline:
            raise ValueError("actual exact-head Alibaba delegated inspection not retained")
        time.sleep(15)


def build_receipt(root, checkout, *, phase):
    contract = grain.load_contract(root)
    if phase == "candidate":
        number = int(os.environ["PR_NUMBER"])
        pr = native.api(f"pulls/{number}")
        head, main = checkout, None
    else:
        associations = native.api(f"commits/{checkout}/pulls")
        matches = [
            pr
            for pr in associations
            if pr["merged_at"] is not None and pr["merge_commit_sha"] == checkout
        ]
        if len(matches) != 1:
            raise ValueError("canonical normal merge PR identity ambiguous")
        number = matches[0]["number"]
        pr = native.api(f"pulls/{number}")
        head, main = pr["head"]["sha"], checkout
    if pr["head"]["sha"] != head:
        raise ValueError("exact qualification PR head mismatch")
    receipt = {
        **grain.binding_fields(root, contract),
        "phase": phase,
        "base_sha": grain.REPAIR_MAIN,
        "head_sha": head,
        "main_sha": main,
        "tree": native.git("rev-parse", head + "^{tree}"),
        "pull_request": number,
        "runs": wait_runs(head, ["ci", "manuscript", "alibaba", "jev", "sdk", "repair_native"]),
        "reviews": {},
    }
    filenames = {
        "jev": "jev-review.json",
        "alibaba": "ocr-evidence.json",
        "sdk": "sdk-qualification.json",
        "repair_native": "native-admission-preflight.json",
    }
    if phase != "candidate":
        receipt["runs"].update(wait_runs(head, ["pre_native"]))
        receipt["runs"].update(
            wait_runs(main, ["post_ci", "post_manuscript", "post_sdk", "post_repair_native"])
        )
        filenames.update(
            pre_native="attempt2-native-admission-preflight.json",
            post_sdk="sdk-qualification.json",
            post_repair_native="native-admission-preflight.json",
        )
    if phase == "canonical":
        receipt["runs"].update(wait_runs(main, ["post_native"]))
        filenames["post_native"] = "attempt2-native-admission-preflight.json"
    for key, filename in filenames.items():
        receipt["reviews"][key] = review(receipt["runs"][key], filename)
    receipt["reviews"]["alibaba"]["inspection_comment_id"] = wait_inspection(receipt)
    grain.verify_inspection(receipt)
    receipt["reviews"]["alibaba"]["delegated_inspection_no_blocking_findings"] = True
    return receipt


def prove_unconsumed(*, phase):
    original = native.api("actions/workflows/study1-sg000031-r2-recovery.yml/runs?per_page=100")
    if original["total_count"] != 1 or len(original["workflow_runs"]) != 1:
        raise ValueError("scientific dispatch history changed during qualification")
    first = original["workflow_runs"][0]
    if first["id"] != 37320473498 or first["run_attempt"] != 1 or first["conclusion"] != "failure":
        raise ValueError("immutable Attempt-1 workflow history drift")
    try:
        history = grain.execution_history()
    except HTTPError as error:
        if error.code != 404 or phase != "candidate":
            raise
        # A dispatch-only workflow not yet on default main cannot be dispatched.
        return {
            "attempt2_canonical_workflow_registered": False,
            "attempt2_scientific_dispatches": 0,
        }
    if history:
        raise ValueError("Attempt-2 authorization consumed by scientific dispatch")
    return {"attempt2_canonical_workflow_registered": True, "attempt2_scientific_dispatches": 0}


def qualify(root, *, comment_id=None):
    if os.environ["GITHUB_REPOSITORY"] != native.REPOSITORY or native.ATTEMPT_ORDINAL != "2":
        raise ValueError("Attempt-2 native qualification context mismatch")
    checkout = native.git("rev-parse", "HEAD")
    if checkout != os.environ["EXPECTED_CHECKOUT_SHA"]:
        raise ValueError("Attempt-2 native checkout identity mismatch")
    event = os.environ["GITHUB_EVENT_NAME"]
    if event not in {"pull_request", "push", "workflow_dispatch"}:
        raise ValueError("Attempt-2 qualification event unsupported")
    with native.native_read_only_preflight() as audit:
        if event == "workflow_dispatch":
            if not comment_id or os.environ["GITHUB_REF"] != "refs/heads/main":
                raise ValueError("canonical receipt verification requires main and comment")
            phase = "canonical"
            receipt, units = grain.qualify_canonical_receipt(root, comment_id, checkout)
        else:
            phase = "candidate" if event == "pull_request" else "post-merge"
            receipt = build_receipt(root, checkout, phase=phase)
            receipt, units = grain.verify_qualification(root, receipt, phase=phase)
        history = prove_unconsumed(phase=phase)
        live_main = native.api("git/ref/heads/main")["object"]["sha"]
    contract = grain.load_contract(root)
    report = {
        "schema_version": "study1-r2-attempt2-native-preflight-v1",
        "attempt_ordinal": 2,
        "phase": phase,
        "engineering_preflight_state": "PASS",
        "R2_scientific_state": "BLOCKED",
        "checkout_sha": checkout,
        "live_main_observed": live_main,
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
        "receipt": receipt,
        "receipt_identity_sha256": native.digest(native.json_bytes(receipt)),
        "contract_sha256": native.lf_digest(root / grain.CONTRACT_PATH),
        "execution_authorization_sha256": grain.EXECUTION_AUTH_SHA,
        "engineering_authorization_sha256": grain.ENGINEERING_AUTH_SHA,
        "attempt1_lineage_sha256": contract["attempt1"]["lineage_sha256"],
        "immutable_files_verified": len(contract["immutable_file_lf_sha256"]),
        "genuine_jev_review_units_verified": units,
        "native_requests": audit,
        "authentication_context": (
            "same workflow github.token/GH_TOKEN, native headers/opener and read-only guard"
        ),
        "source_lf_sha256": {p: native.lf_digest(root / p) for p in grain.SOURCE_PATHS},
        "scientific_runner_unchanged": True,
        "frozen_synthetic_SDK_unchanged": True,
        "REST_mutations_permitted": False,
        "claim_created": False,
        "ledger_created": False,
        "benchmark_downloaded": False,
        "first_turn_generations": 0,
        "physical_model_POSTs": 0,
        "final_rows_materialized": 0,
        "final_content_access": False,
        "execution_authorization_unconsumed": True,
        "new_execution_authorized": False,
        "D4": False,
        "founder_cost_usd": 0,
        **history,
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--comment-id", type=int)
    args = parser.parse_args()
    try:
        report = qualify(ROOT, comment_id=args.comment_id)
    except Exception as error:
        native.write_exclusive(
            args.output,
            {
                "engineering_preflight_state": "FAILED",
                "R2_scientific_state": "BLOCKED",
                "error_sha256": native.digest(str(error)),
                "new_execution_authorized": False,
                "physical_model_POSTs": 0,
            },
        )
        raise SystemExit(
            "Attempt-2 engineering qualification failed; no dispatch or model call authorized"
        ) from None
    native.write_exclusive(args.output, report)
    print("ATTEMPT2_NATIVE_PREFLIGHT=PASS; SCIENTIFIC_DISPATCHES=0; R2=BLOCKED")


if __name__ == "__main__":
    main()
