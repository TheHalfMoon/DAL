# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Callable, Iterator, Mapping
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

MANIFEST_PATH = FINAL_ROOT / "manifest.json"
METRICS_PATH = FINAL_ROOT / "metrics.json"
SUMMARY_PATH = FINAL_ROOT / "summary.json"
RAW_FHIR_PATH = FINAL_ROOT / "raw-fhir-interface-block.json"
RAW_LAYA_PATH = FINAL_ROOT / "raw-laya-pubmedqa-predictions.json"
RAW_NATIVE_PATH = FINAL_ROOT / "raw-native-abstention-predictions.json"
RAW_PUBMED_PATH = FINAL_ROOT / "raw-pubmedqa-predictions.json"

CANONICAL_MAIN_DEPENDENCY = "d676beccfec001fd75d1b157b43068eb49a5733d"

# Byte-level SHA-256 of every canonical input, pinned at the canonical main dependency.
# The builder refuses to derive anything when a checkout input differs from these digests,
# so a mutated post-test input cannot be regenerated into a passing ``--check``.
FROZEN_SOURCE_SHA256: dict[Path, str] = {
    CONTRACT_PATH: "62982bb53ad8cbe6255825c319528d9f50a893b142fbcffd7c55f6b99294fb38",
    MATRIX_PATH: "3a319a13dc18dbe49e063479e2698850b6fb7a3b8968d67c6f3f0f0fd43e496b",
    CALIBRATION_PATH: "1e9ed4558180d07756d4992b6c46963692695ed1fbc8e6ccb01a90a25c003eb6",
    ECAL_PATH: "db77c67ed1041fdb21fed771c1de97e134a1635076bc2254bfe8c8512599c793",
    FHIR_SELECTION_PATH: "0965e516b642c11d305223ac0725e99af7f4002b3252dc10203bc532ec877647",
    MANIFEST_PATH: "6ac53a51eb6caf373a691333c8241b2b7301cde81caa0dda02871154ba2b6dd1",
    METRICS_PATH: "da2e41e7ecda10c2f7dad60b28ad386e160f028b58f76414d7645512633161db",
    RAW_FHIR_PATH: "b8cb7b96241568f7089291614c2157a2656141be16297b0b81791c6cd71893eb",
    RAW_LAYA_PATH: "009831a7a404f8cfc44ea83b13d0ecf8d6e9fb4bdd6c511c2835ec2595a69102",
    RAW_NATIVE_PATH: "5f6b593396dd426eee479bec0aaaadba90e0e44b4ef3e55266ba8c7c702ba8da",
    RAW_PUBMED_PATH: "402c655da798085d68fa54fbcd63c140a0c0cea389113b684315fcbd1e9fbed9",
    SUMMARY_PATH: "49b9f84830afed365b45c4e23f7ff38e5894c990f0af1cd26bf8160612aa0426",
}

PROVENANCE_INDEX_NAME = "provenance_index.json"

# Every generated artifact except the provenance index. The provenance index hashes these
# artifacts and therefore cannot contain its own digest; the package is BASE + provenance index.
BASE_ARTIFACT_NAMES: tuple[str, ...] = (
    "main_results.json",
    "selective_results.json",
    "evidence_boundaries.json",
    "reliability_source_data.json",
    "risk_coverage_source_data.json",
    "fhir_block_table.json",
    "qualitative_examples.json",
    "evidence_packets.json",
    "claim_ledger.json",
)
ARTIFACT_NAMES: tuple[str, ...] = (*BASE_ARTIFACT_NAMES, PROVENANCE_INDEX_NAME)

# Exact canonical inputs read by each derivation. Derivations receive a view restricted to
# these paths; reading an undeclared path or declaring an unread path fails the build.
ARTIFACT_INPUTS: dict[str, tuple[Path, ...]] = {
    "main_results.json": (METRICS_PATH, CONTRACT_PATH),
    "selective_results.json": (METRICS_PATH, CONTRACT_PATH),
    "evidence_boundaries.json": (MATRIX_PATH,),
    "reliability_source_data.json": (RAW_PUBMED_PATH, METRICS_PATH, CONTRACT_PATH, MANIFEST_PATH),
    "risk_coverage_source_data.json": (RAW_NATIVE_PATH, METRICS_PATH, CONTRACT_PATH),
    "fhir_block_table.json": (RAW_FHIR_PATH,),
    "qualitative_examples.json": (
        RAW_PUBMED_PATH,
        RAW_LAYA_PATH,
        RAW_NATIVE_PATH,
        METRICS_PATH,
        CONTRACT_PATH,
    ),
    "evidence_packets.json": (MATRIX_PATH,),
    "claim_ledger.json": (METRICS_PATH, MANIFEST_PATH, RAW_FHIR_PATH, CONTRACT_PATH, MATRIX_PATH),
    PROVENANCE_INDEX_NAME: tuple(FROZEN_SOURCE_SHA256),
}

