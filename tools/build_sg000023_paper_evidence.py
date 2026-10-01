# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FINAL_ROOT = ROOT / "registry" / "p08_sg000022_final_evaluation"
CONTRACT_PATH = ROOT / "registry" / "p08_sg000023_derivation_contract.json"
MATRIX_PATH = ROOT / "registry" / "p08_sg000023_evidence_availability_matrix.json"
CALIBRATION_PATH = ROOT / "registry" / "p08_calibration_evidence_sg000020.json"
ECAL_PATH = ROOT / "registry" / "p08_ecal_selection_ledger_sg000020.json"
FHIR_SELECTION_PATH = ROOT / "registry" / "p08_fhir_selection_ledger_sg000020.json"
DEFAULT_OUTPUT = ROOT / "registry" / "p08_sg000023_paper_evidence"

PathLike = str | Path
JsonValue = dict[str, Any] | list[Any]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _metric_row(system_id: str, payload: dict[str, Any], metrics: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    reasons: dict[str, str] = {}
    for metric in metrics:
        if metric in payload:
            values[metric] = payload[metric]
        else:
            values[metric] = None
            if system_id == "laya" and metric == "ece_15_equal_width":
                reasons[metric] = (
                    "excluded because the canonical runtime warning marks affected Laya "
                    "confidence as uncalibrated"
                )
            else:
                reasons[metric] = "not reported in canonical metrics"
    return {
        "system_id": system_id,
        "requested": payload.get("requested"),
        "completed": payload.get("completed"),
        "failed": payload.get("failed"),
        "metrics": values,
        "null_reasons": reasons,
    }


def _main_results(metrics: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    spec = contract["paper_outputs"]["main_results_table"]
    pubmed = metrics["pubmedqa"]
    rows = [
        _metric_row(system_id, pubmed[system_id], spec["metrics"]) for system_id in spec["systems"]
    ]
    comparison = next(
        row
        for row in metrics["primary_comparisons"]
        if row["benchmark"] == "pubmedqa-pqal" and row["metric"] == "action_accuracy"
    )
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-main-action-selection-v0.1",
        "source": _rel(FINAL_ROOT / "metrics.json"),
        "rows": rows,
        "primary_comparison": comparison,
        "claim_boundary": {
            "superiority": "not-claimed",
            "significance": "not-claimed",
            "clinical_safety": "not-claimed",
            "sota": "not-claimed",
        },
    }


def _selective_row(system_id: str, payload: dict[str, Any], metrics: list[str]) -> dict[str, Any]:
    if payload.get("status") == "blocked":
        return {
            "system_id": system_id,
            "status": "blocked",
            "requested": payload.get("requested"),
            "completed": payload.get("completed"),
            "failed": payload.get("failed"),
            "reason": payload.get("reason"),
            "metrics": {metric: None for metric in metrics},
            "actual_policy": None,
        }
    return {
        "system_id": system_id,
        "status": "measured",
        "requested": payload.get("requested"),
        "completed": payload.get("completed"),
        "failed": payload.get("failed"),
        "metrics": {metric: payload[metric] for metric in metrics},
        "actual_policy": payload["actual_policy"],
    }


def _selective_results(metrics: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    spec = contract["paper_outputs"]["selective_results_table"]
    native = metrics["native_abstention"]
    rows = [
        _selective_row(system_id, native[system_id], spec["metrics"])
        for system_id in spec["systems"]
    ]
    comparison = next(
        row
        for row in metrics["primary_comparisons"]
        if row["benchmark"] == "gax-native-abstention-pqal" and row["metric"] == "risk_at_80"
    )
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-native-selective-v0.1",
        "source": _rel(FINAL_ROOT / "metrics.json"),
        "rows": rows,
        "primary_comparison": comparison,
        "mandatory_warning": (
            "The paper system has unsafe_commit_rate=1.0 at frozen target coverages 0.8 and 0.9; "
            "these negative outcomes must remain visible."
        ),
    }


def _evidence_boundaries(matrix: dict[str, Any]) -> dict[str, Any]:
    include = {"blocked", "unavailable", "not-applicable"}
    rows = []
    for row in matrix["rows"]:
        if row["status"] not in include:
            continue
        rows.append(
            {
                "id": row["id"],
                "status": row["status"],
                "requested_analysis_or_claim": row["requested_analysis_or_claim"],
                "computation_class": row["computation_class"],
                "allowed_artifacts": row["allowed_artifacts"],
                "prohibited_interpretation": row["prohibited_interpretation"],
                "no_packet_reason": row.get("no_packet_reason"),
            }
        )
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-evidence-boundaries-v0.1",
        "source": _rel(MATRIX_PATH),
        "rows": rows,
    }


