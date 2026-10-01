from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "registry" / "p08_sg000023_paper_evidence"


def _load(name: str) -> dict[str, Any]:
    payload = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_evidence_is_deterministically_rebuildable() -> None:
    result = subprocess.run(
        [sys.executable, "tools/build_sg000023_paper_evidence.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "10 artifacts" in result.stdout


def test_paper_evidence_catalog_is_complete() -> None:
    assert {path.name for path in EVIDENCE.glob("*.json")} == {
        "claim_ledger.json",
        "evidence_boundaries.json",
        "evidence_packets.json",
        "fhir_block_table.json",
        "main_results.json",
        "provenance_index.json",
        "qualitative_examples.json",
        "reliability_source_data.json",
        "risk_coverage_source_data.json",
        "selective_results.json",
    }


def test_reliability_and_risk_coverage_preserve_frozen_semantics() -> None:
    reliability = _load("reliability_source_data.json")
    assert [row["system_id"] for row in reliability["systems"]] == [
        "paper",
        "clinical_control",
    ]
    for system in reliability["systems"]:
        assert len(system["bins"]) == 15
        assert system["computed_ece_15_equal_width"] == system["canonical_ece_15_equal_width"]
    assert "uncalibrated" in reliability["laya_disposition"]

    risk = _load("risk_coverage_source_data.json")
    assert risk["no_smoothing"] is True
    assert risk["no_threshold_refit"] is True
    for system in risk["systems"]:
        assert system["n"] == 1000
        assert len(system["points"]) == 1000
        assert system["points"][0]["coverage"] == 0.001
        assert system["points"][-1]["coverage"] == 1.0
        assert system["computed_aurc"] == system["canonical_aurc"]


def test_negative_and_blocked_results_remain_visible() -> None:
    selective = _load("selective_results.json")
    paper = next(row for row in selective["rows"] if row["system_id"] == "paper")
    assert paper["actual_policy"]["0.8"]["unsafe_commit_rate"] == 1.0
    assert paper["actual_policy"]["0.9"]["unsafe_commit_rate"] == 1.0
    laya = next(row for row in selective["rows"] if row["system_id"] == "laya")
    assert laya["status"] == "blocked"

    fhir = _load("fhir_block_table.json")
    assert fhir["new_adapter_forbidden"] is True
    assert all(row["status"] == "blocked" for row in fhir["rows"])
    assert all(row["gold_rows_loaded"] == 0 for row in fhir["rows"])


def test_qualitative_examples_are_content_blind_and_keep_zero_strata() -> None:
    examples = _load("qualitative_examples.json")
    assert examples["clinical_text_used_for_selection"] is False
    assert examples["raw_clinical_text_export"] is False
    for group in (examples["pubmedqa_strata"], examples["native_strata"]):
        for stratum in group:
            assert len(stratum["selected"]) <= 3
            selected_sources = [row["source_id"] for row in stratum["selected"]]
            assert selected_sources == sorted(selected_sources)
            for row in stratum["selected"]:
                assert "text" not in row
                assert "question" not in row
                assert "context" not in row

    zero = next(
        row for row in examples["native_strata"] if row["id"] == "both-abstain-on-sufficient"
    )
    assert zero["member_count"] == 0
    assert zero["selected"] == []


def test_claim_ledger_blocks_forbidden_affirmative_exports() -> None:
    ledger = _load("claim_ledger.json")
    by_id = {row["claim_id"]: row for row in ledger["claims"]}
    assert by_id["SG23-C004"]["status"] == "supported-negative-result"
    assert "unsafe-commit rate 1.0" in by_id["SG23-C004"]["text"]
    assert by_id["SG23-C006"]["status"] == "supported-blocked-result"
    for claim_id in ("SG23-C007", "SG23-C008", "SG23-C009", "SG23-C010"):
        assert by_id[claim_id]["exportable"] is False


def test_provenance_index_binds_sources_and_derived_artifacts() -> None:
    provenance = _load("provenance_index.json")
    assert provenance["canonical_main_dependency"] == (
        "d676beccfec001fd75d1b157b43068eb49a5733d"
    )
    assert provenance["no_new_inference"] is True
    assert provenance["no_post_test_tuning"] is True
    assert len(provenance["artifact_sha256"]) == 9
    assert "registry/p08_sg000022_final_evaluation/metrics.json" in provenance["source_sha256"]
