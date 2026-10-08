"""B1 scientific-capability engineering rehearsal CLI; NEVER science execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.study1_attempt3_b1 import FrozenAttempt3Controller, load_contract

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="B1 unarmed Attempt-3 synthetic-only controller")
    parser.add_argument("--rehearse", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = FrozenAttempt3Controller(ROOT, load_contract(ROOT)).rehearse()
    # Output is a local engineering artifact only. It is never a scientific claim.
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print("ATTEMPT3_B1_ENGINEERING=REHEARSED; SCIENTIFIC_EXECUTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