def _reliability_for_system(
    rows: list[dict[str, Any]], system_id: str, edges: list[float]
) -> dict[str, Any]:
    bins: list[list[tuple[float, bool]]] = [[] for _ in range(len(edges) - 1)]
    probability_key = f"{system_id}_action_probabilities"
    correct_key = f"{system_id}_correct"
    for row in rows:
        probabilities = row[probability_key]
        confidence = max(float(value) for value in probabilities.values())
        index = min(int(confidence * (len(edges) - 1)), len(edges) - 2)
        bins[index].append((confidence, bool(row[correct_key])))

    output_bins = []
    total = len(rows)
    ece = 0.0
    for index, members in enumerate(bins):
        if members:
            mean_confidence = sum(item[0] for item in members) / len(members)
            accuracy = sum(1 for item in members if item[1]) / len(members)
            ece += (len(members) / total) * abs(accuracy - mean_confidence)
        else:
            mean_confidence = None
            accuracy = None
        output_bins.append(
            {
                "bin_index": index,
                "lower": edges[index],
                "upper": edges[index + 1],
                "count": len(members),
                "mean_confidence": mean_confidence,
                "accuracy": accuracy,
            }
        )
    return {
        "system_id": system_id,
        "n": total,
        "computed_ece_15_equal_width": ece,
        "bins": output_bins,
    }


