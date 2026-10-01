from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import platform
from importlib import metadata
from pathlib import Path
from typing import Any

from gaxbench.p08_final_evaluation import (
    AUTHORIZATION_DIGEST,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    aurc,
    calibration_threshold,
    load_json,
    paired_bootstrap_difference,
    risk_at_coverage,
    sigmoid,
    softmax,
    validate_final_evaluation_preflight,
)
from gaxbench.provenance import canonical_json_sha256, sha256_file
from gaxbench.pubmedqa import (
    PubMedQASplitManifest,
    convert_record,
    load_frozen_pqal,
)

_ACTION_ORDER = ("maybe", "no", "yes")
_PUBMEDQA_SPLIT_SHA256 = "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
_PAPER_CHECKPOINT_SHA256 = "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
_LAYA_SOURCE_REVISION = "3c68ca2ccf6a83640ab80c20379503fe72c772fd"
_LAYA_MODEL_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
_LAYA_ADAPTER_REVISION = "dal-p08-laya-pubmedqa-choice-v0.1"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--split-manifest", default="registry/pubmedqa_pqal_split_manifest.json")
    parser.add_argument(
        "--development-manifest",
        default="registry/p08_development_training_manifest_sg000019.json",
    )
    parser.add_argument(
        "--training-contract",
        default="registry/p08_paper_training_contract_sg000019.json",
    )
    parser.add_argument("--source-revision")
    parser.add_argument("--output-dir")
    return parser.parse_args()


def _load_script(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _runtime_identity() -> dict[str, object]:
    packages: dict[str, str] = {}
    for name in (
        "gaxbench",
        "torch",
        "transformers",
        "huggingface_hub",
        "tokenizers",
        "laya",
    ):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or platform.machine() or "unknown",
        "accelerator": "cpu",
        "packages": packages,
    }


def _require_execution_args(args: argparse.Namespace) -> tuple[Path, Path, str, Path]:
    missing = [
        name
        for name in ("source", "source_revision", "output_dir")
        if not getattr(args, name)
    ]
    if missing:
        raise ValueError(f"execution arguments are required: {', '.join(missing)}")
    revision = str(args.source_revision)
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        raise ValueError("source revision must be an exact lowercase git SHA")
    return Path(args.source), Path(args.split_manifest), revision, Path(args.output_dir)


def _load_checkpoint_runtime(
    source: Path,
    development_manifest: Path,
    training_contract: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], Any, Any, Any, Any]:
    wrapper = _load_script(
        "dal_p08_sg000020_checkpoint",
        Path(__file__).with_name("run_p08_sg000020_from_checkpoint.py"),
    )
    control, assurance, contract, shared, d03 = wrapper._load_frozen_checkpoint(  # noqa: SLF001
        source=source,
        development_manifest_path=development_manifest,
        training_contract_path=training_contract,
        output_dir=output_dir,
    )
    return control, assurance, contract, shared, d03, wrapper


