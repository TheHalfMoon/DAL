from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONTRACT = Path("registry/p08_sg000023_derivation_contract.json")
_MATRIX = Path("registry/p08_sg000023_evidence_availability_matrix.json")
_FINAL_ROOT = Path("registry/p08_sg000022_final_evaluation")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_derivation_contract_is_post_final_and_inference_free() -> None:
    contract = _load(_CONTRACT)
    assert contract["schema_version"] == "0.1"
    assert contract["grain_id"] == "SG-000023"
    assert contract["contract_id"] == "dal-p08-post-final-derivation-v0.1"
    assert contract["canonical_dependency"] == (
        "fd77fbab3ebcf9917469ae189b167874b3e058b9"
    )
    assert contract["evidence_matrix_path"] == _MATRIX.as_posix()
    assert contract["canonical_final_evidence_root"] == _FINAL_ROOT.as_posix()
    assert contract["no_new_inference"] is True
    assert contract["no_post_test_tuning"] is True
    assert contract["no_new_threshold_fitting"] is True
    assert contract["no_post_hoc_p_values"] is True
    assert contract["no_outcome_driven_subgroups"] is True


def test_derivation_contract_only_enables_matrix_available_families() -> None:
    contract = _load(_CONTRACT)
    matrix = _load(_MATRIX)
    rows = {row["id"]: row for row in matrix["rows"]}

    assert rows["reliability-analysis"]["status"] == "available"
    assert rows["risk-coverage-analysis"]["status"] == "available"
    assert rows["failure-taxonomy-and-qualitative-errors"]["status"] == "available"
    assert rows["paper-tables"]["status"] == "available"
    assert rows["paper-figures"]["status"] == "available"

    outputs = contract["paper_outputs"]
    assert set(outputs) == {
        "main_results_table",
        "selective_results_table",
        "evidence_boundaries_table",
        "reliability_figure",
        "risk_coverage_figure",
        "fhir_block_table",
    }
    assert "laya" not in outputs["reliability_figure"]["systems"]
    assert "uncalibrated" in outputs["reliability_figure"]["laya_policy"]
    assert outputs["risk_coverage_figure"]["curve_points"] == (
        "every-prefix-from-1-through-1000"
    )
    assert outputs["risk_coverage_figure"]["no_smoothing"] is True
    assert outputs["risk_coverage_figure"]["no_threshold_refit"] is True
    assert outputs["fhir_block_table"]["new_adapter_forbidden"] is True


def test_qualitative_selection_is_content_blind_and_deterministic() -> None:
    selection = _load(_CONTRACT)["qualitative_error_selection"]
    assert selection["selection_rule_id"] == "sg23-lexicographic-outcome-strata-v0.1"
    assert selection["selection_count_per_stratum"] == 3
    assert selection["clinical_text_used_for_selection"] is False
    assert selection["ranking_fields"] == ["source_id"]
    assert selection["ranking_direction"] == "ascending-lexicographic"
    assert selection["raw_clinical_text_export"] is False
    assert selection["zero_member_policy"] == "emit-empty-stratum-with-zero-count"
    assert len(selection["pubmedqa_strata"]) == 4
    assert len(selection["native_strata"]) == 3
    assert set(selection["threshold_sources"]) == {
        "paper_frozen_target_0_8_threshold",
        "control_frozen_target_0_8_threshold",
    }


def test_claim_export_policy_preserves_known_forbidden_claims() -> None:
    policy = _load(_CONTRACT)["claim_export_policy"]
    assert policy["null_negative_blocked_results_must_remain_visible"] is True
    assert set(policy["forbidden_claims"]) == {
        "superiority",
        "clinical-safety",
        "SOTA",
        "FHIR-final-performance",
        "direct-efficiency-superiority",
    }
    assert set(policy["affirmative_claim_requires"]) == {
        "evidence_packet_id",
        "supported-status",
        "canonical-source-paths",
    }


def test_all_declared_canonical_inputs_exist() -> None:
    assert _MATRIX.is_file()
    for filename in (
        "manifest.json",
        "metrics.json",
        "raw-fhir-interface-block.json",
        "raw-laya-pubmedqa-predictions.json",
        "raw-native-abstention-predictions.json",
        "raw-pubmedqa-predictions.json",
        "summary.json",
    ):
        assert (_FINAL_ROOT / filename).is_file(), filename