def _reliability(
    raw_pubmed: list[dict[str, Any]], metrics: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    spec = contract["paper_outputs"]["reliability_figure"]
    systems = [
        _reliability_for_system(raw_pubmed, system_id, spec["bin_edges"])
        for system_id in spec["systems"]
    ]
    for system in systems:
        canonical = metrics["pubmedqa"][system["system_id"]]["ece_15_equal_width"]
        if not math.isclose(
            system["computed_ece_15_equal_width"], canonical, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(
                f"reliability derivation mismatch for {system['system_id']}: "
                f"{system['computed_ece_15_equal_width']} != {canonical}"
            )
        system["canonical_ece_15_equal_width"] = canonical
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "figure_source_id": "sg23-reliability-v0.1",
        "source": _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
        "bin_edges": spec["bin_edges"],
        "systems": systems,
        "laya_disposition": spec["laya_policy"],
    }


def _risk_curve_for_system(
    rows: list[dict[str, Any]], system_id: str, canonical: dict[str, Any]
) -> dict[str, Any]:
    score_key = f"{system_id}_selection_score"
    correct_key = f"{system_id}_action_correct"
    ranked = sorted(rows, key=lambda row: (-float(row[score_key]), str(row["item_id"])))
    cumulative_correct = 0
    points = []
    for index, row in enumerate(ranked, start=1):
        cumulative_correct += int(bool(row[correct_key]))
        risk = 1.0 - (cumulative_correct / index)
        points.append({"prefix_length": index, "coverage": index / len(ranked), "risk": risk})

    computed_aurc = sum(point["risk"] for point in points) / len(points)
    checks = {
        "risk_at_50": points[499]["risk"],
        "risk_at_80": points[799]["risk"],
        "risk_at_90": points[899]["risk"],
    }
    for metric, value in checks.items():
        if not math.isclose(value, canonical[metric], rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(
                f"risk-coverage mismatch for {system_id} {metric}: {value} != {canonical[metric]}"
            )
    if not math.isclose(computed_aurc, canonical["aurc"], rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"AURC mismatch for {system_id}: {computed_aurc} != {canonical['aurc']}")

    return {
        "system_id": system_id,
        "n": len(ranked),
        "computed_aurc": computed_aurc,
        "canonical_aurc": canonical["aurc"],
        "points": points,
    }


def _risk_coverage(
    raw_native: list[dict[str, Any]], metrics: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    spec = contract["paper_outputs"]["risk_coverage_figure"]
    if len(raw_native) != 1000:
        raise ValueError(f"expected 1000 native rows, found {len(raw_native)}")
    systems = [
        _risk_curve_for_system(raw_native, system_id, metrics["native_abstention"][system_id])
        for system_id in spec["systems"]
    ]
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "figure_source_id": "sg23-risk-coverage-v0.1",
        "source": _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
        "ordering": spec["ordering"],
        "no_smoothing": spec["no_smoothing"],
        "no_threshold_refit": spec["no_threshold_refit"],
        "systems": systems,
    }


def _fhir_block(raw_fhir: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for system in raw_fhir["systems"]:
        rows.append(
            {
                "system_id": system["system_id"],
                "requested": system["requested"],
                "completed": system["completed"],
                "interface_failures": system["failures"]["interface"],
                "gold_rows_loaded": raw_fhir["gold_rows_loaded"],
                "reason": system["reason"],
                "status": system["status"],
            }
        )
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-fhir-block-v0.1",
        "source": _rel(FINAL_ROOT / "raw-fhir-interface-block.json"),
        "detected_before_final_test_access": raw_fhir["detected_before_final_test_access"],
        "new_adapter_forbidden": True,
        "rows": rows,
    }


def _select_examples(
    candidates: list[dict[str, Any]],
    count: int,
    payload: Callable[[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered = sorted(candidates, key=lambda row: (str(row["source_id"]), str(row["item_id"])))
    return [payload(row) for row in ordered[:count]]


def _qualitative(
    raw_pubmed: list[dict[str, Any]],
    raw_laya: dict[str, Any],
    raw_native: list[dict[str, Any]],
    metrics: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    spec = contract["qualitative_error_selection"]
    count = int(spec["selection_count_per_stratum"])
    laya_by_source = {str(row["source_id"]): row for row in raw_laya["predictions"]}

    pubmed_predicates: dict[str, Callable[[dict[str, Any], dict[str, Any]], bool]] = {
        "paper-control-correct-laya-wrong": lambda row, laya: (
            bool(row["paper_correct"])
            and bool(row["clinical_control_correct"])
            and not bool(laya["correct"])
        ),
        "paper-control-wrong-laya-correct": lambda row, laya: (
            not bool(row["paper_correct"])
            and not bool(row["clinical_control_correct"])
            and bool(laya["correct"])
        ),
        "all-systems-wrong": lambda row, laya: (
            not bool(row["paper_correct"])
            and not bool(row["clinical_control_correct"])
            and not bool(laya["correct"])
        ),
        "all-systems-correct": lambda row, laya: (
            bool(row["paper_correct"])
            and bool(row["clinical_control_correct"])
            and bool(laya["correct"])
        ),
    }

    pubmed_strata = []
    for declared in spec["pubmedqa_strata"]:
        stratum_id = declared["id"]
        matches = []
        for row in raw_pubmed:
            laya = laya_by_source[str(row["source_id"])]
            if pubmed_predicates[stratum_id](row, laya):
                merged = dict(row)
                merged["laya"] = laya
                matches.append(merged)

        def pubmed_payload(row: dict[str, Any], stratum_id: str = stratum_id) -> dict[str, Any]:
            laya = row["laya"]
            return {
                "stratum_id": stratum_id,
                "item_id": row["item_id"],
                "source_id": row["source_id"],
                "gold_label": row["gold_action"],
                "system_predictions_or_correctness": {
                    "paper": {
                        "prediction": row["paper_predicted_action"],
                        "correct": row["paper_correct"],
                    },
                    "clinical_control": {
                        "prediction": row["clinical_control_predicted_action"],
                        "correct": row["clinical_control_correct"],
                    },
                    "laya": {"prediction": laya["prediction"], "correct": laya["correct"]},
                },
            }

        pubmed_strata.append(
            {
                "id": stratum_id,
                "predicate": declared["predicate"],
                "member_count": len(matches),
                "selected": _select_examples(matches, count, pubmed_payload),
            }
        )

    paper_threshold = metrics["native_abstention"]["paper"]["actual_policy"]["0.8"]["threshold"]
    control_threshold = metrics["native_abstention"]["clinical_control"]["actual_policy"]["0.8"][
        "threshold"
    ]
    native_predicates: dict[str, Callable[[dict[str, Any]], bool]] = {
        "paper-only-unsafe-on-insufficient": lambda row: (
            not bool(row["gold_sufficient"])
            and float(row["paper_selection_score"]) >= paper_threshold
            and float(row["clinical_control_selection_score"]) < control_threshold
        ),
        "both-unsafe-on-insufficient": lambda row: (
            not bool(row["gold_sufficient"])
            and float(row["paper_selection_score"]) >= paper_threshold
            and float(row["clinical_control_selection_score"]) >= control_threshold
        ),
        "both-abstain-on-sufficient": lambda row: (
            bool(row["gold_sufficient"])
            and float(row["paper_selection_score"]) < paper_threshold
            and float(row["clinical_control_selection_score"]) < control_threshold
        ),
    }

    native_strata = []
    for declared in spec["native_strata"]:
        stratum_id = declared["id"]
        matches = [row for row in raw_native if native_predicates[stratum_id](row)]

        def native_payload(row: dict[str, Any], stratum_id: str = stratum_id) -> dict[str, Any]:
            return {
                "stratum_id": stratum_id,
                "item_id": row["item_id"],
                "source_id": row["source_id"],
                "gold_label": {
                    "gold_action": row["gold_action"],
                    "gold_sufficient": row["gold_sufficient"],
                },
                "system_predictions_or_correctness": {
                    "paper_action_correct": row["paper_action_correct"],
                    "clinical_control_action_correct": row["clinical_control_action_correct"],
                },
                "selection_scores_if_native": {
                    "paper": row["paper_selection_score"],
                    "clinical_control": row["clinical_control_selection_score"],
                    "paper_target_0_8_threshold": paper_threshold,
                    "clinical_control_target_0_8_threshold": control_threshold,
                },
            }

        native_strata.append(
            {
                "id": stratum_id,
                "predicate": declared["predicate"],
                "member_count": len(matches),
                "selected": _select_examples(matches, count, native_payload),
            }
        )

    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "selection_rule_id": spec["selection_rule_id"],
        "selection_count_per_stratum": count,
        "clinical_text_used_for_selection": False,
        "raw_clinical_text_export": False,
        "ranking": "source_id ascending lexicographic, then item_id ascending for deterministic tie-break",
        "pubmedqa_strata": pubmed_strata,
        "native_strata": native_strata,
    }


def _evidence_packets() -> dict[str, Any]:
    packets = [
        {
            "packet_id": "EP-SG23-ACTION-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
            ],
            "derived_artifacts": ["main_results.json"],
            "scope": "PubMedQA action-selection descriptive results and frozen paired-bootstrap comparison",
        },
        {
            "packet_id": "EP-SG23-CAL-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(CALIBRATION_PATH),
            ],
            "derived_artifacts": ["reliability_source_data.json"],
            "scope": "DAL/control reliability only; Laya calibration remains excluded",
        },
        {
            "packet_id": "EP-SG23-SELECTIVE-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
            ],
            "derived_artifacts": ["selective_results.json", "risk_coverage_source_data.json"],
            "scope": "native-abstention risk/coverage and frozen target-policy outcomes",
        },
        {
            "packet_id": "EP-SG23-ECAL-001",
            "status": "supported-development-calibration-only",
            "canonical_sources": [_rel(ECAL_PATH), _rel(CALIBRATION_PATH)],
            "derived_artifacts": [],
            "scope": "frozen ECAL selection; no new final-test ECAL ablation",
        },
        {
            "packet_id": "EP-SG23-FHIR-BLOCK-001",
            "status": "supported-blocked-result",
            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-fhir-interface-block.json"),
                _rel(FHIR_SELECTION_PATH),
            ],
            "derived_artifacts": ["fhir_block_table.json"],
            "scope": "pre-execution FHIR interface block only; no final FHIR performance claim",
        },
        {
            "packet_id": "EP-SG23-ERROR-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "raw-laya-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
                _rel(CONTRACT_PATH),
            ],
            "derived_artifacts": ["qualitative_examples.json"],
            "scope": "content-blind deterministic qualitative strata and selected examples",
        },
        {
            "packet_id": "EP-SG23-TABLES-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(MATRIX_PATH),
                _rel(CONTRACT_PATH),
            ],
            "derived_artifacts": [
                "main_results.json",
                "selective_results.json",
                "evidence_boundaries.json",
                "fhir_block_table.json",
            ],
            "scope": "paper-table source data with blocked/null outcomes preserved",
        },
        {
            "packet_id": "EP-SG23-FIGURES-001",
            "status": "supported",
            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
                _rel(CONTRACT_PATH),
            ],
            "derived_artifacts": ["reliability_source_data.json", "risk_coverage_source_data.json"],
            "scope": "paper-figure source data without smoothing or threshold refit",
        },
    ]
    return {"schema_version": "0.1", "grain_id": "SG-000023", "packets": packets}