def _encode_rows(
    rows: list[tuple[str, Any]],
    *,
    split: str,
    contract: Any,
    shared: Any,
    torch: Any,
    transformers: Any,
) -> dict[str, Any]:
    items = [
        convert_record(pmid, record, split=split, include_gold=False)
        for pmid, record in rows
    ]
    questions = [str(item.state["question"]) for item in items]
    evidences = [
        contract.encoder_input.evidence_joiner.join(evidence.text for evidence in item.evidence)
        for item in items
    ]
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        shared.BACKBONE_MODEL_ID,
        revision=shared.BACKBONE_REVISION,
    )
    model = transformers.AutoModel.from_pretrained(
        shared.BACKBONE_MODEL_ID,
        revision=shared.BACKBONE_REVISION,
        torch_dtype=torch.float32,
        attn_implementation="eager",
    )
    model.requires_grad_(False)
    batch_size = contract.recipe.encoder_batch_size
    full = shared._encode_pairs(  # noqa: SLF001
        tokenizer,
        model,
        questions,
        evidences,
        batch_size=batch_size,
        torch=torch,
    )
    question_only = shared._encode_single(  # noqa: SLF001
        tokenizer,
        model,
        questions,
        batch_size=batch_size,
        torch=torch,
    )
    withheld = shared._encode_pairs(  # noqa: SLF001
        tokenizer,
        model,
        questions,
        [""] * len(questions),
        batch_size=batch_size,
        torch=torch,
    )
    first_actions = sorted(items[0].actions, key=lambda action: action.id)
    action_ids = tuple(action.id for action in first_actions)
    if action_ids != _ACTION_ORDER:
        raise RuntimeError(f"PubMedQA action order drifted: {action_ids!r}")
    action_embeddings = shared._encode_single(  # noqa: SLF001
        tokenizer,
        model,
        [action.description for action in first_actions],
        batch_size=batch_size,
        torch=torch,
    )
    return {
        "items": items,
        "full": full,
        "question_only": question_only,
        "withheld": withheld,
        "delta": full - question_only,
        "withheld_delta": withheld - question_only,
        "action_embeddings": action_embeddings,
    }


def _load_calibration_parameters() -> tuple[float, float, float]:
    evidence = load_json("registry/p08_calibration_evidence_sg000020.json")
    if evidence.get("method") != "temperature-scaling-action+platt-sufficiency-v0.1":
        raise RuntimeError("calibration method drift")
    action = evidence.get("action")
    sufficiency = evidence.get("sufficiency")
    if not isinstance(action, dict) or not isinstance(sufficiency, dict):
        raise RuntimeError("canonical calibration evidence shape drift")
    return (
        float(action["temperature"]),
        float(sufficiency["coefficient"]),
        float(sufficiency["intercept"]),
    )


def _calibrate_sufficiency(raw: float, coefficient: float, intercept: float) -> float:
    return sigmoid(coefficient * raw + intercept)


def _argmax_action(probabilities: dict[str, float]) -> str:
    return max(probabilities.items(), key=lambda pair: (pair[1], pair[0]))[0]


def _probability_map(values: list[float]) -> dict[str, float]:
    return dict(zip(_ACTION_ORDER, values, strict=True))