PENDING_PACKET_STATUS = "declared-pending-later-stage"

# Packet registry specification. ``canonical_sources`` of a packet is the union of the exact
# derivation inputs of its derived artifacts plus explicitly bound supporting sources that the
# packet cites without a derivation reading them.
PACKET_SPECS: tuple[dict[str, Any], ...] = (
    {
        "packet_id": "EP-SG23-ACTION-001",
        "matrix_row_id": "main-action-selection-tables",
        "status": "supported",
        "derived_artifacts": ["main_results.json"],
        "supporting_sources": [RAW_PUBMED_PATH, MANIFEST_PATH],
        "scope": "PubMedQA action-selection descriptive results and frozen paired-bootstrap comparison",
    },
    {
        "packet_id": "EP-SG23-CAL-001",
        "matrix_row_id": "reliability-analysis",
        "status": "supported",
        "derived_artifacts": ["reliability_source_data.json"],
        "supporting_sources": [CALIBRATION_PATH],
        "scope": "DAL/control reliability only; affected Laya confidence remains excluded as uncalibrated",
    },
    {
        "packet_id": "EP-SG23-SELECTIVE-001",
        "matrix_row_id": "risk-coverage-analysis",
        "status": "supported",
        "derived_artifacts": ["selective_results.json", "risk_coverage_source_data.json"],
        "supporting_sources": [CALIBRATION_PATH],
        "scope": "native-abstention risk/coverage and frozen target-policy outcomes",
    },
    {
        "packet_id": "EP-SG23-ECAL-001",
        "matrix_row_id": "ecal-reporting",
        "status": "supported-development-calibration-only",
        "derived_artifacts": [],
        "supporting_sources": [ECAL_PATH, CALIBRATION_PATH],
        "scope": "frozen ECAL selection; no new final-test ECAL ablation",
    },
    {
        "packet_id": "EP-SG23-FHIR-BLOCK-001",
        "matrix_row_id": "fhir-final-action-selection",
        "status": "supported-blocked-result",
        "derived_artifacts": ["fhir_block_table.json"],
        "supporting_sources": [FHIR_SELECTION_PATH, METRICS_PATH],
        "scope": "pre-execution FHIR interface block only; no final FHIR performance claim",
    },
    {
        "packet_id": "EP-SG23-ERROR-001",
        "matrix_row_id": "failure-taxonomy-and-qualitative-errors",
        "status": "supported",
        "derived_artifacts": ["qualitative_examples.json"],
        "supporting_sources": [],
        "scope": "content-blind deterministic qualitative strata and selected examples",
    },
    {
        "packet_id": "EP-SG23-TABLES-001",
        "matrix_row_id": "paper-tables",
        "status": "supported",
        "derived_artifacts": [
            "main_results.json",
            "selective_results.json",
            "evidence_boundaries.json",
            "fhir_block_table.json",
        ],
        "supporting_sources": [],
        "scope": "paper-table source data with blocked/null outcomes preserved",
    },
    {
        "packet_id": "EP-SG23-FIGURES-001",
        "matrix_row_id": "paper-figures",
        "status": "supported",
        "derived_artifacts": ["reliability_source_data.json", "risk_coverage_source_data.json"],
        "supporting_sources": [],
        "scope": "paper-figure source data without smoothing or threshold refit",
    },
    {
        "packet_id": "EP-SG23-PACKETS-INDEX",
        "matrix_row_id": "evidence-packets",
        "status": "supported",
        "derived_artifacts": ["evidence_packets.json", PROVENANCE_INDEX_NAME],
        "supporting_sources": [],
        "scope": "evidence-packet registry and byte-level provenance index for this package",
    },
    {
        "packet_id": "EP-SG23-CLAIMS-INDEX",
        "matrix_row_id": "claim-ledger",
        "status": "supported",
        "derived_artifacts": ["claim_ledger.json"],
        "supporting_sources": [],
        "scope": "machine-readable claim ledger with supported, null, negative, blocked, and unavailable dispositions",
    },
    {
        "packet_id": "EP-SG23-LIT-001",
        "matrix_row_id": "related-work-refresh",
        "status": PENDING_PACKET_STATUS,
        "derived_artifacts": [],
        "supporting_sources": [],
        "scope": "dated related-work refresh and novelty disposition",
        "pending_reason": "Related-work refresh evidence is produced by a later SG-000023 stage; this package contains no literature evidence and supports no novelty claim.",
    },
    {
        "packet_id": "EP-SG23-FREEZE-001",
        "matrix_row_id": "p08-final-result-freeze",
        "status": PENDING_PACKET_STATUS,
        "derived_artifacts": [],
        "supporting_sources": [],
        "scope": "P08 final result and claim freeze manifest",
        "pending_reason": "The final result/claim freeze is a later SG-000023 governance stage that requires the related-work refresh; this package does not freeze claims.",
    },
)

