"""Investigate every retained blocker reason using normalized development evidence.

Only finite structural names or hash identities may leave this analysis. Candidate
FHIR support is not a claim of equivalence to the frozen benchmark server.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from persist_sg000028_evidence import ROOT, build, load, safe_reason, sha

OUTPUT = ROOT / "registry/study1_sg000028_blocker_investigation.json"
FHIR_CANDIDATES = frozenset(
    "category code date encounter patient specimen status type _sort _include".split()
)
INVALID_PREFIX_MODIFIERS = frozenset({"date:gt", "date:gte", "date:lt", "date:lte"})
NAME_SHAPE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*(?:[.:][A-Za-z_][A-Za-z0-9_-]*)*")


def classify(reason: str) -> tuple[str, str, str]:
    if reason.startswith("unsupported-parameter:"):
        name = reason.removeprefix("unsupported-parameter:")
        if not NAME_SHAPE.fullmatch(name):
            return (
                "malformed-fhir-search-parameter-name",
                "name-structure-anomaly-not-complete-server-semantics-proof",
                "Retain blocker pending faithful semantics proof; do not rewrite the name. "
                "FHIR R4 permits ignoring empty parameters, so empty-value cases are potential "
                "compatibility or exerciser deficiencies rather than proven irreparable requests.",
            )
        if name in INVALID_PREFIX_MODIFIERS:
            return (
                "comparison-prefix-used-as-search-modifier",
                "proven-structural-prefix-misplacement",
                "Retain blocker; FHIR comparison prefixes belong in values, not these modifiers.",
            )
        if name in FHIR_CANDIDATES:
            return (
                "compatibility-surface-deficiency-candidate",
                "resource-specific-semantics-unproven",
                "A separately governed deterministic repair may support valid resource-specific "
                "search semantics only after benchmark equivalence is proven.",
            )
        return (
            "nonstandard-or-unproven-search-semantics",
            "upstream-benchmark-semantics-required",
            "Do not alias, drop, ignore, or reinterpret the parameter; retain blocker until "
            "the exact frozen benchmark meaning can be supported faithfully.",
        )
    if reason == "search-target-outside-development-role":
        return (
            "role-firewall-target-rejection",
            "rejection-proven-underlying-target-identity-unavailable",
            "Retain firewall. Normalized evidence cannot distinguish a malformed identifier, "
            "hallucinated target, or forbidden-role target. Never expand to final-role resources.",
        )
    if reason in {"llm-call-error", "no-response"}:
        return (
            "inference-runtime-response-failure",
            "exception-class-not-retained",
            "Investigate runtime only in a separately governed diagnostic; do not fabricate calls "
            "or switch the producer. Existing evidence cannot identify the underlying exception.",
        )
    if reason == "no-tool-call":
        return (
            "missing-observed-tool-call",
            "observed-with-inference-error-in-this-run",
            "Retain failed row. Compatibility code cannot supply an unobserved tool call.",
        )
    if reason == "invalid-non-relative-query":
        return (
            "request-outside-relative-get-contract",
            "proven-observed-contract-rejection",
            "Retain blocker; the evidence does not preserve an absolute origin or fragment and "
            "cannot justify rewriting the request.",
        )
    raise ValueError("unclassified canonical blocker reason")


def analyze(source: Path) -> dict:
    evidence = build(source)
    if evidence != load(ROOT / "registry/study1_sg000028_execution_37156028113.json"):
        raise ValueError("immutable source evidence drift")
    rows = [
        json.loads(line)
        for path in source.rglob("shard-*-rows.jsonl")
        for line in path.read_text().splitlines()
        if line
    ]
    reason_counts: Counter[str] = Counter()
    class_rows: Counter[str] = Counter()
    reason_receipts = {}
    immutable_obstruction_hashes = set()
    missing_call_with_error = 0
    malformed_name_rows_with_empty_parameter = 0
    for row in rows:
        classes = set()
        if any(
            reason.startswith("unsupported-parameter:")
            and not NAME_SHAPE.fullmatch(reason.removeprefix("unsupported-parameter:"))
            and any(
                reason.removeprefix("unsupported-parameter:") + "=<empty>" in pattern
                for pattern in row["normalized_patterns"]
            )
            for reason in row["reason_codes"]
        ):
            malformed_name_rows_with_empty_parameter += 1
        if "no-tool-call" in row["reason_codes"] and "llm-call-error" in row["reason_codes"]:
            missing_call_with_error += 1
        for reason in row["reason_codes"]:
            category, certainty, action = classify(reason)
            classes.add(category)
            reason_counts[reason] += 1
            identity = safe_reason(reason)
            reason_receipts[identity] = {
                "safe_reason": identity,
                "source_reason_sha256": sha(reason.encode()),
                "class": category,
                "certainty": certainty,
                "governed_action": action,
            }
            if category in {
                "malformed-fhir-search-parameter-name",
                "comparison-prefix-used-as-search-modifier",
            }:
                immutable_obstruction_hashes.add(row["question_id_sha256"])
        class_rows.update(classes)
    for reason, count in reason_counts.items():
        reason_receipts[safe_reason(reason)]["affected_row_occurrences"] = count
    blocked = sum(row["status"] == "behavior-changing-blocker" for row in rows)
    return {
        "schema_version": "0.1",
        "study_id": "study1",
        "specgrain_id": "SG-000028",
        "grain_id": "SG-000028-G1",
        "research_contract_issue": 141,
        "source_main": evidence["canonical_main_sha"],
        "source_run": evidence["workflow_run_id"],
        "persisted_evidence_sha256": sha(
            (ROOT / "registry/study1_sg000028_execution_37156028113.json").read_bytes()
        ),
        "development_rows_investigated": len(rows),
        "blocked_rows_retained": blocked,
        "all_observed_reason_keys_classified": True,
        "unique_reason_keys": len(reason_receipts),
        "blocker_class_row_counts": dict(sorted(class_rows.items())),
        "class_counts_overlap": True,
        "reason_investigation": sorted(reason_receipts.values(), key=lambda r: r["safe_reason"]),
        "immutable_malformed_or_invalid_modifier_row_count": len(immutable_obstruction_hashes),
        "immutable_obstruction_question_hash_set_sha256": sha(
            json.dumps(sorted(immutable_obstruction_hashes), separators=(",", ":")).encode()
        ),
        "missing_tool_call_rows_with_inference_error": missing_call_with_error,
        "malformed_name_rows_with_empty_parameter": malformed_name_rows_with_empty_parameter,
        "empty_parameter_semantic_repair_candidate": True,
        "normative_reference": {
            "url": "https://hl7.org/fhir/R4/search.html",
            "page_sha256": "7db9490e5723cf44a6c998471f229575d7a00d76db52ee2684014049f8e0524d",
            "section": "3.1.1.4.5 Prefixes",
            "verified_quote": "For the ordered parameter types of number, date, and quantity, "
            "a prefix to the parameter value may be used to control the nature of the matching.",
            "empty_parameter_rule": "Empty parameters are not an error - they are just ignored "
            "by the server.",
            "limit": "This establishes prefix placement and empty-parameter handling, "
            "not the frozen server's complete handling of "
            "unknown parameters. Unsupported-parameter handling remains unproven; no "
            "lenient-ignore equivalence is claimed or used to waive the strict gate.",
        },
        "limits": [
            "Blocker reasons are row-associated; multiple tool calls cannot be "
            "individually attributed.",
            "Normalization discarded parameter values, target identities, absolute origins, "
            "and exception classes.",
            "Unsupported names were checked before role scope; reported classes are not a "
            "complete census of latent blockers.",
            "Candidate standard FHIR names do not prove resource-specific support or "
            "frozen benchmark equivalence.",
            "No final patient, resource, question, trace, label, or model output was consulted.",
        ],
        "current_protocol_conclusion": (
            "Faithful compatibility repairs may address valid search semantics, "
            "including empty-parameter handling. Naming anomalies alone do not prove all "
            "61 affected rows irreparable. Turning the 41 rows with comparison syntax used "
            "as unsupported modifiers into intended valid comparisons would require forbidden "
            "request reinterpretation. Faithful error retention does not make the original "
            "strict no-malformed-behavior gate PASS. The strict gate remains blocked."
        ),
        "governance_gate": {
            "state": "BLOCKED_REQUIRES_FOUNDER_DECISION",
            "decision_scope": "Future program direction after an immutable negative qualification; "
            "no waiver, PASS claim, or producer switch within SG-000028 is authorized.",
            "options": [
                {
                    "id": "A",
                    "description": "Preserve this negative Study 1 frontier and authorize a "
                    "separate prospective recovery/restart protocol with disclosed development "
                    "outcome exposure; freeze new rules and identities before any new execution.",
                    "consequence": "Current SG-000028 stays BLOCKED; current D4 stays inactive. "
                    "The sealed final role stays untouched and may be carried forward only under "
                    "a separately qualified final-evaluation authorization.",
                },
                {
                    "id": "B",
                    "description": "Retain the current protocol and document the program "
                    "as scientifically blocked at this negative qualification.",
                    "consequence": "No D4-D10 execution or final evaluation can proceed under "
                    "the current strict gate; no new experiment is authorized.",
                },
            ],
            "recommended_option": "A",
            "recommendation_reason": "A separate prospective protocol can address the feasibility "
            "failure without retroactively weakening the original result or claiming blindness "
            "to already-observed development outcomes.",
            "authorization_received": False,
        },
        "raw_benchmark_source_accessed": False,
        "raw_traces_accessed": False,
        "final_role_content_accessed": False,
        "producer_changed": False,
        "gate_criteria_changed": False,
        "d4_activation_allowed": False,
        "training_performed": False,
        "answer_correctness_scored": False,
        "model_selection_performed": False,
        "zero_founder_cost": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = analyze(args.source)
    payload = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    if args.check:
        if OUTPUT.read_bytes() != payload:
            raise SystemExit("blocker investigation drift")
    else:
        OUTPUT.write_bytes(payload)
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "unique_reason_keys",
                    "blocker_class_row_counts",
                    "immutable_malformed_or_invalid_modifier_row_count",
                ]
            },
            sort_keys=True,
        )
    )