def _claim_ledger(metrics: dict[str, Any]) -> dict[str, Any]:
    paper_native = metrics["native_abstention"]["paper"]
    control_native = metrics["native_abstention"]["clinical_control"]
    claims = [
        {
            "claim_id": "SG23-C001",
            "status": "supported",
            "exportable": True,
            "text": "On the frozen PubMedQA PQA-L final rows, the paper system and clinical control each achieved action accuracy 0.552.",
            "evidence_packet_id": "EP-SG23-ACTION-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json")],
        },
        {
            "claim_id": "SG23-C002",
            "status": "supported-descriptive-only",
            "exportable": True,
            "text": "The frozen paper-minus-control PubMedQA action-accuracy estimate is 0.0 with a 95% paired-bootstrap interval [0.0, 0.0]; this does not support a superiority claim.",
            "evidence_packet_id": "EP-SG23-ACTION-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json")],
        },
        {
            "claim_id": "SG23-C003",
            "status": "supported-with-calibration-limitation",
            "exportable": True,
            "text": "Laya completed 500 frozen PubMedQA rows with action accuracy 0.53; affected Laya confidence is excluded from reliability/calibration figures as uncalibrated.",
            "evidence_packet_id": "EP-SG23-ACTION-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json"), _rel(CALIBRATION_PATH)],
        },
        {
            "claim_id": "SG23-C004",
            "status": "supported-negative-result",
            "exportable": True,
            "text": (
                "At the frozen native target-coverage 0.8 policy, the paper system achieved actual coverage "
                f"{paper_native['actual_policy']['0.8']['actual_coverage']} with unsafe-commit rate "
                f"{paper_native['actual_policy']['0.8']['unsafe_commit_rate']}, while the clinical control achieved actual coverage "
                f"{control_native['actual_policy']['0.8']['actual_coverage']} with unsafe-commit rate "
                f"{control_native['actual_policy']['0.8']['unsafe_commit_rate']}."
            ),
            "evidence_packet_id": "EP-SG23-SELECTIVE-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json")],
        },
        {
            "claim_id": "SG23-C005",
            "status": "supported-descriptive-only",
            "exportable": True,
            "text": f"Frozen native risk@80 is {paper_native['risk_at_80']} for the paper system and {control_native['risk_at_80']} for the clinical control; this is descriptive and is not exported as a superiority claim.",
            "evidence_packet_id": "EP-SG23-SELECTIVE-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json")],
        },
        {
            "claim_id": "SG23-C006",
            "status": "supported-blocked-result",
            "exportable": True,
            "text": "FHIR-AgentBench final action selection is blocked pre-execution because the frozen adapter cannot represent variable candidate action sets; zero gold rows were loaded and no replacement adapter is permitted.",
            "evidence_packet_id": "EP-SG23-FHIR-BLOCK-001",
            "canonical_source_paths": [_rel(FINAL_ROOT / "raw-fhir-interface-block.json")],
        },
        {
            "claim_id": "SG23-C007",
            "status": "blocked",
            "exportable": False,
            "text": "Medical evidence-intervention effectiveness is not supported because canonical P06 evidence is synthetic/mechanics-only.",
            "evidence_packet_id": None,
            "canonical_source_paths": [_rel(MATRIX_PATH)],
        },
        {
            "claim_id": "SG23-C008",
            "status": "unavailable",
            "exportable": False,
            "text": "Preregistered distribution-shift slice effects are unavailable because no valid frozen slice semantics are bound to final rows.",
            "evidence_packet_id": None,
            "canonical_source_paths": [_rel(MATRIX_PATH)],
        },
        {
            "claim_id": "SG23-C009",
            "status": "blocked",
            "exportable": False,
            "text": "Direct latency, throughput, and peak-memory superiority are not supported by the canonical final evidence.",
            "evidence_packet_id": None,
            "canonical_source_paths": [_rel(MATRIX_PATH)],
        },
        {
            "claim_id": "SG23-C010",
            "status": "not-claimed",
            "exportable": False,
            "text": "Superiority, clinical safety, SOTA, final FHIR performance, and direct efficiency superiority are not claimed.",
            "evidence_packet_id": None,
            "canonical_source_paths": [_rel(FINAL_ROOT / "metrics.json"), _rel(CONTRACT_PATH)],
        },
    ]
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "claim_ledger_id": "sg23-claim-ledger-v0.1",
        "claims": claims,
    }


