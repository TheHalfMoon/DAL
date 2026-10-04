"""Persist safe sufficient statistics from the completed canonical development run.

Never fetch benchmark data or regenerate inference. Legacy malformed parameter names
are opaque digest identities; their literal content is not copied to durable evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAIN = "f8f5c1c8ebfbe2e044ad9beae55e56b94f1f449d"
RUN = 37156028113
REPORT_SHA = "f1eeef772aa827a0500fb79b559cd7344f8bf2cf434e423e4191cbc9e7884164"
OUTPUT = ROOT / "registry/study1_sg000028_execution_37156028113.json"
# Finite structural vocabulary, never arbitrary generated strings.
PARAMETERS = frozenset(
    "id _id patient _count _date _include _limit _since _sort _until category code "
    "code.code code.coding.code code.coding.system code.system coding.code coding.system "
    "criteria date date-gt date.ge date.lt date:gt date:gte date:lt date:lte dateToday "
    "display effectiveDateTime effectiveDateTime.ge effectiveDateTime.lt "
    "effectivePeriod.end effectivePeriod.start encounter encounter:reference entryMode "
    "identifier.system identifier.value limit medicationAdministration.route "
    "medicationCodeableConcept medicationCodeableConcept.coding.code "
    "medicationCodeableConcept.coding.display medicationCodeableConcept.coding.system "
    "medicationReference medicationReference.display medicationRequest.route method "
    "reference request.method route route.code route.coding.code route.coding.display "
    "route.coding.system route.display route.system route:contains sort specimen status "
    "system type value valueBelow valueLessThan valueLow valueQuantity valueQuantity.lt".split()
)
VALUE_CLASSES = frozenset(
    "positive-int invalid-count id-list id patient-reference patient-id comparator "
    "token reference list empty value".split()
)
REASONS = frozenset(
    {
        "invalid-non-relative-query",
        "llm-call-error",
        "no-response",
        "no-tool-call",
        "search-target-outside-development-role",
    }
)
RESOURCE_TYPES = frozenset(
    "Patient Encounter Condition MedicationRequest Procedure Observation "
    "MedicationAdministration Specimen Location Medication".split()
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_reason(reason: str) -> str:
    if reason in REASONS:
        return reason
    prefix = "unsupported-parameter:"
    if reason.startswith(prefix) and reason[len(prefix) :] in PARAMETERS:
        return reason
    return "opaque-reason-sha256:" + sha(reason.encode())


def safe_pattern(pattern: str) -> str:
    if pattern == "invalid:invalid-non-relative-query":
        return pattern
    if pattern.startswith("read:"):
        resource = pattern[5:].removesuffix("/{id}")
        if resource in RESOURCE_TYPES and pattern.endswith("/{id}"):
            return pattern
    if pattern.startswith("search:"):
        resource, _, query = pattern[7:].partition("?")
        if resource in RESOURCE_TYPES:
            tokens = query.split("&") if query else []
            for token in tokens:
                match = re.fullmatch(r"([^=]+)=<([^<>]+)>", token)
                if not match or match[1] not in PARAMETERS or match[2] not in VALUE_CLASSES:
                    break
            else:
                return pattern
    return "opaque-pattern-sha256:" + sha(pattern.encode())


def build(source: Path) -> dict[str, Any]:
    report_path = next(source.rglob("query_trace_qualification.json"))
    report = load(report_path)
    if sha(report_path.read_bytes()) != REPORT_SHA or report["canonical_main_sha"] != MAIN:
        raise ValueError("canonical report identity mismatch")
    receipt = load(report_path.with_name("execution_receipt.json"))
    if receipt["query_trace_report_sha256"] != REPORT_SHA:
        raise ValueError("canonical receipt mismatch")

    # Recompute the original aggregate without printing or persisting its literal keys.
    spec = importlib.util.spec_from_file_location(
        "sg28_aggregate", ROOT / "scripts/study1_sg000028_query_trace_aggregate.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        previous_sha = os.environ.get("GITHUB_SHA")
        os.environ["GITHUB_SHA"] = MAIN
        try:
            recomputed = module.aggregate(
                source, Path(directory) / "report.json", Path(directory) / "receipt.json"
            )
        finally:
            if previous_sha is None:
                os.environ.pop("GITHUB_SHA", None)
            else:
                os.environ["GITHUB_SHA"] = previous_sha
        if recomputed != report:
            raise ValueError("canonical aggregate recomputation mismatch")

    artifacts = load(source / "artifacts.json")["artifacts"]
    jobs = load(source / "jobs.json")["jobs"]
    if len(artifacts) != 9 or len(jobs) != 9:
        raise ValueError("canonical job/artifact accounting mismatch")
    for artifact in artifacts:
        if (
            artifact["workflow_run"]["head_sha"] != MAIN
            or artifact["workflow_run"]["id"] != RUN
            or artifact["expired"]
        ):
            raise ValueError("artifact provenance drift")
        archive = source / "archives" / f"{artifact['id']}.zip"
        if "sha256:" + sha(archive.read_bytes()) != artifact["digest"]:
            raise ValueError("artifact ZIP digest mismatch")
    if any(j["head_sha"] != MAIN or j["run_id"] != RUN for j in jobs):
        raise ValueError("job provenance drift")

    rows = [
        json.loads(line)
        for path in sorted(source.rglob("shard-*-rows.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    patterns: dict[str, dict[str, Any]] = {}
    reasons: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    for row in rows:
        for reason in row["reason_codes"]:
            reasons[safe_reason(reason)] += 1
        row_classes = set()
        for reason in row["reason_codes"]:
            if reason.startswith("unsupported-parameter:"):
                name = reason.removeprefix("unsupported-parameter:")
                category = (
                    "unsupported-structural-parameter"
                    if name in PARAMETERS
                    else "malformed-or-unrecognized-parameter-name"
                )
            elif reason == "search-target-outside-development-role":
                category = "role-firewall-target-rejection"
            elif reason in {"llm-call-error", "no-response"}:
                category = "inference-response-failure"
            elif reason == "no-tool-call":
                category = "missing-tool-call"
            else:
                category = "invalid-request-shape"
            row_classes.add(category)
        classes.update(row_classes)
        for pattern in row["normalized_patterns"]:
            digest = sha(pattern.encode())
            entry = patterns.setdefault(
                digest,
                {
                    "source_pattern_sha256": digest,
                    "safe_pattern": safe_pattern(pattern),
                    "occurrences": 0,
                    "row_status_associations": Counter(),
                    "blocker_reason_associations": Counter(),
                },
            )
            entry["occurrences"] += 1
            entry["row_status_associations"][row["status"]] += 1
            entry["blocker_reason_associations"].update(
                safe_reason(reason) for reason in row["reason_codes"]
            )
    for entry in patterns.values():
        statuses = entry["row_status_associations"]
        entry["support_status"] = (
            "observed-only-in-passing-rows"
            if not statuses["behavior-changing-blocker"]
            else "blocked-row-associated-not-qualified"
        )
        entry["call_level_support_attribution_available"] = False
        entry["row_status_associations"] = dict(sorted(statuses.items()))
        entry["blocker_reason_associations"] = dict(
            sorted(entry["blocker_reason_associations"].items())
        )
    shards = []
    for audit_path in sorted(source.rglob("shard-*-audit.json")):
        audit = load(audit_path)
        index = audit["shard_index"]
        job = next(job for job in jobs if job["name"] == f"Development trace shard {index}")
        cleanup = next(
            step
            for step in job["steps"]
            if step["name"] == "Delete raw benchmark source before artifact upload"
        )
        if job["conclusion"] != "success" or cleanup["conclusion"] != "success":
            raise ValueError("canonical shard cleanup incomplete")
        artifact = next(
            a for a in artifacts if a["name"].startswith(f"sg000028-query-trace-shard-{index}-")
        )
        shard_rows = [r for r in rows if int(r["question_id_sha256"][:16], 16) % 8 == index]
        if len(shard_rows) != audit["selected_rows"]:
            raise ValueError("row-to-shard accounting mismatch")
        if Counter(r["status"] for r in shard_rows) != audit["status_counts"]:
            raise ValueError("shard status accounting mismatch")
        shards.append(
            {
                "shard_index": index,
                "job_id": job["id"],
                "artifact_id": artifact["id"],
                "artifact_digest": artifact["digest"],
                "zip_digest_verified": True,
                "audit_sha256": sha(audit_path.read_bytes()),
                "rows_sha256": audit["rows_sha256"],
                "selected_rows": audit["selected_rows"],
                "calibration_rows": audit["selected_calibration_rows"],
                "validation_rows": audit["selected_validation_rows"],
                "status_counts": audit["status_counts"],
                "reason_counts": dict(
                    sorted(
                        Counter(
                            {safe_reason(k): v for k, v in audit["reason_counts"].items()}
                        ).items()
                    )
                ),
                "final_rows_materialized": audit["final_rows_materialized"],
                "final_question_content_accessed": audit["final_question_content_accessed"],
                "raw_benchmark_source_cleanup_step": "success",
            }
        )
    aggregate_artifact = next(a for a in artifacts if "qualification" in a["name"])
    aggregate_job = next(j for j in jobs if j["name"] == "Aggregate query-trace gate evidence")
    if aggregate_job["conclusion"] != "success":
        raise ValueError("aggregate job incomplete")
    implementation_paths = [
        "scripts/study1_sg000028_query_trace_runner.py",
        "scripts/study1_sg000028_query_trace_aggregate.py",
        "src/gaxbench/study1_query_trace_gate.py",
        "src/gaxbench/study1_fhir_compat.py",
        "registry/study1_sg000028_contract.json",
        "registry/study1_sg000027_trace_producer_freeze.json",
        "registry/study1_sg000028_trace_producer_provenance_correction.json",
        "registry/study1_sg000026_fhir_runtime_manifest.json",
        ".github/workflows/study1-sg000028-query-trace-gate.yml",
    ]
    return {
        "schema_version": "0.1",
        "study_id": "study1",
        "specgrain_id": "SG-000028",
        "grain_id": "SG-000028-E1",
        "grain_kind": "canonical-negative-evidence-persistence",
        "canonical_main_sha": MAIN,
        "workflow_run_id": RUN,
        "workflow_url": f"https://github.com/TheHalfMoon/DAL/actions/runs/{RUN}",
        "workflow_execution_status": "success",
        "scientific_gate_status": "BLOCKED",
        "query_trace_gate_result": report["query_trace_gate_result"],
        "source_report_sha256": REPORT_SHA,
        "source_receipt_sha256": sha(report_path.with_name("execution_receipt.json").read_bytes()),
        "original_aggregate_recomputed_exactly": True,
        "aggregate_job_id": aggregate_job["id"],
        "aggregate_artifact_id": aggregate_artifact["id"],
        "aggregate_artifact_digest": aggregate_artifact["digest"],
        "all_nine_zip_digests_verified": True,
        "calibration_rows": report["calibration_rows"],
        "validation_rows": report["validation_rows"],
        "development_rows": len(rows),
        "unique_question_hashes": report["unique_question_hashes"],
        "question_role_assignments_sha256": sha(
            json.dumps(
                sorted((r["question_id_sha256"], r["role"]) for r in rows), separators=(",", ":")
            ).encode()
        ),
        "membership_sha256": report["membership_sha256"],
        "source_sha256": report["source_sha256"],
        "status_counts": report["status_counts"],
        "total_tool_calls": report["total_tool_calls"],
        "normalized_unique_pattern_count": len(patterns),
        "pattern_support_evidence": sorted(
            patterns.values(), key=lambda v: v["source_pattern_sha256"]
        ),
        "pattern_attribution_limit": (
            "Row artifacts associate reasons with rows, not individual calls; "
            "blocked-row association must not be interpreted as a proven per-call root cause."
        ),
        "blocker_reason_counts": dict(sorted(reasons.items())),
        "blocker_class_row_counts": dict(sorted(classes.items())),
        "blocker_class_counts_overlap": True,
        "shards": shards,
        "trace_producer": load(ROOT / "registry/study1_sg000028_contract.json")["trace_producer"],
        "runtime_manifest_path": "registry/study1_sg000026_fhir_runtime_manifest.json",
        "implementation_lf_sha256": {
            p: sha(
                subprocess.run(
                    ["git", "show", f"{MAIN}:{p}"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout.replace(b"\r\n", b"\n")
            )
            for p in implementation_paths
        },
        "artifact_firewall": {
            "legacy_source_masking_assertions_verified": False,
            "legacy_defect": "Generated malformed parameter names retained literal fragments "
            "in pattern and reason keys despite value masking.",
            "source_literal_keys_republished": False,
            "durable_output_policy": "finite structural vocabulary or opaque SHA-256 identities",
            "opaque_pattern_count": sum(
                v["safe_pattern"].startswith("opaque-") for v in patterns.values()
            ),
            "opaque_reason_count": sum(k.startswith("opaque-") for k in reasons),
            "raw_questions_emitted_by_persistence": False,
            "raw_patient_ids_emitted_by_persistence": False,
            "raw_query_values_emitted_by_persistence": False,
            "raw_traces_emitted_by_persistence": False,
        },
        "final_rows_materialized": report["final_rows_materialized"],
        "final_question_content_accessed": report["final_question_content_accessed"],
        "sealed_final_role": {"patients": 40, "rows": 173, "access": "sealed-before-D9"},
        "answer_correctness_scored": False,
        "training_performed": False,
        "model_selection_performed": False,
        "second_turn_reasoning_executed": False,
        "sg000028_closeout_allowed": False,
        "d4_activation_allowed": False,
        "zero_founder_cost": True,
        "cost_usd": report["cost_usd"],
        "next_governed_action": (
            "repair-artifact-output-firewall-and-investigate-complete-blocker-set"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = (json.dumps(build(args.source), indent=2, sort_keys=True) + "\n").encode()
    if args.check:
        if OUTPUT.read_bytes() != payload:
            raise SystemExit("durable evidence drift")
    else:
        OUTPUT.write_bytes(payload)
    print("Canonical safe evidence verified: 1463 rows; BLOCKED; final role sealed.")
