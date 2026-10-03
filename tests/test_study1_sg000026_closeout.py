from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT = ROOT / "registry" / "study1_sg000026_closeout.json"
FRONTIER = ROOT / "registry" / "study1_sg000026_frontier_status.json"
AMENDMENT = ROOT / "registry" / "study1_sg000026_stage_order_amendment.json"
CONTRACT = ROOT / "registry" / "study1_sg000026_contract.json"
REPORT = ROOT / "registry" / "study1_sg000026_real_direct_id_qualification.json"
RECEIPT = ROOT / "registry" / "study1_sg000026_real_direct_id_execution_receipt.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _lf_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_d2_closeout_binds_immutable_contract_and_canonical_amendment() -> None:
    closeout = _load(CLOSEOUT)
    assert closeout["status"] == "closed-canonical"
    assert closeout["pre_closeout_main"] == "c1bc808d6381f8cab02da8adfc9ba519370cc0f8"
    assert closeout["original_contract"]["sha256"] == _lf_sha(CONTRACT)
    assert closeout["original_contract"]["preserved_unchanged"] is True
    effective = closeout["effective_protocol"]
    assert effective["amendment_pr"] == 130
    assert effective["amendment_merge_sha"] == "c1bc808d6381f8cab02da8adfc9ba519370cc0f8"
    assert effective["amendment_sha256"] == _lf_sha(AMENDMENT)
    assert effective["post_main_gaxbench_run"] == 37134290437
    assert effective["post_main_manuscript_run"] == 37134290428
    assert effective["observed_query_pattern_criterion_preserved"] is True


def test_every_model_independent_d2_exit_criterion_is_proven() -> None:
    closeout = _load(CLOSEOUT)
    criteria = closeout["model_independent_exit_criteria"]
    assert [item["id"] for item in criteria] == [
        "D2-E1", "D2-E2", "D2-E3", "D2-E4", "D2-E5", "D2-E6", "D2-E7", "D2-E8"
    ]
    assert {item["status"] for item in criteria} == {"proven"}
    assert all(item["evidence"] for item in criteria)

    report = _load(REPORT)
    receipt = _load(RECEIPT)
    assert report["requested_reference_count"] == report["resolved_reference_count"] == 21527
    assert report["exact_match_rows"] == report["rows_with_expected_ids"] == 1087
    assert report["mismatch_rows"] == 0
    assert report["missing_reference_count"] == 0
    assert report["runtime_parse_failure_count"] == 0
    assert report["model_selection_performed"] is False
    assert report["training_performed"] is False
    assert report["sealed_final_rows_accessed"] is False
    assert receipt["zero_founder_cost"] is True
    assert receipt["sealed_final_rows_accessed"] is False


def test_closeout_preserves_mandatory_post_d3_query_trace_gate() -> None:
    closeout = _load(CLOSEOUT)
    gate = closeout["deferred_mandatory_gate"]
    assert gate["status"] == "preserved-not-executed-in-D2"
    assert gate["execution_stage"] == "immediate-post-D3-pre-D4"
    assert gate["roles"] == ["calibration", "validation"]
    assert gate["D4_blocked_until_pass"] is True
    assert set(gate["invalid_substitutes"]) == {
        "SQL proc_query", "expected resource IDs", "static source inspection", "invented traces"
    }


def test_closeout_keeps_final_sealed_and_d3_inactive() -> None:
    closeout = _load(CLOSEOUT)
    frontier = _load(FRONTIER)
    sealed = closeout["sealed_final_boundary"]
    assert sealed["test_patient_count"] == 40
    assert sealed["test_row_count"] == 173
    assert sealed["test_gold_serialized"] is False
    assert sealed["access"] == "sealed"
    assert sealed["accessed_in_D2"] is False
    assert frontier["state"] == "closed-canonical-model-independent-d2"
    assert frontier["d2_closed"] is True
    assert frontier["d3_activation_eligible"] is True
    assert frontier["later_stages_activated"] is False
    assert frontier["d4_activation_allowed"] is False
    assert frontier["closeout_artifact"]["sha256"] == _raw_sha(CLOSEOUT)