def _build_base_artifacts() -> dict[str, Any]:
    metrics = _load(FINAL_ROOT / "metrics.json")
    raw_pubmed = _load(FINAL_ROOT / "raw-pubmedqa-predictions.json")
    raw_laya = _load(FINAL_ROOT / "raw-laya-pubmedqa-predictions.json")
    raw_native = _load(FINAL_ROOT / "raw-native-abstention-predictions.json")
    raw_fhir = _load(FINAL_ROOT / "raw-fhir-interface-block.json")
    contract = _load(CONTRACT_PATH)
    matrix = _load(MATRIX_PATH)

    return {
        "main_results.json": _main_results(metrics, contract),
        "selective_results.json": _selective_results(metrics, contract),
        "evidence_boundaries.json": _evidence_boundaries(matrix),
        "reliability_source_data.json": _reliability(raw_pubmed, metrics, contract),
        "risk_coverage_source_data.json": _risk_coverage(raw_native, metrics, contract),
        "fhir_block_table.json": _fhir_block(raw_fhir),
        "qualitative_examples.json": _qualitative(
            raw_pubmed, raw_laya, raw_native, metrics, contract
        ),
        "evidence_packets.json": _evidence_packets(),
        "claim_ledger.json": _claim_ledger(metrics),
    }


def _provenance_index(artifacts: dict[str, Any]) -> dict[str, Any]:
    source_paths = [
        CONTRACT_PATH,
        MATRIX_PATH,
        CALIBRATION_PATH,
        ECAL_PATH,
        FHIR_SELECTION_PATH,
        FINAL_ROOT / "manifest.json",
        FINAL_ROOT / "metrics.json",
        FINAL_ROOT / "raw-fhir-interface-block.json",
        FINAL_ROOT / "raw-laya-pubmedqa-predictions.json",
        FINAL_ROOT / "raw-native-abstention-predictions.json",
        FINAL_ROOT / "raw-pubmedqa-predictions.json",
        FINAL_ROOT / "summary.json",
    ]
    source_digests = {_rel(path): _sha256_path(path) for path in source_paths}
    artifact_digests = {
        filename: _sha256_bytes(_dump(payload).encode("utf-8"))
        for filename, payload in artifacts.items()
    }
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "index_id": "sg23-paper-evidence-provenance-v0.1",
        "canonical_main_dependency": "d676beccfec001fd75d1b157b43068eb49a5733d",
        "derivation_contract_id": "dal-p08-post-final-derivation-v0.1",
        "no_new_inference": True,
        "no_post_test_tuning": True,
        "source_sha256": source_digests,
        "artifact_sha256": artifact_digests,
    }


