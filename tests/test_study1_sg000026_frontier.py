from __future__ import annotations

import json
from pathlib import Path

STATUS_PATH = Path("registry/study1_sg000026_frontier_status.json")
CURRENT_PATH = Path("specs/CURRENT.md")
TASKS_PATH = Path("specs/tasks.md")


def _status() -> dict[str, object]:
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def test_sg000026_frontier_records_authorized_option_a_boundary() -> None:
    status = _status()
    assert status["state"] == "option-a-authorized-custodian-pending-canonicalization"
    assert status["governance_gate_issue"] == 120
    assert status["canonical_frontier_sha"] == "b46d3de2c5722b43f6ff6354a9f7fb5917c60283"
    recovery = status["authorized_recovery"]
    assert isinstance(recovery, dict)
    assert recovery["option"] == "option-a-blind-metadata-only-custodian"
    assert recovery["authorization_comment_id"] == 5963555775
    grains = status["canonical_grains"]
    assert isinstance(grains, list)
    assert [grain["pull_request"] for grain in grains] == [116, 117, 118, 119, 121]
    assert status["blocked_development_rows"] == {"calibration": 341, "validation": 1122}
    assert status["sealed_final_role"] == {
        "access": "sealed-and-forbidden-to-d2",
        "patients": 40,
        "rows": 173,
    }
    assert status["d2_closeout_allowed"] is False
    assert status["later_stages_activated"] is False


def test_sg000026_human_frontier_matches_machine_state() -> None:
    current = CURRENT_PATH.read_text(encoding="utf-8")
    tasks = TASKS_PATH.read_text(encoding="utf-8")

    marker = "ACTIVE — OPTION_A_AUTHORIZED / CUSTODIAN_PENDING_CANONICALIZATION"
    assert marker in current
    assert marker in tasks
    assert "GOVERNANCE ACTIVATION ONLY" not in current
    assert "PR #117 merge `0cfc2db`" in tasks
    assert "PR #118 merge `5ea436e`" in tasks
    assert "PR #119 merge `aa59981`" in tasks
    assert "PR #121 merge `b46d3de2`" in tasks
    assert "Founder-authorize Option A" in tasks
    assert "Canonical SG-000026 / D2 closeout" in tasks
