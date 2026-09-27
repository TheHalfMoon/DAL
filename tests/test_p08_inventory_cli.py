from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "registry" / "p08_real_inventory.json"


def test_inventory_cli_reports_sealed_blockers() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "gaxbench.p08_inventory_cli",
            "--inventory",
            str(INVENTORY),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["final_test_access"] == "sealed"
    assert payload["ready_for_authorization"] is False
    assert payload["blockers"] == sorted(payload["blockers"])
    assert len(payload["inventory_digest"]) == 64