DISPLAY_DECIMALS = 4
DISPLAY_RULE = (
    "presentation-only fixed-point rounding to 4 decimal places; the unrounded canonical "
    "values remain in primary_comparison and are the scientific evidence"
)


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


def _display(value: float) -> str:
    return f"{value:.{DISPLAY_DECIMALS}f}"


class SourceView(Mapping[Path, Any]):
    """Read-only view over loaded canonical sources restricted to declared inputs."""

    def __init__(self, loaded: Mapping[Path, Any], allowed: tuple[Path, ...]) -> None:
        self._loaded = loaded
        self._allowed = frozenset(allowed)
        self.accessed: set[Path] = set()

    def __getitem__(self, key: Path) -> Any:
        if key not in self._allowed:
            raise KeyError(f"undeclared canonical source read: {_rel(key)}")
        self.accessed.add(key)
        return self._loaded[key]

    def __iter__(self) -> Iterator[Path]:
        return iter(sorted(self._allowed))

    def __len__(self) -> int:
        return len(self._allowed)


def verify_frozen_sources() -> list[str]:
    """Return digest violations of canonical inputs; an empty list means all inputs are frozen."""
    errors: list[str] = []
    for path, expected in FROZEN_SOURCE_SHA256.items():
        if not path.is_file():
            errors.append(f"missing canonical source: {_rel(path)}")
            continue
        actual = _sha256_path(path)
        if actual != expected:
            errors.append(f"canonical source digest mismatch: {_rel(path)} {actual} != {expected}")
    if errors:
        return errors
    manifest = _load(MANIFEST_PATH)
    for filename, record in sorted(manifest["artifacts"].items()):
        path = FINAL_ROOT / filename
        if path not in FROZEN_SOURCE_SHA256:
            errors.append(f"final manifest artifact not pinned by builder: {filename}")
        elif record["byte_sha256"] != FROZEN_SOURCE_SHA256[path]:
            errors.append(f"final manifest digest disagrees with builder pin: {filename}")
    return errors


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


def _comparison_display(comparison: dict[str, Any]) -> dict[str, Any]:
    bootstrap = comparison["paired_bootstrap"]
    return {
        "estimate": _display(bootstrap["estimate"]),
        "ci_low": _display(bootstrap["ci_low"]),
        "ci_high": _display(bootstrap["ci_high"]),
        "ci_level": bootstrap["ci_level"],
        "rule": DISPLAY_RULE,
    }


def _primary_comparison(metrics: dict[str, Any], benchmark: str, metric: str) -> dict[str, Any]:
    return dict(
        next(
            row
            for row in metrics["primary_comparisons"]
            if row["benchmark"] == benchmark and row["metric"] == metric
        )
    )


def _main_results(src: SourceView) -> dict[str, Any]:
    metrics = src[METRICS_PATH]
    spec = src[CONTRACT_PATH]["paper_outputs"]["main_results_table"]
    pubmed = metrics["pubmedqa"]
    rows = [
        _metric_row(system_id, pubmed[system_id], spec["metrics"]) for system_id in spec["systems"]
    ]
    comparison = _primary_comparison(metrics, "pubmedqa-pqal", "action_accuracy")
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-main-action-selection-v0.1",
        "rows": rows,
        "primary_comparison": comparison,
        "primary_comparison_display": _comparison_display(comparison),
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