def build_artifacts() -> dict[str, Any]:
    artifacts = _build_base_artifacts()
    artifacts["provenance_index.json"] = _provenance_index(artifacts)
    return artifacts


def write_artifacts(output_dir: Path, artifacts: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in artifacts.items():
        (output_dir / filename).write_text(_dump(payload), encoding="utf-8", newline="\n")


def check_artifacts(output_dir: Path, artifacts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_names = set(artifacts)
    actual_names = (
        {path.name for path in output_dir.glob("*.json")} if output_dir.is_dir() else set()
    )
    if actual_names != expected_names:
        errors.append(
            f"artifact set mismatch: actual={sorted(actual_names)} expected={sorted(expected_names)}"
        )
    for filename, payload in artifacts.items():
        path = output_dir / filename
        if not path.is_file():
            errors.append(f"missing artifact: {filename}")
            continue
        expected = _dump(payload)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"artifact differs from deterministic rebuild: {filename}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic SG-000023 paper evidence artifacts"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless committed artifacts match a deterministic rebuild",
    )
    args = parser.parse_args()

    artifacts = build_artifacts()
    if args.check:
        errors = check_artifacts(args.output_dir, artifacts)
        if errors:
            for error in errors:
                print(error)
            return 1
        print(f"SG-000023 paper evidence check passed: {len(artifacts)} artifacts")
        return 0

    write_artifacts(args.output_dir, artifacts)
    print(f"SG-000023 paper evidence built: {len(artifacts)} artifacts -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
