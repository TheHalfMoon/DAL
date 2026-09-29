from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.native_abstention_qualification import qualify_native_abstention


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-split", required=True, type=Path)
    parser.add_argument("--parent-leakage", required=True, type=Path)
    parser.add_argument("--role-output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--qualification-output", required=True, type=Path)
    args = parser.parse_args()

    role, audit, qualification = qualify_native_abstention(
        args.parent_split,
        args.parent_leakage,
    )
    write_json(args.role_output, role)
    write_json(args.audit_output, audit)
    write_json(args.qualification_output, qualification)


if __name__ == "__main__":
    main()
