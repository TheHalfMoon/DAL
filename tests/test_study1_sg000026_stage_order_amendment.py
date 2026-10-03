from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "registry" / "study1_sg000026_stage_order_amendment.json"
PROTOCOL = ROOT / "registry" / "study1_preregistered_protocol_2026-10-02.json"
FRONTIER = ROOT / "registry" / "study1_sg000026_frontier_status.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_stage_order_amendment_binds_founder_authorization_and_parent_protocol() -> None:
    amendment = _load(AMENDMENT)
    authorization = amendment["founder_authorization"]
    parent = amendment["immutable_parent_protocol"]

    assert amendment["amendment_id"] == "SG-000026-G3"
    assert authorization["issue"] == 128
    assert authorization["comment_id"] == 5970595978
    assert authorization["option"] == "A"
    assert authorization["authorized"] is True
    assert parent["modified_by_this_amendment"] is False
    assert parent["sha256"] == _sha256(PROTOCOL)
    assert parent["sha256"] == "d4947d8db42494684bd0c4e67d590f9ef13b52c68e13766faaeb0dcb55cf1192"


def test_query_pattern_criterion_is_deferred_but_not_removed() -> None:
    amendment = _load(AMENDMENT)
    stages = amendment["effective_stage_order"]
    d2 = stages["D2"]
    gate = stages["post_D3_pre_D4_query_trace_gate"]

    assert d2["deferred_but_mandatory_criterion"] == (
        "every governed development-role FHIR query pattern is supported or explicitly blocking"
    )
    assert gate["mandatory"] is True
    assert gate["roles"] == ["calibration", "validation"]
    assert gate["D4_blocked_until_pass"] is True
    assert stages["D4"]["training_or_fine_tuning_allowed_before_query_trace_gate_pass"] is False
    assert set(gate["invalid_substitutes"]) == {
        "SQL proc_query",
        "expected resource IDs",
        "static source inspection",
        "invented traces",
    }


def test_amendment_does_not_close_d2_or_activate_later_stages() -> None:
    amendment = _load(AMENDMENT)
    effects = amendment["current_effects"]
    final = amendment["sealed_final_invariants"]
    frontier = _load(FRONTIER)

    assert effects == {
        "D2_closed": False,
        "D3_activated": False,
        "model_selected": False,
        "training_activated": False,
        "final_role_access_authorized": False,
    }
    assert final["patients"] == 40
    assert final["rows"] == 173
    assert final["access_before_D9"] == "forbidden"
    assert frontier["state"] == "direct-id-proven-stage-order-repaired-d2-closeout-pending"
    assert frontier["d2_closeout_allowed"] is False
    assert frontier["later_stages_activated"] is False
    assert frontier["real_direct_id_evidence"]["query_trace_coverage"] == (
        "deferred-mandatory-post-d3-pre-d4"
    )
