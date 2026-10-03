from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "registry/study1_sg000027_trace_producer_freeze.json"
CLOSEOUT = ROOT / "registry/study1_sg000027_closeout.json"
REPAIR = ROOT / "registry/study1_sg000027_transport_repair_contract.json"
CONTRACT = ROOT / "registry/study1_sg000028_contract.json"
CORRECTION = ROOT / "registry/study1_sg000028_trace_producer_provenance_correction.json"
FRONTIER = ROOT / "registry/study1_sg000028_frontier_status.json"
PATCH = ROOT / "patches/study1_fhir_agentbench_qwen_structured_tool_calls.patch"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lf_sha256(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_d3_freeze_bytes_remain_bound_to_canonical_closeout() -> None:
    closeout = _load(CLOSEOUT)
    expected = closeout["canonical_inputs"]["trace_producer_freeze"]["lf_sha256"]
    assert expected == "2dc7159d84772aeb775e605e6bbaf79187ce3293331764a6f9f2fc9e66feeec5"
    assert _lf_sha256(FREEZE) == expected


def test_provenance_overlay_matches_canonical_repair_bytes() -> None:
    freeze = _load(FREEZE)["trace_producer_identity"]["fhir_agentbench"]
    repair = _load(REPAIR)["repair"]
    contract = _load(CONTRACT)["trace_producer"]
    correction = _load(CORRECTION)
    correct = correction["correct_canonical_repair_provenance"]
    incorrect = correction["incorrect_freeze_provenance"]

    actual_patch_sha256 = hashlib.sha256(PATCH.read_bytes()).hexdigest()
    expected = {
        "transport_patch_sha256": actual_patch_sha256,
        "patched_core_utils_blob_sha": "e43534fcb90ca8a69d9cb75e458cd5d3ee01ecf6",
        "patched_core_utils_sha256": (
            "9dcbe56df002e8e30c28cc171dd47db687aa6760e5fc798aaa2dc5dc1d9803da"
        ),
    }
    assert expected["transport_patch_sha256"] == (
        "ef9c657ca666a1a6a9e7f21c79afe1da9e30ed4a30b879ecc6fb2af00db5d757"
    )

    assert repair["patch_path"] == correct["patch_path"]
    assert contract["transport_patch_path"] == correct["patch_path"]
    assert repair["patch_sha256"] == expected["transport_patch_sha256"]
    assert repair["patched_core_utils_blob_sha"] == expected[
        "patched_core_utils_blob_sha"
    ]
    assert repair["patched_core_utils_sha256"] == expected[
        "patched_core_utils_sha256"
    ]

    for source in (contract, correct):
        assert source["transport_patch_sha256"] == expected["transport_patch_sha256"]
        assert source["patched_core_utils_blob_sha"] == expected[
            "patched_core_utils_blob_sha"
        ]
        assert source["patched_core_utils_sha256"] == expected[
            "patched_core_utils_sha256"
        ]

    for key in expected:
        assert freeze[key] == incorrect[key]
        assert freeze[key] != correct[key]


def test_correction_is_provenance_only_and_does_not_switch_trace_producer() -> None:
    correction = _load(CORRECTION)
    invariants = correction["semantic_invariants"]
    assert all(value is False for value in invariants.values())
    assert correction["governance"]["correction_scope"] == (
        "provenance-fields-only-to-match-already-canonical-repair-bytes"
    )
    assert correction["governance"]["query_trace_gate_must_rerun_after_correction"] is True
    assert correction["governance"]["d4_activation_allowed"] is False
    assert correction["governance"]["training_allowed"] is False
    assert correction["governance"]["final_role_access_allowed"] is False


def test_blocked_run_is_explicitly_pre_data_and_not_query_trace_evidence() -> None:
    discovery = _load(CORRECTION)["discovery"]
    frontier = _load(FRONTIER)
    assert discovery["query_trace_run_id"] == 37150279061
    assert discovery["failure_class"] == "pre-data-provenance-mismatch"
    assert discovery["development_data_accessed"] is False
    assert discovery["final_data_accessed"] is False
    assert discovery["query_trace_evidence_generated"] is False
    assert frontier["canonical_dependency"]["blocked_provenance_run"] == 37150279061
    assert frontier["query_trace_evidence_generated"] is False
    assert frontier["development_data_accessed_by_blocked_provenance_run"] is False
    assert frontier["final_data_accessed_by_blocked_provenance_run"] is False
    assert frontier["d4_activation_allowed"] is False


def test_sg000028_contract_points_to_correction_and_keeps_gate_binding() -> None:
    contract = _load(CONTRACT)
    assert contract["activation_dependency"]["trace_producer_provenance_correction_path"] == (
        "registry/study1_sg000028_trace_producer_provenance_correction.json"
    )
    assert contract["governance"]["trace_producer_switching_after_gate_outcomes"] is False
    assert contract["governance"]["d4_activated"] is False
    assert contract["governance"]["training_allowed"] is False
    assert contract["governance"]["final_role_access_allowed"] is False
