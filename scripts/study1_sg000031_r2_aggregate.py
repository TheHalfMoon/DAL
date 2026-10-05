"""Retain the entire denominator and classify R2 separately from immutable SG-000028."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from study1_sg000031_r2_admission import LEDGER_BRANCH, LEDGER_ROOT, api, verify_claim

from gaxbench.study1_query_trace_gate import DevelopmentTraceAudit
from gaxbench.study1_recovery_execution import (
    R2Row,
    classify_rows,
    digest,
    read_journal,
    write_exclusive,
)


def git_bytes(*args):
    return subprocess.check_output(["git", *args])


def execution_jobs_successful(jobs):
    required = [
        "Qualify and permanently claim the sole R2 attempt",
        *(f"Frozen R2 shard {shard}" for shard in range(8)),
    ]
    for name in required:
        matching = [
            job for job in jobs if job["name"] == name or job["name"].endswith(" / " + name)
        ]
        if (
            len(matching) != 1
            or matching[0]["status"] != "completed"
            or matching[0]["conclusion"] != "success"
        ):
            return False
    return True


def pending_canonical_finalization(report):
    # This job cannot prove its own eventual upload success or canonical evidence closeout.
    return {
        **report,
        "candidate_scientific_state": report["scientific_state"],
        "scientific_state": "BLOCKED",
        "canonical_execution_finalization_complete": False,
        "canonical_PASS_requires_successful_whole_run_and_qualified_closeout": True,
    }


def aggregate(args):
    claim = verify_claim(args.claim_sha)
    ref = f"refs/remotes/origin/{LEDGER_BRANCH}"
    plan_bytes = git_bytes("show", f"{ref}:{LEDGER_ROOT}/plan.json")
    plan = json.loads(plan_bytes)
    custody = DevelopmentTraceAudit.model_validate(plan["custodian_audit"])
    rows = [R2Row.model_validate(row) for row in plan["rows"]]
    if custody.selected_rows != 1463 or any(row.status != "not-attempted" for row in rows):
        raise ValueError("invalid full-population plan")
    latest = {row.question_id_sha256: row for row in rows}
    ledger_files = (
        git_bytes("ls-tree", "-r", "--name-only", ref, "--", f"{LEDGER_ROOT}/rows")
        .decode()
        .splitlines()
    )
    remote_rows = {}
    for path in ledger_files:
        content = git_bytes("show", f"{ref}:{path}")
        row = R2Row.model_validate_json(content)
        key = row.question_id_sha256
        if (
            path != f"{LEDGER_ROOT}/rows/{key}.json"
            or key not in latest
            or row.role != latest[key].role
            or row.input_sha256 != latest[key].input_sha256
            or key in remote_rows
        ):
            raise ValueError("durable ledger identity drift")
        remote_rows[key] = row
        latest[key] = row
    execution_jobs = api(f"actions/runs/{os.environ['GITHUB_RUN_ID']}/jobs?per_page=100")["jobs"]
    interrupted = not execution_jobs_successful(execution_jobs)
    journal_digests = {}
    for shard in range(8):
        expected = [row for row in rows if int(row.question_id_sha256[:16], 16) % 8 == shard]
        journals = list(args.input_dir.rglob(f"shard-{shard}-journal.jsonl"))
        audits = list(args.input_dir.rglob(f"shard-{shard}-audit.json"))
        jobs = list(args.input_dir.rglob(f"shard-{shard}-job-status.json"))
        if len(journals) > 1 or len(audits) > 1 or len(jobs) > 1:
            raise ValueError("duplicate shard evidence")
        if jobs:
            job = json.loads(jobs[0].read_bytes())
            if (
                job["run_id"] != os.environ["GITHUB_RUN_ID"]
                or job["main_sha"] != os.environ["GITHUB_SHA"]
                or job["shard"] != shard
            ):
                raise ValueError("shard job evidence identity drift")
        if not jobs or job["job_status"] != "success":
            interrupted = True
        if not journals:
            interrupted = True
            continue
        journal = journals[0]
        observed = read_journal(journal, expected)
        journal_digests[str(shard)] = digest(journal.read_bytes())
        if not audits:
            interrupted = True
        else:
            audit = json.loads(audits[0].read_bytes())
            DevelopmentTraceAudit.model_validate(audit["custodian_audit"])
            if (
                audit["claim_sha"] != args.claim_sha
                or audit["main_sha"] != os.environ["GITHUB_SHA"]
                or audit["run_id"] != int(os.environ["GITHUB_RUN_ID"])
                or audit["journal_sha256"] != journal_digests[str(shard)]
            ):
                raise ValueError("shard provenance or journal digest drift")
            interrupted |= audit["interrupted"]
        for key, row in observed.items():
            if row.status in {"pass", "behavior-changing-blocker"}:
                if key not in remote_rows or remote_rows[key].model_dump() != row.model_dump():
                    interrupted = True
            if row.generation_attempts > latest[key].generation_attempts:
                latest[key] = row
            elif row.status in {"pass", "behavior-changing-blocker"}:
                latest[key] = row
    ordered = [latest[row.question_id_sha256] for row in rows]
    report = classify_rows(
        ordered, engineering_qualified=claim["engineering_qualified"], interrupted=interrupted
    )
    report = pending_canonical_finalization(report)
    source = json.loads(Path("registry/study1_sg000028_execution_37156028113.json").read_bytes())
    report.update(
        {
            "attempt_claim": claim,
            "ledger_commit": git_bytes("rev-parse", ref).decode().strip(),
            "plan_sha256": digest(plan_bytes),
            "journal_sha256s": journal_digests,
            "execution_job_conclusions": [
                {key: job[key] for key in ("id", "name", "status", "conclusion")}
                for job in execution_jobs
            ],
            "historical_pattern_sha256s": sorted(
                entry["source_pattern_sha256"] for entry in source["pattern_support_evidence"]
            ),
            "observed_pattern_sha256s": sorted(
                {
                    call.observed_pattern_sha256
                    for row in ordered
                    for call in row.calls
                    if call.observed_pattern_sha256
                }
            ),
            "complete_durable_lineage": not interrupted and report["population_complete"],
            "custodian_audit": custody.model_dump(mode="json"),
        }
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for row in ordered:
        write_exclusive(
            args.output_dir / "rows" / f"{row.question_id_sha256}.json", row.model_dump(mode="json")
        )
    write_exclusive(args.output_dir / "r2-report.json", report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "scientific_state",
                    "completed_rows",
                    "unfinished_rows",
                    "unresolved_behavior_changing_blocker_rows",
                    "observed_tool_calls",
                    "http_post_admissions",
                    "interrupted",
                    "D4",
                    "founder_cost",
                )
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--claim-sha", required=True)
    args = parser.parse_args()
    try:
        aggregate(args)
    except Exception as error:
        write_exclusive(
            args.output_dir / "r2-aggregation-failure.json",
            {
                "scientific_state": "BLOCKED",
                "expected_rows": 1463,
                "code": "aggregation-incomplete-retain-permanent-attempt-and-ledger",
                "error_sha256": digest(str(error)),
                "claim_sha": args.claim_sha,
                "new_founder_decision_before_new_model_attempt": True,
                "D4": False,
            },
        )
        raise SystemExit("R2 accounting incomplete; retained attempt remains BLOCKED") from None


if __name__ == "__main__":
    main()