def _selective_results(src: SourceView) -> dict[str, Any]:
    metrics = src[METRICS_PATH]
    spec = src[CONTRACT_PATH]["paper_outputs"]["selective_results_table"]
    native = metrics["native_abstention"]
    rows = [
        _selective_row(system_id, native[system_id], spec["metrics"])
        for system_id in spec["systems"]
    ]
    comparison = _primary_comparison(metrics, "gax-native-abstention-pqal", "risk_at_80")
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "table_id": "sg23-native-selective-v0.1",
        "rows": rows,
        "primary_comparison": comparison,
        "primary_comparison_display": _comparison_display(comparison),
        "mandatory_warning": (
            "The paper system has unsafe_commit_rate=1.0 at frozen target coverages 0.8 and 0.9; "
            "these negative outcomes must remain visible."
        ),
    }


def _evidence_boundaries(src: SourceView) -> dict[str, Any]:
    include = {"blocked", "unavailable", "not-applicable"}
    rows = []
    for row in src[MATRIX_PATH]["rows"]:
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
            mean_confidence = math.fsum(item[0] for item in members) / len(members)
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


def _reliability(src: SourceView) -> dict[str, Any]:
    raw_pubmed = src[RAW_PUBMED_PATH]
    metrics = src[METRICS_PATH]
    spec = src[CONTRACT_PATH]["paper_outputs"]["reliability_figure"]
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
        "bin_edges": spec["bin_edges"],
        "systems": systems,
        "laya_disposition": spec["laya_policy"],
        "laya_runtime_warning": src[MANIFEST_PATH]["laya_runtime_warning"],
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

    computed_aurc = math.fsum(point["risk"] for point in points) / len(points)
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


def _risk_coverage(src: SourceView) -> dict[str, Any]:
    raw_native = src[RAW_NATIVE_PATH]
    metrics = src[METRICS_PATH]
    spec = src[CONTRACT_PATH]["paper_outputs"]["risk_coverage_figure"]
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
        "ordering": spec["ordering"],
        "no_smoothing": spec["no_smoothing"],
        "no_threshold_refit": spec["no_threshold_refit"],
        "systems": systems,
    }


def _fhir_block(src: SourceView) -> dict[str, Any]:
    raw_fhir = src[RAW_FHIR_PATH]
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


def _qualitative(src: SourceView) -> dict[str, Any]:
    raw_pubmed = src[RAW_PUBMED_PATH]
    raw_laya = src[RAW_LAYA_PATH]
    raw_native = src[RAW_NATIVE_PATH]
    metrics = src[METRICS_PATH]
    spec = src[CONTRACT_PATH]["qualitative_error_selection"]
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


def _matrix_packet_ids(matrix: dict[str, Any]) -> list[str]:
    return [packet_id for row in matrix["rows"] for packet_id in row["evidence_packet_ids"]]


def _evidence_packets(src: SourceView) -> dict[str, Any]:
    matrix_rows = {row["id"]: row for row in src[MATRIX_PATH]["rows"]}
    packets = []
    for spec in PACKET_SPECS:
        row = matrix_rows[spec["matrix_row_id"]]
        if spec["packet_id"] not in row["evidence_packet_ids"]:
            raise ValueError(
                f"packet {spec['packet_id']} is not declared by matrix row {spec['matrix_row_id']}"
            )
        derivation_inputs = sorted(
            {_rel(path) for name in spec["derived_artifacts"] for path in ARTIFACT_INPUTS[name]}
        )
        supporting = sorted(_rel(path) for path in spec["supporting_sources"])
        packet: dict[str, Any] = {
            "packet_id": spec["packet_id"],
            "matrix_row_id": spec["matrix_row_id"],
            "matrix_row_status": row["status"],
            "status": spec["status"],
            "derived_artifacts": list(spec["derived_artifacts"]),
            "derivation_inputs": derivation_inputs,
            "supporting_sources": supporting,
            "canonical_sources": sorted(set(derivation_inputs) | set(supporting)),
            "scope": spec["scope"],
        }
        if "pending_reason" in spec:
            packet["pending_reason"] = spec["pending_reason"]
        packets.append(packet)
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "source_semantics": {
            "derivation_inputs": "exact canonical files read by the derivations of the packet's derived artifacts",
            "supporting_sources": "canonical files the packet binds as supporting evidence without a derivation reading them",
            "canonical_sources": "union of derivation_inputs and supporting_sources",
            PENDING_PACKET_STATUS: "packet declared by the availability matrix whose evidence is produced by a later SG-000023 stage; it supports no claim",
        },
        "packets": packets,
    }


