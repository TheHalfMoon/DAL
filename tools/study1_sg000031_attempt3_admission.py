"""Executable but unarmed Attempt-3 admission controller; engineering rehearsal only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.study1_attempt3_admission import (
    Attempt3AdmissionController,
    Attempt3AdmissionWorker,
    load_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attempt-3 admission: synthetic no-science rehearsal"
    )
    parser.add_argument("--rehearse", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    controller = Attempt3AdmissionController(load_contract(ROOT))
    result = controller.rehearse(ROOT)
    # Output is an engineering-only local proof, not a scientific receipt or ledger.
    # Exclusive creation prevents accidental overwrite/replay in the same workspace.
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    # Structural worker reference only. Never execute it.
    assert Attempt3AdmissionWorker is not None
    print("ATTEMPT3_REHEARSAL=UNARMED; SCIENTIFIC_EXECUTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