def _paper_and_control_predictions(
    rows: list[tuple[str, Any]],
    encoded: dict[str, Any],
    *,
    control: dict[str, Any],
    assurance: dict[str, Any],
    shared: Any,
    d03: Any,
    torch: Any,
    temperature: float,
    sufficiency_coefficient: float,
    sufficiency_intercept: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    action_logits = shared._control_logits(encoded["full"], control)  # noqa: SLF001
    withheld_logits = shared._control_logits(encoded["withheld"], control)  # noqa: SLF001
    critic_logits = d03._critic(  # noqa: SLF001
        action_logits,
        encoded["delta"],
        encoded["action_embeddings"],
        assurance,
    )
    present_raw, withheld_raw = d03._suff(  # noqa: SLF001
        encoded["delta"], assurance, torch
    )
    if not bool(torch.equal(action_logits, shared._control_logits(encoded["full"], control))):
        raise RuntimeError("D03 action-equivalence invariant failed")

    pubmed_rows: list[dict[str, object]] = []
    native_rows: list[dict[str, object]] = []
    for index, (pmid, record) in enumerate(rows):
        present_probs = _probability_map(
            softmax(action_logits[index].detach().cpu().tolist(), temperature=temperature)
        )
        withheld_probs = _probability_map(
            softmax(withheld_logits[index].detach().cpu().tolist(), temperature=temperature)
        )
        critic_probs = _probability_map(
            softmax(critic_logits[index].detach().cpu().tolist(), temperature=temperature)
        )
        predicted = _argmax_action(present_probs)
        correct = predicted == record.final_decision
        suff_present = _calibrate_sufficiency(
            float(present_raw[index].detach().cpu().item()),
            sufficiency_coefficient,
            sufficiency_intercept,
        )
        suff_withheld = _calibrate_sufficiency(
            float(withheld_raw[index].detach().cpu().item()),
            sufficiency_coefficient,
            sufficiency_intercept,
        )
        control_present_score = max(present_probs.values())
        control_withheld_score = max(withheld_probs.values())
        pubmed_rows.append(
            {
                "item_id": f"pubmedqa-pqal-{pmid}",
                "source_id": pmid,
                "gold_action": record.final_decision,
                "paper_action_probabilities": present_probs,
                "clinical_control_action_probabilities": present_probs,
                "paper_critic_probabilities": critic_probs,
                "paper_predicted_action": predicted,
                "clinical_control_predicted_action": predicted,
                "paper_correct": correct,
                "clinical_control_correct": correct,
                "paper_sufficiency_probability": suff_present,
            }
        )
        native_rows.extend(
            [
                {
                    "item_id": f"pubmedqa-pqal-{pmid}::evidence-present",
                    "source_id": pmid,
                    "gold_sufficient": True,
                    "gold_action": record.final_decision,
                    "paper_action_correct": correct,
                    "clinical_control_action_correct": correct,
                    "paper_selection_score": suff_present,
                    "clinical_control_selection_score": control_present_score,
                },
                {
                    "item_id": f"pubmedqa-pqal-{pmid}::evidence-withheld",
                    "source_id": pmid,
                    "gold_sufficient": False,
                    "gold_action": None,
                    "paper_action_correct": False,
                    "clinical_control_action_correct": False,
                    "paper_selection_score": suff_withheld,
                    "clinical_control_selection_score": control_withheld_score,
                },
            ]
        )
    return pubmed_rows, native_rows


def _calibration_scores(
    rows: list[tuple[str, Any]],
    encoded: dict[str, Any],
    *,
    control: dict[str, Any],
    assurance: dict[str, Any],
    shared: Any,
    d03: Any,
    torch: Any,
    temperature: float,
    sufficiency_coefficient: float,
    sufficiency_intercept: float,
) -> tuple[list[float], list[float]]:
    del rows
    present_logits = shared._control_logits(encoded["full"], control)  # noqa: SLF001
    withheld_logits = shared._control_logits(encoded["withheld"], control)  # noqa: SLF001
    present_raw, withheld_raw = d03._suff(encoded["delta"], assurance, torch)  # noqa: SLF001
    paper_scores = [
        _calibrate_sufficiency(
            float(value.detach().cpu().item()),
            sufficiency_coefficient,
            sufficiency_intercept,
        )
        for value in present_raw
    ] + [
        _calibrate_sufficiency(
            float(value.detach().cpu().item()),
            sufficiency_coefficient,
            sufficiency_intercept,
        )
        for value in withheld_raw
    ]
    control_scores = [
        max(softmax(row.detach().cpu().tolist(), temperature=temperature))
        for row in present_logits
    ] + [
        max(softmax(row.detach().cpu().tolist(), temperature=temperature))
        for row in withheld_logits
    ]
    return paper_scores, control_scores


def _laya_predictions(rows: list[tuple[str, Any]]) -> dict[str, object]:
    laya = _load_script(
        "dal_p08_laya_final",
        Path(__file__).with_name("run_p08_laya_qualification.py"),
    )
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    counts = {"timeout": 0, "oom": 0, "transport": 0, "interface": 0, "parse": 0}
    try:
        agent = laya._load_agent()  # noqa: SLF001
    except BaseException as exc:
        kind = laya._classify_failure(exc)  # noqa: SLF001
        normalized = kind if kind in counts else "parse"
        counts[normalized] += len(rows)
        failures.append(
            {
                "scope": "model-bootstrap",
                "category": normalized,
                "error_type": type(exc).__name__,
                "message": str(exc)[:500],
                "affected_count": len(rows),
            }
        )
        agent = None
    if agent is not None:
        questions = laya._questions()  # noqa: SLF001
        for pmid, record in rows:
            try:
                result = agent.predict(laya._state(record), questions)  # noqa: SLF001
                choice, probabilities, confidence = laya._validated_answer(result)  # noqa: SLF001
                predictions.append(
                    {
                        "item_id": f"pubmedqa-pqal-{pmid}",
                        "source_id": pmid,
                        "prediction": choice,
                        "probabilities": probabilities,
                        "confidence": confidence,
                        "gold_action": record.final_decision,
                        "correct": choice == record.final_decision,
                    }
                )
            except BaseException as exc:
                kind = laya._classify_failure(exc)  # noqa: SLF001
                normalized = kind if kind in counts else "parse"
                counts[normalized] += 1
                failures.append(
                    {
                        "scope": "item",
                        "source_id": pmid,
                        "category": normalized,
                        "error_type": type(exc).__name__,
                        "message": str(exc)[:500],
                        "affected_count": 1,
                    }
                )
    return {
        "schema_version": "0.1",
        "system_id": "laya",
        "source_revision": _LAYA_SOURCE_REVISION,
        "model_revision": _LAYA_MODEL_REVISION,
        "adapter_revision": _LAYA_ADAPTER_REVISION,
        "requested": len(rows),
        "completed": len(predictions),
        "failures": counts,
        "failure_records": failures,
        "predictions": predictions,
    }


def _classification_metrics(rows: list[dict[str, Any]], prefix: str) -> dict[str, object]:
    completed = len(rows)
    correct = sum(bool(row[f"{prefix}_correct"]) for row in rows)
    nll_values: list[float] = []
    brier_values: list[float] = []
    confidences: list[tuple[float, bool]] = []
    class_stats = {label: {"tp": 0, "fp": 0, "fn": 0} for label in _ACTION_ORDER}
    for row in rows:
        probabilities = row[f"{prefix}_action_probabilities"]
        gold = str(row["gold_action"])
        predicted = str(row[f"{prefix}_predicted_action"])
        probability = max(float(probabilities[gold]), 1e-12)
        nll_values.append(-math.log(probability))
        brier_values.append(
            math.fsum(
                (float(probabilities[label]) - (1.0 if label == gold else 0.0)) ** 2
                for label in _ACTION_ORDER
            )
        )
        confidence = max(float(value) for value in probabilities.values())
        confidences.append((confidence, predicted == gold))
        for label in _ACTION_ORDER:
            if predicted == label and gold == label:
                class_stats[label]["tp"] += 1
            elif predicted == label:
                class_stats[label]["fp"] += 1
            elif gold == label:
                class_stats[label]["fn"] += 1
    f1_values: list[float] = []
    for values in class_stats.values():
        tp = values["tp"]
        fp = values["fp"]
        fn = values["fn"]
        denominator = 2 * tp + fp + fn
        f1_values.append(0.0 if denominator == 0 else 2 * tp / denominator)
    ece = 0.0
    bins = 15
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        members = [
            (confidence, is_correct)
            for confidence, is_correct in confidences
            if confidence >= low and (confidence < high or (index == bins - 1 and confidence <= high))
        ]
        if not members:
            continue
        mean_confidence = math.fsum(value for value, _ in members) / len(members)
        mean_accuracy = math.fsum(1.0 if flag else 0.0 for _, flag in members) / len(members)
        ece += len(members) / completed * abs(mean_confidence - mean_accuracy)
    return {
        "requested": completed,
        "completed": completed,
        "failed": 0,
        "accuracy": correct / completed,
        "macro_f1": math.fsum(f1_values) / len(f1_values),
        "nll": math.fsum(nll_values) / completed,
        "multiclass_brier": math.fsum(brier_values) / completed,
        "ece_15_equal_width": ece,
    }


def _laya_metrics(payload: dict[str, Any]) -> dict[str, object]:
    predictions = payload["predictions"]
    completed = int(payload["completed"])
    requested = int(payload["requested"])
    if not completed:
        return {
            "requested": requested,
            "completed": 0,
            "failed": requested,
            "accuracy": None,
            "nll": None,
            "multiclass_brier": None,
        }
    correct = sum(bool(row["correct"]) for row in predictions)
    nll: list[float] = []
    brier: list[float] = []
    for row in predictions:
        probabilities = row["probabilities"]
        gold = str(row["gold_action"])
        nll.append(-math.log(max(float(probabilities[gold]), 1e-12)))
        brier.append(
            math.fsum(
                (float(probabilities[label]) - (1.0 if label == gold else 0.0)) ** 2
                for label in ("yes", "no", "maybe")
            )
        )
    return {
        "requested": requested,
        "completed": completed,
        "failed": requested - completed,
        "accuracy": correct / completed,
        "nll": math.fsum(nll) / completed,
        "multiclass_brier": math.fsum(brier) / completed,
        "failure_categories": payload["failures"],
    }


def _native_metrics(
    rows: list[dict[str, Any]],
    *,
    prefix: str,
    calibration_scores: list[float],
) -> dict[str, object]:
    correctness = [bool(row[f"{prefix}_action_correct"]) for row in rows]
    scores = [float(row[f"{prefix}_selection_score"]) for row in rows]
    result: dict[str, object] = {
        "requested": len(rows),
        "completed": len(rows),
        "failed": 0,
        "risk_at_50": risk_at_coverage(correctness, scores, 0.5),
        "risk_at_80": risk_at_coverage(correctness, scores, 0.8),
        "risk_at_90": risk_at_coverage(correctness, scores, 0.9),
        "aurc": aurc(correctness, scores),
    }
    policy: dict[str, object] = {}
    for target in (0.5, 0.8, 0.9):
        threshold = calibration_threshold(calibration_scores, target)
        committed = [score >= threshold for score in scores]
        sufficient = [bool(row["gold_sufficient"]) for row in rows]
        requested = len(rows)
        insufficient_count = sum(not value for value in sufficient)
        sufficient_count = sum(sufficient)
        unsafe = sum(flag and not gold for flag, gold in zip(committed, sufficient, strict=True))
        over = sum((not flag) and gold for flag, gold in zip(committed, sufficient, strict=True))
        policy[f"{target:.1f}"] = {
            "threshold": threshold,
            "actual_coverage": sum(committed) / requested,
            "unsafe_commit_rate": unsafe / insufficient_count,
            "over_abstain_rate": over / sufficient_count,
        }
    present = [row for row in rows if bool(row["gold_sufficient"])]
    result["present_action_accuracy"] = sum(
        bool(row[f"{prefix}_action_correct"]) for row in present
    ) / len(present)
    result["actual_policy"] = policy
    return result


def _primary_comparisons(
    pubmed: list[dict[str, Any]],
    native: list[dict[str, Any]],
) -> list[dict[str, object]]:
    def paper_accuracy(sample: list[dict[str, Any]]) -> float:
        return sum(bool(row["paper_correct"]) for row in sample) / len(sample)

    def control_accuracy(sample: list[dict[str, Any]]) -> float:
        return sum(bool(row["clinical_control_correct"]) for row in sample) / len(sample)

    def paper_risk(sample: list[dict[str, Any]]) -> float:
        return risk_at_coverage(
            [bool(row["paper_action_correct"]) for row in sample],
            [float(row["paper_selection_score"]) for row in sample],
            0.8,
        )

    def control_risk(sample: list[dict[str, Any]]) -> float:
        return risk_at_coverage(
            [bool(row["clinical_control_action_correct"]) for row in sample],
            [float(row["clinical_control_selection_score"]) for row in sample],
            0.8,
        )

    return [
        {
            "benchmark": "pubmedqa-pqal",
            "metric": "action_accuracy",
            "direction": "paper-minus-control",
            "status": "measured",
            "paired_bootstrap": paired_bootstrap_difference(
                pubmed,
                paper_accuracy,
                control_accuracy,
                replicates=BOOTSTRAP_REPLICATES,
                seed=BOOTSTRAP_SEED,
                ci_level=CI_LEVEL,
            ),
        },
        {
            "benchmark": "gax-native-abstention-pqal",
            "metric": "risk_at_80",
            "direction": "paper-minus-control; lower-is-better",
            "status": "measured",
            "paired_bootstrap": paired_bootstrap_difference(
                native,
                paper_risk,
                control_risk,
                replicates=BOOTSTRAP_REPLICATES,
                seed=BOOTSTRAP_SEED,
                ci_level=CI_LEVEL,
            ),
        },
        {
            "benchmark": "fhir-agentbench",
            "metric": "action_accuracy",
            "direction": "paper-minus-control",
            "status": "blocked",
            "blocked_reason": "pre-execution frozen interface mismatch",
            "paired_bootstrap": None,
        },
    ]


def _execute(args: argparse.Namespace) -> int:
    contract = validate_final_evaluation_preflight(Path.cwd())
    source, split_manifest_path, revision, output_dir = _require_execution_args(args)
    if revision != os.environ.get("GITHUB_SHA", revision):
        raise RuntimeError("source revision does not match canonical workflow SHA")
    manifest = PubMedQASplitManifest.model_validate_json(
        split_manifest_path.read_text(encoding="utf-8")
    )
    if canonical_json_sha256(manifest.model_dump(mode="json")) != _PUBMEDQA_SPLIT_SHA256:
        raise RuntimeError("PubMedQA split manifest digest drift")
    if len(manifest.test_ids) != 500:
        raise RuntimeError("PubMedQA final-test denominator drift")

    records = dict(load_frozen_pqal(source))
    test_rows = [(pmid, records[pmid]) for pmid in manifest.test_ids]
    calibration_rows = [(pmid, records[pmid]) for pmid in manifest.calibration_ids]
    if set(manifest.test_ids) & set(manifest.calibration_ids):
        raise RuntimeError("test/calibration membership overlap")

    import torch
    import transformers

    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
    torch.use_deterministic_algorithms(True)
    control, assurance, training_contract, shared, d03, _ = _load_checkpoint_runtime(
        source,
        Path(args.development_manifest),
        Path(args.training_contract),
        output_dir,
    )
    if sha256_file(Path("registry/p08_gax_paper_candidate_seed0_checkpoint_sg000019.json")) != (
        _PAPER_CHECKPOINT_SHA256
    ):
        raise RuntimeError("paper checkpoint digest drift")
    temperature, suff_coefficient, suff_intercept = _load_calibration_parameters()
    encoded_test = _encode_rows(
        test_rows,
        split="test",
        contract=training_contract,
        shared=shared,
        torch=torch,
        transformers=transformers,
    )
    encoded_calibration = _encode_rows(
        calibration_rows,
        split="calibration",
        contract=training_contract,
        shared=shared,
        torch=torch,
        transformers=transformers,
    )
    pubmed_rows, native_rows = _paper_and_control_predictions(
        test_rows,
        encoded_test,
        control=control,
        assurance=assurance,
        shared=shared,
        d03=d03,
        torch=torch,
        temperature=temperature,
        sufficiency_coefficient=suff_coefficient,
        sufficiency_intercept=suff_intercept,
    )
    paper_calibration, control_calibration = _calibration_scores(
        calibration_rows,
        encoded_calibration,
        control=control,
        assurance=assurance,
        shared=shared,
        d03=d03,
        torch=torch,
        temperature=temperature,
        sufficiency_coefficient=suff_coefficient,
        sufficiency_intercept=suff_intercept,
    )
    laya_payload = _laya_predictions(test_rows)
    fhir_blocked = {
        "schema_version": "0.1",
        "benchmark": "fhir-agentbench",
        "detected_before_final_test_access": True,
        "gold_rows_loaded": 0,
        "systems": [
            {
                "system_id": system_id,
                "requested": 173,
                "completed": 0,
                "failures": {"interface": 173},
                "status": "blocked",
                "reason": "frozen adapter cannot represent variable FHIR candidate action sets",
            }
            for system_id in contract.required_systems
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_pubmed = output_dir / "raw-pubmedqa-predictions.json"
    raw_native = output_dir / "raw-native-abstention-predictions.json"
    raw_laya = output_dir / "raw-laya-pubmedqa-predictions.json"
    raw_fhir = output_dir / "raw-fhir-interface-block.json"
    _write_json(raw_pubmed, pubmed_rows)
    _write_json(raw_native, native_rows)
    _write_json(raw_laya, laya_payload)
    _write_json(raw_fhir, fhir_blocked)

    # Derived metrics are intentionally computed only after all raw artifacts exist on disk.
    pubmed = load_json(raw_pubmed)
    native = load_json(raw_native)
    laya = load_json(raw_laya)
    metrics = {
        "schema_version": "0.1",
        "grain_id": "SG-000022",
        "source_revision": revision,
        "authorization_digest": AUTHORIZATION_DIGEST,
        "contract_revision": contract.contract_revision,
        "runtime": _runtime_identity(),
        "raw_artifacts": {
            raw_pubmed.name: sha256_file(raw_pubmed),
            raw_native.name: sha256_file(raw_native),
            raw_laya.name: sha256_file(raw_laya),
            raw_fhir.name: sha256_file(raw_fhir),
        },
        "pubmedqa": {
            "paper": _classification_metrics(pubmed, "paper"),
            "clinical_control": _classification_metrics(pubmed, "clinical_control"),
            "laya": _laya_metrics(laya),
        },
        "native_abstention": {
            "paper": _native_metrics(
                native,
                prefix="paper",
                calibration_scores=paper_calibration,
            ),
            "clinical_control": _native_metrics(
                native,
                prefix="clinical_control",
                calibration_scores=control_calibration,
            ),
            "laya": {
                "requested": 1000,
                "completed": 0,
                "failed": 1000,
                "failure_categories": {"interface": 1000},
                "status": "blocked",
                "reason": "frozen Laya adapter has no information-sufficiency output",
            },
        },
        "fhir_agentbench": fhir_blocked,
        "primary_comparisons": _primary_comparisons(pubmed, native),
        "multiplicity": {
            "policy": "holm-primary-family-v0.1",
            "status": "no-p-values-emitted",
            "reason": (
                "The frozen statistics layer specifies confidence intervals and Holm policy but "
                "does not freeze a primary p-value construction. No significance or superiority "
                "claim is emitted from SG-000022."
            ),
        },
        "claims": {
            "superiority": "not-claimed",
            "clinical_safety": "not-claimed",
            "sota": "not-claimed",
        },
        "zero_founder_cost": True,
    }
    metrics_path = output_dir / "metrics.json"
    _write_json(metrics_path, metrics)
    summary = {
        "schema_version": "0.1",
        "grain_id": "SG-000022",
        "source_revision": revision,
        "authorization_digest": AUTHORIZATION_DIGEST,
        "pubmedqa_requested": 500,
        "native_requested": 1000,
        "fhir_requested": 173,
        "fhir_status": "interface-blocked-preexecution",
        "laya_pubmedqa_requested": int(laya["requested"]),
        "laya_pubmedqa_completed": int(laya["completed"]),
        "raw_artifacts_persisted_before_metrics": True,
        "metrics_sha256": sha256_file(metrics_path),
        "final_test_inference_executed": True,
        "zero_founder_cost": True,
    }
    _write_json(output_dir / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


def main() -> int:
    args = _args()
    contract = validate_final_evaluation_preflight(Path.cwd())
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "grain_id": contract.grain_id,
                    "authorization_digest": contract.authorization_digest,
                    "final_test_rows_used": 0,
                    "status": "preflight-pass",
                },
                sort_keys=True,
            )
        )
        return 0
    return _execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
