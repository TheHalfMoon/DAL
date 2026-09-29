from __future__ import annotations

import argparse
import importlib
import json
import math
import platform
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

from gaxbench.p08_real_systems import (
    DevelopmentTrainingManifest,
    ExecutionFailureCounts,
    RuntimeIdentity,
    SystemExecutionEvidence,
    execution_evidence_digest,
)
from gaxbench.p08_system_qualification import (
    LAYA_MODEL_REVISION,
    LAYA_SOURCE_REVISION,
    SG000019_DEVELOPMENT_MANIFEST_SHA256,
    SystemQualificationBundle,
    qualification_bundle_digest,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.pubmedqa import PubMedQARecord, load_frozen_pqal
from gaxbench.schema import StrictModel

LAYA_MODEL_ID = "convaiinnovations/laya"
LAYA_ADAPTER_REVISION = "dal-p08-laya-pubmedqa-choice-v0.1"
QUESTION_ID = "pubmedqa_answer"
FailureKind = Literal["oom", "timeout", "transport", "interface", "other"]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: object
    if isinstance(value, StrictModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _runtime_identity() -> RuntimeIdentity:
    packages: dict[str, str] = {}
    for package_name in (
        "gaxbench",
        "laya",
        "torch",
        "transformers",
        "safetensors",
        "huggingface_hub",
        "tokenizers",
        "numpy",
    ):
        packages[package_name] = metadata.version(package_name)
    return RuntimeIdentity(
        os=platform.platform(),
        python=platform.python_version(),
        processor=platform.processor() or platform.machine() or "unknown-x86_64",
        accelerator="cpu",
        packages=packages,
    )


def _classify_failure(exc: BaseException) -> FailureKind:
    message = str(exc).lower()
    if isinstance(exc, MemoryError) or "out of memory" in message or "oom" in message:
        return "oom"
    if isinstance(exc, TimeoutError) or "timed out" in message or "timeout" in message:
        return "timeout"
    if isinstance(exc, (ConnectionError, OSError)) and any(
        token in message for token in ("http", "network", "connection", "download", "socket")
    ):
        return "transport"
    if isinstance(exc, (KeyError, TypeError, ValueError, AttributeError)):
        return "interface"
    return "other"


def _failure_counts(counts: dict[FailureKind, int]) -> ExecutionFailureCounts:
    return ExecutionFailureCounts(
        oom=counts["oom"],
        timeout=counts["timeout"],
        transport=counts["transport"],
        interface=counts["interface"],
        other=counts["other"],
    )


def _state(record: PubMedQARecord) -> str:
    evidence = "\n".join(
        f"[{index}] {context}" for index, context in enumerate(record.CONTEXTS, start=1)
    )
    return f"Biomedical research question:\n{record.QUESTION}\n\nEvidence:\n{evidence}"


def _questions() -> dict[str, dict[str, object]]:
    return {
        QUESTION_ID: {
            "type": "choice",
            "instructions": (
                "Using only the biomedical evidence in the state, answer the research question. "
                "Choose the single best answer."
            ),
            "criteria": {
                "yes": "The evidence supports answering yes.",
                "no": "The evidence supports answering no.",
                "maybe": "The evidence is inconclusive or supports answering maybe.",
            },
        }
    }


def _validated_answer(result: object) -> tuple[str, dict[str, float], float | None]:
    if not isinstance(result, dict):
        raise TypeError("Laya result must be a dictionary")
    answers = result.get("answers")
    if not isinstance(answers, dict):
        raise TypeError("Laya result.answers must be a dictionary")
    answer = answers.get(QUESTION_ID)
    if not isinstance(answer, dict):
        raise TypeError(f"Laya result is missing {QUESTION_ID!r}")
    if answer.get("type") != "choice":
        raise ValueError("Laya PubMedQA answer must be type='choice'")

    choice = answer.get("choice")
    if choice not in {"yes", "no", "maybe"}:
        raise ValueError(f"unexpected Laya choice {choice!r}")

    raw_probabilities = answer.get("probabilities")
    if not isinstance(raw_probabilities, dict):
        raise TypeError("Laya choice answer must expose probabilities")
    if set(raw_probabilities) != {"yes", "no", "maybe"}:
        raise ValueError("Laya probabilities must contain exactly yes/no/maybe")

    probabilities: dict[str, float] = {}
    for label in ("yes", "no", "maybe"):
        raw_value = raw_probabilities[label]
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise TypeError(f"Laya probability for {label!r} must be numeric")
        value = float(raw_value)
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValueError(f"Laya probability for {label!r} is outside [0, 1]")
        probabilities[label] = value

    probability_sum = sum(probabilities.values())
    if not 0.98 <= probability_sum <= 1.02:
        raise ValueError(f"Laya probabilities sum to {probability_sum}, expected approximately 1")

    raw_confidence = answer.get("confidence")
    confidence: float | None = None
    if raw_confidence is not None:
        if isinstance(raw_confidence, bool) or not isinstance(raw_confidence, (int, float)):
            raise TypeError("Laya confidence must be numeric when present")
        confidence = float(raw_confidence)
        if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
            raise ValueError("Laya confidence is outside [0, 1]")
    return str(choice), probabilities, confidence


def _load_agent() -> Any:
    hub_module = importlib.import_module("huggingface_hub")
    laya_module = importlib.import_module("laya")
    snapshot_download = hub_module.snapshot_download
    agent_type = laya_module.Agent
    snapshot = snapshot_download(
        repo_id=LAYA_MODEL_ID,
        revision=LAYA_MODEL_REVISION,
        allow_patterns=[
            "rl_agent_config.json",
            "model.safetensors",
            "tokenizer/*",
            "encoder/*",
        ],
    )
    snapshot_path = Path(snapshot).resolve()
    if snapshot_path.name != LAYA_MODEL_REVISION:
        raise RuntimeError(
            "Laya snapshot revision drift: "
            f"expected {LAYA_MODEL_REVISION}, got {snapshot_path.name}"
        )
    if not (snapshot_path / "model.safetensors").is_file():
        raise RuntimeError("pinned Laya snapshot is missing model.safetensors")
    return agent_type(str(snapshot_path), device="cpu")


def _execute(
    records: dict[str, PubMedQARecord],
    manifest: DevelopmentTrainingManifest,
) -> tuple[dict[str, object], SystemExecutionEvidence, SystemQualificationBundle | None]:
    runtime = _runtime_identity()
    failures: dict[FailureKind, int] = {
        "oom": 0,
        "timeout": 0,
        "transport": 0,
        "interface": 0,
        "other": 0,
    }
    failure_records: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []
    correct_count = 0

    try:
        agent = _load_agent()
    except BaseException as exc:  # preserve bootstrap failure as evidence
        kind = _classify_failure(exc)
        failures[kind] = len(manifest.selection_ids)
        failure_records.append(
            {
                "scope": "model-bootstrap",
                "kind": kind,
                "error_type": type(exc).__name__,
                "message": str(exc)[:500],
                "affected_count": len(manifest.selection_ids),
            }
        )
        agent = None

    if agent is not None:
        questions = _questions()
        for pmid in manifest.selection_ids:
            record = records[pmid]
            try:
                result = agent.predict(_state(record), questions)
                choice, probabilities, confidence = _validated_answer(result)
                is_correct = choice == record.final_decision
                if is_correct:
                    correct_count += 1
                prediction_rows.append(
                    {
                        "item_id": f"pubmedqa-pqal-{pmid}",
                        "source_id": pmid,
                        "prediction": choice,
                        "probabilities": probabilities,
                        "confidence": confidence,
                        "gold_development_only": record.final_decision,
                        "correct_development_only": is_correct,
                    }
                )
            except BaseException as exc:  # preserve every failed request
                kind = _classify_failure(exc)
                failures[kind] += 1
                failure_records.append(
                    {
                        "scope": "item",
                        "source_id": pmid,
                        "kind": kind,
                        "error_type": type(exc).__name__,
                        "message": str(exc)[:500],
                        "affected_count": 1,
                    }
                )

    completed_count = len(prediction_rows)
    failed_count = sum(failures.values())
    requested_count = len(manifest.selection_ids)
    if completed_count + failed_count != requested_count:
        raise RuntimeError("internal failure accounting lost requests")

    accuracy: float | None = None
    if completed_count:
        accuracy = correct_count / completed_count
    predictions_payload: dict[str, object] = {
        "schema_version": "0.1",
        "system_id": "laya",
        "role": "baseline",
        "source_revision": LAYA_SOURCE_REVISION,
        "model_id": LAYA_MODEL_ID,
        "model_revision": LAYA_MODEL_REVISION,
        "adapter_revision": LAYA_ADAPTER_REVISION,
        "dataset_manifest_sha256": SG000019_DEVELOPMENT_MANIFEST_SHA256,
        "evaluation_role": "development-selection",
        "requested_count": requested_count,
        "completed_count": completed_count,
        "failure_count": failed_count,
        "failures": failure_records,
        "predictions": prediction_rows,
        "development_metrics": {
            "correct_count": correct_count,
            "accuracy": accuracy,
        },
        "zero_founder_cost": True,
        "final_test_access": "sealed",
    }
    predictions_sha256 = canonical_json_sha256(predictions_payload)
    status: Literal["complete", "partial", "blocked"]
    if completed_count == requested_count and failed_count == 0:
        status = "complete"
    elif completed_count > 0:
        status = "partial"
    else:
        status = "blocked"

    evidence = SystemExecutionEvidence(
        system_id="laya",
        role="baseline",
        source_revision=LAYA_SOURCE_REVISION,
        model_revision=LAYA_MODEL_REVISION,
        tokenizer_revision=None,
        adapter_revision=LAYA_ADAPTER_REVISION,
        checkpoint_sha256=None,
        training_seed=None,
        dataset_manifest_sha256=SG000019_DEVELOPMENT_MANIFEST_SHA256,
        evaluation_role="development-selection",
        requested_count=requested_count,
        completed_count=completed_count,
        failures=_failure_counts(failures),
        runtime=runtime,
        predictions_sha256=predictions_sha256 if completed_count else None,
        status=status,
    )
    bundle: SystemQualificationBundle | None = None
    if status == "complete":
        bundle = SystemQualificationBundle(system_id="laya", executions=[evidence])
    return predictions_payload, evidence, bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--development-manifest", required=True, type=Path)
    parser.add_argument("--predictions-output", required=True, type=Path)
    parser.add_argument("--evidence-output", required=True, type=Path)
    parser.add_argument("--bundle-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()

    manifest = DevelopmentTrainingManifest.model_validate(
        json.loads(args.development_manifest.read_text(encoding="utf-8"))
    )
    manifest_digest = canonical_json_sha256(manifest.model_dump(mode="json"))
    if manifest_digest != SG000019_DEVELOPMENT_MANIFEST_SHA256:
        raise RuntimeError(
            "development manifest drift: "
            f"expected {SG000019_DEVELOPMENT_MANIFEST_SHA256}, got {manifest_digest}"
        )

    source_records = dict(load_frozen_pqal(args.source))
    selected = set(manifest.selection_ids)
    if selected & set(manifest.train_ids):
        raise RuntimeError("development-selection overlaps training rows")
    missing = sorted(selected - set(source_records))
    if missing:
        raise RuntimeError(f"frozen PubMedQA source is missing selection rows: {missing[:5]}")

    predictions, evidence, bundle = _execute(source_records, manifest)
    _write_json(args.predictions_output, predictions)
    _write_json(args.evidence_output, evidence)
    if bundle is not None:
        _write_json(args.bundle_output, bundle)

    summary: dict[str, object] = {
        "schema_version": "0.1",
        "system_id": "laya",
        "status": evidence.status,
        "execution_evidence_sha256": execution_evidence_digest(evidence),
        "qualification_bundle_sha256": (
            qualification_bundle_digest(bundle) if bundle is not None else None
        ),
        "requested_count": evidence.requested_count,
        "completed_count": evidence.completed_count,
        "failure_count": evidence.failures.total(),
        "development_accuracy": predictions["development_metrics"],
        "model_revision": LAYA_MODEL_REVISION,
        "source_revision": LAYA_SOURCE_REVISION,
        "zero_founder_cost": True,
        "final_test_access": "sealed",
    }
    _write_json(args.summary_output, summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
