# ruff: noqa: E501
"""Study 1 D1: non-destructive forensic diagnosis of the immutable Study 0 predictions.

Reads only the SG-000022 raw prediction artifacts, verified against their pinned byte digests,
and writes one diagnostic record. It changes no Study 0 artifact, claim, or result, and its
findings are diagnostic inputs to Study 1 design, never revisions of Study 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FINAL_ROOT = ROOT / "registry" / "p08_sg000022_final_evaluation"
OUTPUT = ROOT / "registry" / "study1_d1_pilot_diagnosis.json"

PINNED = {
    "raw-pubmedqa-predictions.json": "402c655da798085d68fa54fbcd63c140a0c0cea389113b684315fcbd1e9fbed9",
    "raw-laya-pubmedqa-predictions.json": "009831a7a404f8cfc44ea83b13d0ecf8d6e9fb4bdd6c511c2835ec2595a69102",
    "raw-native-abstention-predictions.json": "5f6b593396dd426eee479bec0aaaadba90e0e44b4ef3e55266ba8c7c702ba8da",
    "metrics.json": "da2e41e7ecda10c2f7dad60b28ad386e160f028b58f76414d7645512633161db",
}
LABELS = ("yes", "no", "maybe")
BINS = 15


def _load(name: str) -> Any:
    path = FINAL_ROOT / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PINNED[name]:
        raise ValueError(f"Study 0 artifact digest mismatch: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _classification(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    confusion = {gold: {pred: 0 for pred in LABELS} for gold in LABELS}
    for gold, pred in pairs:
        confusion[gold][pred] += 1
    per_class = {}
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[g][label] for g in LABELS if g != label)
        fn = sum(confusion[label][p] for p in LABELS if p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "support": tp + fn,
            "predicted": tp + fp,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    n = len(pairs)
    gold_counts = Counter(gold for gold, _ in pairs)
    majority_label, majority_count = max(gold_counts.items(), key=lambda item: (item[1], item[0]))
    return {
        "n": n,
        "gold_distribution": {label: gold_counts[label] for label in LABELS},
        "prediction_distribution": {
            label: sum(1 for _, p in pairs if p == label) for label in LABELS
        },
        "confusion_rows_gold_columns_predicted": confusion,
        "per_class": per_class,
        "accuracy": sum(confusion[label][label] for label in LABELS) / n,
        "macro_f1": math.fsum(per_class[label]["f1"] for label in LABELS) / len(LABELS),
        "balanced_accuracy": math.fsum(per_class[label]["recall"] for label in LABELS)
        / len(LABELS),
        "majority_class_baseline": {"label": majority_label, "accuracy": majority_count / n},
        "error_taxonomy": {
            f"{gold}->{pred}": confusion[gold][pred]
            for gold in LABELS
            for pred in LABELS
            if gold != pred and confusion[gold][pred]
        },
    }


def _class_calibration(rows: list[dict[str, Any]], key: str, gold_key: str) -> dict[str, Any]:
    """One-vs-rest calibration per class with 15 equal-width bins."""
    result = {}
    for label in LABELS:
        bins: list[list[tuple[float, bool]]] = [[] for _ in range(BINS)]
        for row in rows:
            p = float(row[key][label])
            bins[min(int(p * BINS), BINS - 1)].append((p, row[gold_key] == label))
        ece = math.fsum(
            (len(members) / len(rows))
            * abs(
                math.fsum(m[0] for m in members) / len(members)
                - sum(m[1] for m in members) / len(members)
            )
            for members in bins
            if members
        )
        probabilities = [float(row[key][label]) for row in rows]
        result[label] = {
            "mean_predicted_probability": math.fsum(probabilities) / len(rows),
            "empirical_frequency": sum(1 for row in rows if row[gold_key] == label) / len(rows),
            "min_probability": min(probabilities),
            "max_probability": max(probabilities),
            "one_vs_rest_ece_15_bins": ece,
        }
    return result


def _auroc(positive: list[float], negative: list[float]) -> float:
    wins = math.fsum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def _native(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for system in ("paper", "clinical_control"):
        key = f"{system}_selection_score"
        present = [float(r[key]) for r in rows if r["gold_sufficient"]]
        withheld = [float(r[key]) for r in rows if not r["gold_sufficient"]]
        policy = metrics["native_abstention"][system]["actual_policy"]
        out[system] = {
            "present_rows": len(present),
            "withheld_rows": len(withheld),
            "present_score_min": min(present),
            "present_score_max": max(present),
            "withheld_score_min": min(withheld),
            "withheld_score_max": max(withheld),
            "distinct_withheld_scores": len(set(withheld)),
            "present_vs_withheld_auroc": _auroc(present, withheld),
            "withheld_rows_at_or_above_frozen_threshold": {
                target: sum(1 for w in withheld if w >= policy[target]["threshold"])
                for target in sorted(policy)
            },
        }
    out["answerable_fraction"] = sum(1 for r in rows if r["gold_sufficient"]) / len(rows)
    return out


def build() -> dict[str, Any]:
    pubmed = _load("raw-pubmedqa-predictions.json")
    laya = {
        str(row["source_id"]): row
        for row in _load("raw-laya-pubmedqa-predictions.json")["predictions"]
    }
    native = _load("raw-native-abstention-predictions.json")
    metrics = _load("metrics.json")
    paper = _classification([(r["gold_action"], r["paper_predicted_action"]) for r in pubmed])
    control = _classification(
        [(r["gold_action"], r["clinical_control_predicted_action"]) for r in pubmed]
    )
    laya_cls = _classification(
        [(r["gold_action"], laya[str(r["source_id"])]["prediction"]) for r in pubmed]
    )
    confidences = [max(float(v) for v in r["paper_action_probabilities"].values()) for r in pubmed]
    native_diag = _native(native, metrics)
    paper_target = native_diag["paper"]["withheld_rows_at_or_above_frozen_threshold"]
    findings = {
        "F1-majority-class-collapse": (
            paper["prediction_distribution"]["yes"] == paper["n"]
            and paper["accuracy"] == paper["majority_class_baseline"]["accuracy"]
        ),
        "F2-paper-equals-control": paper == control,
        "F3-trivial-sufficiency-separation": (
            native_diag["paper"]["present_vs_withheld_auroc"] == 1.0
            and native_diag["paper"]["distinct_withheld_scores"] == 1
        ),
        "F4-coverage-targets-exceed-answerable-fraction": max(float(t) for t in paper_target)
        > native_diag["answerable_fraction"],
        "F5-constant-score-tie-forced-full-commit": paper_target["0.8"]
        == native_diag["paper"]["withheld_rows"],
    }
    return {
        "schema_version": "0.1",
        "grain_id": "SG-000025",
        "record_id": "study1-d1-pilot-diagnosis-v0.1",
        "scope": "Diagnostic only. Computed from immutable Study 0 raw predictions; Study 0 evidence, claims, and results are unchanged.",
        "sources_sha256": {
            f"registry/p08_sg000022_final_evaluation/{name}": digest
            for name, digest in sorted(PINNED.items())
        },
        "pubmedqa": {
            "paper_system": paper,
            "clinical_control": control,
            "laya": laya_cls,
            "paper_confidence_range": {"min": min(confidences), "max": max(confidences)},
            "paper_class_calibration": _class_calibration(
                pubmed, "paper_action_probabilities", "gold_action"
            ),
            "laya_class_calibration_note": "Not computed: Laya affected confidence is uncalibrated (Study 0 runtime warning).",
        },
        "native_abstention": native_diag,
        "findings": findings,
        "finding_definitions": {
            "F1-majority-class-collapse": "paper system predicts the majority class on every PubMedQA row and its accuracy equals the majority-class baseline",
            "F2-paper-equals-control": "paper and control classification reports are identical",
            "F3-trivial-sufficiency-separation": "sufficiency score separates evidence-present from evidence-withheld rows perfectly while assigning every withheld row one constant score",
            "F4-coverage-targets-exceed-answerable-fraction": "a frozen coverage target exceeds the fraction of answerable rows, so meeting it forces commits on insufficient rows",
            "F5-constant-score-tie-forced-full-commit": "at target 0.8 every withheld row ties at or above the frozen threshold, so the policy commits on all rows",
        },
        "study1_design_implications": [
            "Train and select the QA component against macro-F1 and balanced accuracy, not accuracy alone, and report the majority-class baseline.",
            "Use class-aware objectives or sampling; a head that reproduces class priors must be rejected in development.",
            "Construct insufficiency that cannot be detected from context presence alone (partial, irrelevant, contradictory evidence, and genuinely unanswerable questions).",
            "Keep coverage targets at or below the answerable fraction, or report risk-coverage without forcing commits, and define deterministic tie handling.",
            "Evaluate whether the assurance layer changes decisions, not only whether it ranks inputs.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Study 1 D1 pilot diagnosis")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != text:
            print("pilot diagnosis differs from deterministic rebuild")
            return 1
        print("Study 1 D1 pilot diagnosis check passed")
        return 0
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Study 1 D1 pilot diagnosis built -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
