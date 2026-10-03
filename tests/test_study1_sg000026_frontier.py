from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATUS_PATH = Path("registry/study1_sg000026_frontier_status.json")
CURRENT_PATH = Path("specs/CURRENT.md")
TASKS_PATH = Path("specs/tasks.md")
REPORT_PATH = Path("registry/study1_sg000026_real_direct_id_qualification.json")
RECEIPT_PATH = Path("registry/study1_sg000026_real_direct_id_execution_receipt.json")


def _status() -> dict[str, object]:
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sg000026_frontier_records_direct_id_proof_and_query_trace_gate() -> None:
    status = _status()
    assert status["state"] == "direct-id-proven-query-trace-producer-governance-blocked"
    assert status["recovery_governance_gate_issue"] == 120
    assert status["governance_gate_issue"] == 128
    assert status["query_trace_recovery_gate_issue"] == 126
    assert status["canonical_frontier_sha"] == "8eee15506a48dd03428363d8b5e7234d50f4a960"
    recovery = status["authorized_recovery"]
    assert isinstance(recovery, dict)
    assert recovery["option"] == "option-a-blind-metadata-only-custodian"
    assert recovery["authorization_comment_id"] == 5963555775
    grains = status["canonical_grains"]
    assert isinstance(grains, list)
    assert [grain["pull_request"] for grain in grains] == [
        116,
        117,
        118,
        119,
        121,
        122,
        123,
        124,
        125,
    ]
    assert status["blocked_development_rows"] == {"calibration": 341, "validation": 1122}
    assert status["sealed_final_role"] == {
        "access": "sealed-and-forbidden-to-d2",
        "patients": 40,
        "rows": 173,
    }
    query_recovery = status["query_trace_recovery_authorization"]
    assert isinstance(query_recovery, dict)
    assert query_recovery["authorization_comment_id"] == 5970310150
    assert query_recovery["authorized"] is True
    assert status["d2_closeout_allowed"] is False
    assert status["later_stages_activated"] is False


def test_sg000026_direct_id_evidence_is_exact_and_durable() -> None:
    status = _status()
    evidence = status["real_direct_id_evidence"]
    assert isinstance(evidence, dict)
    assert evidence["workflow_run"] == 37088504254
    assert evidence["artifact_id"] == 11261144886
    assert evidence["report_sha256"] == _sha256(REPORT_PATH)
    assert evidence["receipt_sha256"] == _sha256(RECEIPT_PATH)
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert report["status"] == "partial-pass-direct-id-only"
    assert report["resolved_reference_count"] == 21527
    assert report["missing_reference_count"] == 0
    assert report["mismatch_rows"] == 0
    assert report["query_trace_coverage"] == "blocked-unavailable-from-authorized-projection"
    assert report["d2_closeout_allowed"] is False
    assert report["sealed_final_rows_accessed"] is False
    assert receipt["canonical_main_sha"] == "8eee15506a48dd03428363d8b5e7234d50f4a960"
    assert receipt["sealed_final_rows_accessed"] is False
    assert receipt["zero_founder_cost"] is True


def test_sg000026_human_frontier_matches_machine_state() -> None:
    current = CURRENT_PATH.read_text(encoding="utf-8")
    tasks = TASKS_PATH.read_text(encoding="utf-8")

    marker = "REAL_DIRECT_ID_PROVEN / QUERY_TRACE_PRODUCER_GOVERNANCE_BLOCKED"
    assert marker in current
    assert marker in tasks
    assert "Issue #126" in current
    assert "Issue #126" in tasks
    assert "Issue #128" in current
    assert "Issue #128" in tasks
    assert "run `37088504254` SUCCESS" in tasks
    assert "21,527/21,527" in current
    assert "21,527/21,527" in tasks
    assert "invented traces are not acceptable substitutes" in tasks
    assert "Canonical SG-000026 / D2 closeout" in tasks


def test_query_trace_governance_records_authorization_and_stage_order_block() -> None:
    record = json.loads(
        Path("registry/study1_sg000026_query_trace_governance.json").read_text(encoding="utf-8")
    )
    authorization = record["query_trace_recovery_authorization"]
    assert authorization["issue"] == 126
    assert authorization["comment_id"] == 5970310150
    assert authorization["authorized"] is True
    assert authorization["final_role_content_or_trace_access_allowed"] is False

    upstream = record["frozen_upstream_trace_dependency"]
    assert upstream["commit"] == "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    assert upstream["single_turn_request_agent_blob_sha"] == (
        "1188a4053560924c3ed801e9b1aaa91ccd6d010d"
    )
    assert upstream["core_utils_blob_sha"] == "6544570985916074f40a5fb469243aa5ced22f65"

    conflict = record["stage_order_conflict"]
    assert conflict["status"] == "blocked-requires-founder-decision"
    assert conflict["issue"] == 128
    assert record["invariants"]["model_selection_performed"] is False
    assert (
        record["invariants"]["development_question_text_accessed_for_this_governance_record"]
        is False
    )
    assert record["invariants"]["final_role_content_accessed"] is False
    assert record["invariants"]["d3_activated"] is False
    assert record["d2_closeout_allowed"] is False
