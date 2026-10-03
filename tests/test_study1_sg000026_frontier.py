from __future__ import annotations

import json
from pathlib import Path

STATUS_PATH = Path("registry/study1_sg000026_frontier_status.json")
CURRENT_PATH = Path("specs/CURRENT.md")
TASKS_PATH = Path("specs/tasks.md")


def _status() -> dict[str, object]:
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def test_sg000026_frontier_records_canonical_grains_and_blocker() -> None:
    status = _status()
    assert status["state"] == "blocked-at-governance-gate"
    assert status["governance_gate_issue"] == 120
    assert status["canonical_frontier_sha"] == "aa59981148692c3524e66fb5e27d2dfce83533ae"
    grains = status["canonical_grains"]
    assert isinstance(grains, list)
    assert [grain["pull_request"] for grain in grains] == [116, 117, 118, 119]
    assert status["blocked_development_rows"] == {"calibration": 341, "validation": 1122}
    assert status["sealed_final_role"] == {
        "access": "sealed-and-forbidden-to-d2",
        "patients": 40,
        "rows": 173,
    }


def test_sg000026_human_frontier_matches_machine_state() -> None:
    current = CURRENT_PATH.read_text(encoding="utf-8")
    tasks = TASKS_PATH.read_text(encoding="utf-8")

    marker = "ACTIVE — BLOCKED_AT_GOVERNANCE_GATE #120"
    assert marker in current
    assert marker in tasks
    assert "GOVERNANCE ACTIVATION ONLY" not in current
    assert "ACTIVE ? GOVERNANCE ONLY" not in tasks
    assert "PR #117 merge `0cfc2db`" in tasks
    assert "PR #118 merge `5ea436e`" in tasks
    assert "PR #119 merge `aa59981`" in tasks
    assert "Canonical SG-000026 / D2 closeout" in tasks
