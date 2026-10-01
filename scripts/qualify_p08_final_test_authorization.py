from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.p08_final_test_authorization import (
    build_final_test_authorization,
    load_final_test_authorization,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Qualify the SG-000021 final-test authorization artifact without running "
            "final-test inference."
        )
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--authorization",
        type=Path,
        default=Path("registry/p08_final_test_authorization_sg000021.json"),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    expected = load_final_test_authorization(root / args.authorization)
    rebuilt = build_final_test_authorization(root)
    if rebuilt != expected:
        raise SystemExit("SG-000021 authorization artifact does not match canonical evidence")

    print(
        json.dumps(
            {
                "authorization_digest": rebuilt.authorization_digest,
                "authorized_grain": rebuilt.authorized_grain,
                "final_test_access": rebuilt.final_test_access,
                "final_test_inference_executed": rebuilt.final_test_inference_executed,
                "final_test_rows_used": rebuilt.final_test_rows_used,
                "required_dataset_count": len(rebuilt.required_datasets),
                "required_system_count": len(rebuilt.required_system_bundle_digests),
                "state": rebuilt.state,
                "zero_founder_cost": rebuilt.zero_founder_cost,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())