def _claim(
    claim_id: str,
    status: str,
    exportable: bool,
    text: str,
    packet_id: str | None,
    sources: list[Path],
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "status": status,
        "exportable": exportable,
        "text": text,
        "evidence_packet_id": packet_id,
        "canonical_source_paths": [_rel(path) for path in sources],
    }


def _claim_ledger(src: SourceView) -> dict[str, Any]:
    metrics = src[METRICS_PATH]
    laya_warning = src[MANIFEST_PATH]["laya_runtime_warning"]
    raw_fhir = src[RAW_FHIR_PATH]
    laya_policy = src[CONTRACT_PATH]["paper_outputs"]["reliability_figure"]["laya_policy"]
    src[MATRIX_PATH]  # C007-C009 cite matrix dispositions
    pubmed = metrics["pubmedqa"]
    pubmed_comparison = _primary_comparison(metrics, "pubmedqa-pqal", "action_accuracy")
    pubmed_display = _comparison_display(pubmed_comparison)
    paper_native = metrics["native_abstention"]["paper"]
    control_native = metrics["native_abstention"]["clinical_control"]
    native_display = _comparison_display(
        _primary_comparison(metrics, "gax-native-abstention-pqal", "risk_at_80")
    )
    fhir_requested = sorted({system["requested"] for system in raw_fhir["systems"]})
    if not laya_warning["observed"] or "uncalibrated" not in laya_policy:
        raise ValueError("Laya calibration limitation evidence is missing")
    claims = [
        _claim(
            "SG23-C001",
            "supported",
            True,
            f"On the frozen PubMedQA PQA-L final rows, the paper system achieved action accuracy {pubmed['paper']['accuracy']} and the clinical control achieved action accuracy {pubmed['clinical_control']['accuracy']}.",
            "EP-SG23-ACTION-001",
            [METRICS_PATH],
        ),
        _claim(
            "SG23-C002",
            "supported-descriptive-only",
            True,
            f"The frozen paper-minus-control PubMedQA action-accuracy estimate is {pubmed_display['estimate']} with a 95% paired-bootstrap interval [{pubmed_display['ci_low']}, {pubmed_display['ci_high']}]; this does not support a superiority claim.",
            "EP-SG23-ACTION-001",
            [METRICS_PATH],
        ),
        _claim(
            "SG23-C003",
            "supported-with-calibration-limitation",
            True,
            f"Laya completed {pubmed['laya']['completed']} of {pubmed['laya']['requested']} frozen PubMedQA rows with action accuracy {pubmed['laya']['accuracy']}; affected Laya confidence is excluded from reliability/calibration figures as uncalibrated.",
            "EP-SG23-CAL-001",
            [METRICS_PATH, MANIFEST_PATH, CONTRACT_PATH],
        ),
        _claim(
            "SG23-C004",
            "supported-negative-result",
            True,
            (
                "At the frozen native target-coverage 0.8 policy, the paper system achieved actual coverage "
                f"{paper_native['actual_policy']['0.8']['actual_coverage']} with unsafe-commit rate "
                f"{paper_native['actual_policy']['0.8']['unsafe_commit_rate']}, while the clinical control achieved actual coverage "
                f"{control_native['actual_policy']['0.8']['actual_coverage']} with unsafe-commit rate "
                f"{control_native['actual_policy']['0.8']['unsafe_commit_rate']}."
            ),
            "EP-SG23-SELECTIVE-001",
            [METRICS_PATH],
        ),
        _claim(
            "SG23-C005",
            "supported-descriptive-only",
            True,
            f"Frozen native risk@80 is {paper_native['risk_at_80']} for the paper system and {control_native['risk_at_80']} for the clinical control (paper-minus-control estimate {native_display['estimate']}, 95% paired-bootstrap interval [{native_display['ci_low']}, {native_display['ci_high']}], lower is better); this is descriptive and is not exported as a superiority claim.",
            "EP-SG23-SELECTIVE-001",
            [METRICS_PATH],
        ),
        _claim(
            "SG23-C006",
            "supported-blocked-result",
            True,
            f"FHIR-AgentBench final action selection is blocked pre-execution because the frozen adapter cannot represent variable candidate action sets; {raw_fhir['gold_rows_loaded']} gold rows were loaded for a requested denominator of {fhir_requested[0] if len(fhir_requested) == 1 else fhir_requested}, and no replacement adapter is permitted.",
            "EP-SG23-FHIR-BLOCK-001",
            [RAW_FHIR_PATH],
        ),
        _claim(
            "SG23-C007",
            "blocked",
            False,
            "Medical evidence-intervention effectiveness is not supported because canonical P06 evidence is synthetic/mechanics-only.",
            None,
            [MATRIX_PATH],
        ),
        _claim(
            "SG23-C008",
            "unavailable",
            False,
            "Preregistered distribution-shift slice effects are unavailable because no valid frozen slice semantics are bound to final rows.",
            None,
            [MATRIX_PATH],
        ),
        _claim(
            "SG23-C009",
            "blocked",
            False,
            "Direct latency, throughput, and peak-memory superiority are not supported by the canonical final evidence.",
            None,
            [MATRIX_PATH],
        ),
        _claim(
            "SG23-C010",
            "not-claimed",
            False,
            "Superiority, clinical safety, SOTA, final FHIR performance, and direct efficiency superiority are not claimed.",
            None,
            [METRICS_PATH, CONTRACT_PATH],
        ),
    ]
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "claim_ledger_id": "sg23-claim-ledger-v0.1",
        "claims": claims,
    }


