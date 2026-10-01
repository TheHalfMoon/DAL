from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_ROOT = Path("registry/p08_sg000022_final_evaluation")
_MANIFEST = _ROOT / "manifest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest() -> dict[str, Any]:
    payload = _load(_MANIFEST)
    assert isinstance(payload, dict)
    return payload


def test_sg000022_promoted_files_match_one_shot_artifact_bytes() -> None:
    manifest = _manifest()
    assert manifest["grain_id"] == "SG-000022"
    assert manifest["canonical_execution_main"] == (
        "f1955d5beeb2444f1d604626629036196a1dedd5"
    )
    assert manifest["source_workflow_run_id"] == 36886952302
    assert manifest["source_artifact_id"] == 11176566473
    assert manifest["source_artifact_zip_sha256"] == (
        "8dcd894be6ae184aaf5311417d268a5500b89d0d78d14ee7a79305fbb3071136"
    )
    assert manifest["source_post_merge_gaxbench_run_id"] == 36886952212
    assert manifest["authorization_digest"] == (
        "626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de"
    )
    assert manifest["final_test_inference_executed"] is True
    assert manifest["raw_artifacts_persisted_before_metrics"] is True
    assert manifest["zero_founder_cost"] is True
    assert manifest["post_test_tuning_permitted"] is False

    assert set(manifest["artifacts"]) == {
        "metrics.json",
        "summary.json",
        "raw-fhir-interface-block.json",
        "raw-laya-pubmedqa-predictions.json",
        "raw-native-abstention-predictions.json",
        "raw-pubmedqa-predictions.json",
    }
    for name, entry in manifest["artifacts"].items():
        path = _ROOT / name
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["byte_sha256"]


def test_sg000022_preserves_negative_blocked_and_warning_outcomes() -> None:
    manifest = _manifest()
    metrics = _load(_ROOT / "metrics.json")
    summary = _load(_ROOT / "summary.json")
    fhir = _load(_ROOT / "raw-fhir-interface-block.json")

    assert summary["pubmedqa_requested"] == 500
    assert summary["native_requested"] == 1000
    assert summary["fhir_requested"] == 173
    assert summary["fhir_status"] == "interface-blocked-preexecution"
    assert summary["laya_pubmedqa_completed"] == 500
    assert summary["raw_artifacts_persisted_before_metrics"] is True

    assert metrics["pubmedqa"]["paper"]["accuracy"] == 0.552
    assert metrics["pubmedqa"]["clinical_control"]["accuracy"] == 0.552
    assert metrics["pubmedqa"]["laya"]["accuracy"] == 0.53

    pubmed_primary = metrics["primary_comparisons"][0]
    assert pubmed_primary["paired_bootstrap"]["estimate"] == 0.0
    assert pubmed_primary["paired_bootstrap"]["ci_low"] == 0.0
    assert pubmed_primary["paired_bootstrap"]["ci_high"] == 0.0

    native_primary = metrics["primary_comparisons"][1]
    assert native_primary["paired_bootstrap"]["estimate"] == (
        -0.012499999999999956
    )
    assert native_primary["paired_bootstrap"]["ci_low"] == (
        -0.020000000000000018
    )
    assert native_primary["paired_bootstrap"]["ci_high"] == (
        -0.004999999999999893
    )
    assert metrics["native_abstention"]["paper"]["risk_at_80"] == 0.655
    assert metrics["native_abstention"]["clinical_control"]["risk_at_80"] == (
        0.6675
    )

    paper_policy = metrics["native_abstention"]["paper"]["actual_policy"]
    assert paper_policy["0.8"]["actual_coverage"] == 1.0
    assert paper_policy["0.8"]["unsafe_commit_rate"] == 1.0
    assert paper_policy["0.9"]["actual_coverage"] == 1.0
    assert paper_policy["0.9"]["unsafe_commit_rate"] == 1.0

    assert metrics["primary_comparisons"][2]["status"] == "blocked"
    assert fhir["detected_before_final_test_access"] is True
    assert fhir["gold_rows_loaded"] == 0
    for system in fhir["systems"]:
        assert system["requested"] == 173
        assert system["completed"] == 0
        assert system["failures"]["interface"] == 173
        assert system["status"] == "blocked"

    assert metrics["multiplicity"]["status"] == "no-p-values-emitted"
    assert metrics["claims"] == {
        "clinical_safety": "not-claimed",
        "sota": "not-claimed",
        "superiority": "not-claimed",
    }
    assert manifest["laya_runtime_warning"]["observed"] is True
    assert manifest["laya_runtime_warning"]["kind"] == (
        "uncalibrated-confidence-warning"
    )
