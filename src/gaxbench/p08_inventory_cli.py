from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.p08_inventory import audit_real_inventory, load_real_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gax-p08-inventory")
    parser.add_argument("--inventory", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    inventory_path = Path(args.inventory).resolve()
    report = audit_real_inventory(load_real_inventory(inventory_path))
    print(
        json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