DERIVATIONS: dict[str, Callable[[SourceView], dict[str, Any]]] = {
    "main_results.json": _main_results,
    "selective_results.json": _selective_results,
    "evidence_boundaries.json": _evidence_boundaries,
    "reliability_source_data.json": _reliability,
    "risk_coverage_source_data.json": _risk_coverage,
    "fhir_block_table.json": _fhir_block,
    "qualitative_examples.json": _qualitative,
    "evidence_packets.json": _evidence_packets,
    "claim_ledger.json": _claim_ledger,
}


def _build_base_artifacts(loaded: Mapping[Path, Any]) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for name in BASE_ARTIFACT_NAMES:
        inputs = ARTIFACT_INPUTS[name]
        view = SourceView(loaded, inputs)
        payload = DERIVATIONS[name](view)
        unread = set(inputs) - view.accessed
        if unread:
            raise ValueError(
                f"{name} declares unread canonical sources: {sorted(_rel(p) for p in unread)}"
            )
        payload["canonical_sources"] = sorted(_rel(path) for path in inputs)
        artifacts[name] = payload
    return artifacts


def _provenance_index(artifacts: dict[str, Any]) -> dict[str, Any]:
    source_digests = {_rel(path): digest for path, digest in sorted(FROZEN_SOURCE_SHA256.items())}
    artifact_digests = {
        filename: _sha256_bytes(_dump(artifacts[filename]).encode("utf-8"))
        for filename in BASE_ARTIFACT_NAMES
    }
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000023",
        "index_id": "sg23-paper-evidence-provenance-v0.1",
        "canonical_main_dependency": CANONICAL_MAIN_DEPENDENCY,
        "derivation_contract_id": "dal-p08-post-final-derivation-v0.1",
        "no_new_inference": True,
        "no_post_test_tuning": True,
        "frozen_source_digests_verified_before_derivation": True,
        "artifact_inventory": list(ARTIFACT_NAMES),
        "self_hash_exclusion": f"{PROVENANCE_INDEX_NAME} cannot contain its own digest; artifact_sha256 covers every other artifact in artifact_inventory",
        "canonical_sources": sorted(source_digests),
        "source_sha256": source_digests,
        "artifact_sha256": artifact_digests,
    }


