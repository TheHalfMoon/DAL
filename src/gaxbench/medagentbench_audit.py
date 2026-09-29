from __future__ import annotations

import json
from pathlib import Path

from gaxbench.medagentbench_qualification import (
    MEDAGENTBENCH_ROLE_REVISION,
    MedAgentBenchCorpusProbe,
)
from gaxbench.provenance import canonical_json_sha256


def leakage_audit_payload(probe: MedAgentBenchCorpusProbe) -> dict[str, object]:
    """Return the exact metadata-only payload hashed by SG-000016 qualification."""
    return {
        "duplicate_task_id_count": probe.duplicate_task_id_count,
        "exact_duplicate_visible_task_count": probe.exact_duplicate_visible_task_count,
        "near_duplicate_visible_pair_count": probe.near_duplicate_visible_pair_count,
        "cross_family_near_duplicate_pair_count": probe.cross_family_near_duplicate_pair_count,
        "near_duplicate_pair_digest": probe.near_duplicate_pair_digest,
        "public_benchmark_pretraining_contamination": (
            probe.public_benchmark_pretraining_contamination
        ),
        "role_revision": MEDAGENTBENCH_ROLE_REVISION,
    }


def write_leakage_audit(
    source_probe_path: str | Path,
    output_path: str | Path,
) -> str:
    probe = MedAgentBenchCorpusProbe.model_validate_json(
        Path(source_probe_path).read_text(encoding="utf-8")
    )
    payload = leakage_audit_payload(probe)
    destination = Path(output_path)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return canonical_json_sha256(payload)
