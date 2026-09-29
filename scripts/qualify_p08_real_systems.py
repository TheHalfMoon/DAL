from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaxbench.p08_development_audit import (
    audit_development_training_split,
    development_leakage_audit_digest,
)
from gaxbench.p08_real_systems import (
    build_development_training_manifest,
    development_manifest_digest,
)
from gaxbench.pubmedqa import PubMedQASplitManifest, load_frozen_pqal


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
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--parent-split", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--leakage-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()

    records = load_frozen_pqal(args.source)
    parent = PubMedQASplitManifest.model_validate(
        json.loads(args.parent_split.read_text(encoding="utf-8"))
    )
    manifest = build_development_training_manifest(records, parent)
    manifest_digest = development_manifest_digest(manifest)
    leakage = audit_development_training_split(records, parent, manifest)
    leakage_digest = development_leakage_audit_digest(leakage)

    if not leakage.clean:
        raise SystemExit(
            "SG-000019 nested development split has cross-role leakage; "
            "training/selection qualification is blocked"
        )

    write_json(args.manifest_output, manifest)
    write_json(args.leakage_output, leakage)
    write_json(
        args.summary_output,
        {
            "schema_version": "0.1",
            "dataset_id": manifest.dataset_id,
            "transform_revision": manifest.transform_revision,
            "manifest_sha256": manifest_digest,
            "leakage_audit_sha256": leakage_digest,
            "leakage_clean": leakage.clean,
            "train_count": len(manifest.train_ids),
            "selection_count": len(manifest.selection_ids),
            "train_action_counts": manifest.train_action_counts,
            "selection_action_counts": manifest.selection_action_counts,
            "training_seeds": manifest.training_seeds,
            "final_test_access": manifest.final_test_access,
        },
    )
    print(manifest_digest)
    print(leakage_digest)


if __name__ == "__main__":
    main()