def validate_package(artifacts: dict[str, Any], matrix: dict[str, Any]) -> list[str]:
    """Mechanically validate matrix/packet/claim/source consistency of a built package."""
    errors: list[str] = []
    if tuple(artifacts) != ARTIFACT_NAMES:
        errors.append(f"artifact inventory mismatch: {list(artifacts)}")

    packets = artifacts["evidence_packets.json"]["packets"]
    packet_ids = [packet["packet_id"] for packet in packets]
    declared_ids = _matrix_packet_ids(matrix)
    if len(set(packet_ids)) != len(packet_ids):
        errors.append("duplicate packet IDs in packet registry")
    if len(set(declared_ids)) != len(declared_ids):
        errors.append("duplicate packet IDs declared by availability matrix")
    if set(packet_ids) != set(declared_ids):
        errors.append(
            "packet registry does not match availability matrix: "
            f"missing={sorted(set(declared_ids) - set(packet_ids))} "
            f"undeclared={sorted(set(packet_ids) - set(declared_ids))}"
        )
    by_id = {packet["packet_id"]: packet for packet in packets}
    matrix_rows = {row["id"]: row for row in matrix["rows"]}
    for packet in packets:
        row = matrix_rows.get(packet["matrix_row_id"])
        if row is None:
            errors.append(f"packet {packet['packet_id']} binds unknown matrix row")
            continue
        if packet["packet_id"] not in row["evidence_packet_ids"]:
            errors.append(f"packet {packet['packet_id']} is not declared by matrix row {row['id']}")
        if packet["matrix_row_status"] != row["status"]:
            errors.append(f"packet {packet['packet_id']} misstates matrix row status")

    covered: set[str] = set()
    for packet in packets:
        pending = packet["status"] == PENDING_PACKET_STATUS
        if pending and (packet["derived_artifacts"] or packet["canonical_sources"]):
            errors.append(f"pending packet carries evidence: {packet['packet_id']}")
        if pending and not packet.get("pending_reason"):
            errors.append(f"pending packet lacks reason: {packet['packet_id']}")
        if not pending and not packet["canonical_sources"]:
            errors.append(f"packet without canonical sources: {packet['packet_id']}")
        for name in packet["derived_artifacts"]:
            if name not in artifacts:
                errors.append(f"packet {packet['packet_id']} binds unknown artifact {name}")
                continue
            covered.add(name)
            actual = artifacts[name]["canonical_sources"]
            if not set(actual) <= set(packet["canonical_sources"]):
                errors.append(f"packet {packet['packet_id']} omits sources of {name}")
    uncovered = set(ARTIFACT_NAMES) - covered
    if uncovered:
        errors.append(f"artifacts not bound to any packet: {sorted(uncovered)}")

    for claim in artifacts["claim_ledger.json"]["claims"]:
        packet_id = claim["evidence_packet_id"]
        if claim["exportable"]:
            if packet_id is None:
                errors.append(f"exportable claim without packet: {claim['claim_id']}")
                continue
            if not claim["status"].startswith("supported"):
                errors.append(f"exportable claim without supported status: {claim['claim_id']}")
        if packet_id is None:
            continue
        packet = by_id.get(packet_id)
        if packet is None:
            errors.append(f"claim {claim['claim_id']} binds unknown packet {packet_id}")
            continue
        if packet["status"] == PENDING_PACKET_STATUS:
            errors.append(f"claim {claim['claim_id']} binds pending packet {packet_id}")
        missing = set(claim["canonical_source_paths"]) - set(packet["canonical_sources"])
        if missing:
            errors.append(
                f"claim {claim['claim_id']} cites sources outside packet {packet_id}: {sorted(missing)}"
            )
    return errors


def build_artifacts() -> dict[str, Any]:
    errors = verify_frozen_sources()
    if errors:
        raise ValueError("; ".join(errors))
    loaded = {path: _load(path) for path in FROZEN_SOURCE_SHA256}
    artifacts = _build_base_artifacts(loaded)
    artifacts[PROVENANCE_INDEX_NAME] = _provenance_index(artifacts)
    artifacts[PROVENANCE_INDEX_NAME]["canonical_sources"] = sorted(
        _rel(path) for path in ARTIFACT_INPUTS[PROVENANCE_INDEX_NAME]
    )
    errors = validate_package(artifacts, loaded[MATRIX_PATH])
    if errors:
        raise ValueError("; ".join(errors))
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
