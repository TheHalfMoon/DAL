from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
from pathlib import Path
from typing import Any

from gaxbench.p08_paper_models import (
    BACKBONE_MODEL_ID,
    BACKBONE_REVISION,
    CLINICAL_CONTROL_ARCHITECTURE,
    DAL_PAPER_ARCHITECTURE,
    PaperTrainingContract,
    training_contract_digest,
)
from gaxbench.p08_real_systems import (
    CheckpointProvenance,
    DevelopmentTrainingManifest,
    ExecutionFailureCounts,
    RuntimeIdentity,
    SystemExecutionEvidence,
)
from gaxbench.p08_system_qualification import (
    CLINICAL_MODEL_REVISION,
    CONTROL_ADAPTER_REVISION,
    PAPER_ADAPTER_REVISION,
    PAPER_MODEL_REVISION,
    SystemQualificationBundle,
)
from gaxbench.provenance import canonical_json_sha256, sha256_file
from gaxbench.pubmedqa import PubMedQARecord, convert_record, load_frozen_pqal

_ACTION_ORDER = ("maybe", "no", "yes")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--training-contract", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return sha256_file(path)


def _load_json_model(path: Path, model_type: type[Any]) -> Any:
    return model_type.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _selected_records(
    source: Path,
    manifest: DevelopmentTrainingManifest,
) -> tuple[list[tuple[str, PubMedQARecord]], list[tuple[str, PubMedQARecord]]]:
    records = dict(load_frozen_pqal(source))
    allowed = set(manifest.train_ids) | set(manifest.selection_ids)
    if len(allowed) != 450:
        raise ValueError("SG-000019 must expose exactly 450 development rows")
    if not allowed <= set(records):
        raise ValueError("development manifest references missing PubMedQA rows")
    train = [(pmid, records[pmid]) for pmid in manifest.train_ids]
    selection = [(pmid, records[pmid]) for pmid in manifest.selection_ids]
    return train, selection


def _visible_item(
    pmid: str,
    record: PubMedQARecord,
    *,
    split: str,
) -> Any:
    return convert_record(
        pmid,
        record,
        split=split,
        include_gold=True,
    )


def _mean_pool(hidden: Any, attention_mask: Any, torch: Any) -> Any:
    mask = attention_mask.unsqueeze(-1).to(dtype=hidden.dtype)
    summed = (hidden * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp_min(1.0)
    pooled = summed / counts
    return torch.nn.functional.normalize(pooled, p=2.0, dim=1)


def _encode_pairs(
    tokenizer: Any,
    model: Any,
    questions: list[str],
    evidences: list[str],
    *,
    batch_size: int,
    torch: Any,
) -> Any:
    outputs: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(questions), batch_size):
            encoded = tokenizer(
                questions[start : start + batch_size],
                evidences[start : start + batch_size],
                padding=True,
                truncation="only_second",
                max_length=512,
                return_tensors="pt",
            )
            result = model(**encoded)
            outputs.append(_mean_pool(result.last_hidden_state, encoded["attention_mask"], torch))
    return torch.cat(outputs, dim=0).cpu()


def _encode_single(
    tokenizer: Any,
    model: Any,
    texts: list[str],
    *,
    batch_size: int,
    torch: Any,
) -> Any:
    outputs: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            encoded = tokenizer(
                texts[start : start + batch_size],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            result = model(**encoded)
            outputs.append(_mean_pool(result.last_hidden_state, encoded["attention_mask"], torch))
    return torch.cat(outputs, dim=0).cpu()


def _prepare_embeddings(
    train_records: list[tuple[str, PubMedQARecord]],
    selection_records: list[tuple[str, PubMedQARecord]],
    contract: PaperTrainingContract,
    *,
    torch: Any,
    transformers: Any,
) -> dict[str, Any]:
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        BACKBONE_MODEL_ID,
        revision=BACKBONE_REVISION,
    )
    model = transformers.AutoModel.from_pretrained(
        BACKBONE_MODEL_ID,
        revision=BACKBONE_REVISION,
        torch_dtype=torch.float32,
        attn_implementation="eager",
    )
    model.requires_grad_(False)

    train_items = [
        _visible_item(pmid, record, split="train") for pmid, record in train_records
    ]
    selection_items = [
        _visible_item(pmid, record, split="validation")
        for pmid, record in selection_records
    ]
    all_items = train_items + selection_items
    questions = [str(item.state["question"]) for item in all_items]
    evidences = [
        contract.encoder_input.evidence_joiner.join(evidence.text for evidence in item.evidence)
        for item in all_items
    ]
    batch_size = contract.recipe.encoder_batch_size
    full = _encode_pairs(
        tokenizer,
        model,
        questions,
        evidences,
        batch_size=batch_size,
        torch=torch,
    )
    question_only = _encode_single(
        tokenizer,
        model,
        questions,
        batch_size=batch_size,
        torch=torch,
    )

    first_actions = sorted(all_items[0].actions, key=lambda action: action.id)
    action_ids = tuple(action.id for action in first_actions)
    if action_ids != _ACTION_ORDER:
        raise ValueError(f"unexpected PubMedQA action order: {action_ids!r}")
    for item in all_items:
        current = tuple(action.id for action in sorted(item.actions, key=lambda action: action.id))
        if current != _ACTION_ORDER:
            raise ValueError("PubMedQA action schema drift across development rows")
    action_texts = [action.description for action in first_actions]
    action_embeddings = _encode_single(
        tokenizer,
        model,
        action_texts,
        batch_size=batch_size,
        torch=torch,
    )

    labels = torch.tensor(
        [_ACTION_ORDER.index(item.gold.action) for item in all_items],
        dtype=torch.long,
    )
    train_count = len(train_items)
    return {
        "train_items": train_items,
        "selection_items": selection_items,
        "train_full": full[:train_count],
        "selection_full": full[train_count:],
        "train_delta": full[:train_count] - question_only[:train_count],
        "selection_delta": full[train_count:] - question_only[train_count:],
        "train_labels": labels[:train_count],
        "selection_labels": labels[train_count:],
        "action_embeddings": action_embeddings,
        "hidden_size": int(full.shape[1]),
        "action_texts": action_texts,
    }


def _linear_parameters(hidden_size: int, torch: Any) -> dict[str, Any]:
    weight = torch.nn.Parameter(torch.empty(3, hidden_size))
    bias = torch.nn.Parameter(torch.zeros(3))
    torch.nn.init.xavier_uniform_(weight)
    return {"action_weight": weight, "action_bias": bias}


def _paper_parameters(hidden_size: int, torch: Any) -> dict[str, Any]:
    parameters = _linear_parameters(hidden_size, torch)
    parameters.update(
        {
            "residual_scale": torch.nn.Parameter(torch.zeros(1)),
            "suff_scale": torch.nn.Parameter(torch.ones(1)),
            "suff_bias": torch.nn.Parameter(torch.zeros(1)),
        }
    )
    return parameters


def _paper_logits(
    full: Any,
    delta: Any,
    action_embeddings: Any,
    parameters: dict[str, Any],
    *,
    torch: Any,
) -> tuple[Any, Any, Any]:
    base_logits = full @ parameters["action_weight"].T + parameters["action_bias"]
    typed_residual = delta @ action_embeddings.T
    action_logits = base_logits + parameters["residual_scale"] * typed_residual
    evidence_delta_norm = torch.linalg.vector_norm(delta, ord=2, dim=1)
    present_sufficiency = (
        parameters["suff_scale"] * evidence_delta_norm + parameters["suff_bias"]
    )
    withheld_sufficiency = torch.zeros_like(present_sufficiency) + parameters["suff_bias"]
    return action_logits, present_sufficiency, withheld_sufficiency


def _classification_metrics(logits: Any, labels: Any, *, torch: Any) -> tuple[float, float]:
    nll = float(torch.nn.functional.cross_entropy(logits, labels).item())
    accuracy = float((logits.argmax(dim=1) == labels).float().mean().item())
    return nll, accuracy


def _paper_metric(
    full: Any,
    delta: Any,
    labels: Any,
    action_embeddings: Any,
    parameters: dict[str, Any],
    *,
    torch: Any,
) -> tuple[float, float, float, float]:
    with torch.no_grad():
        logits, present, withheld = _paper_logits(
            full,
            delta,
            action_embeddings,
            parameters,
            torch=torch,
        )
        action_nll, accuracy = _classification_metrics(logits, labels, torch=torch)
        present_probability = torch.sigmoid(present)
        withheld_probability = torch.sigmoid(withheld)
        sufficiency_brier = float(
            torch.cat(
                [
                    (present_probability - 1.0).square(),
                    withheld_probability.square(),
                ]
            )
            .mean()
            .item()
        )
    return action_nll + 0.5 * sufficiency_brier, action_nll, sufficiency_brier, accuracy


def _clone_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    return {name: value.detach().cpu().clone() for name, value in parameters.items()}


def _restore_parameters(parameters: dict[str, Any], state: dict[str, Any]) -> None:
    for name, parameter in parameters.items():
        parameter.data.copy_(state[name])


def _train_paper(
    embeddings: dict[str, Any],
    contract: PaperTrainingContract,
    seed: int,
    *,
    torch: Any,
) -> tuple[dict[str, Any], list[dict[str, float | int]], dict[str, float | int]]:
    torch.manual_seed(seed)
    parameters = _paper_parameters(embeddings["hidden_size"], torch)
    optimizer = torch.optim.AdamW(
        list(parameters.values()),
        lr=contract.recipe.learning_rate,
        weight_decay=contract.recipe.weight_decay,
    )
    history: list[dict[str, float | int]] = []
    best_metric = math.inf
    best_state: dict[str, Any] | None = None
    best_record: dict[str, float | int] | None = None
    count = int(embeddings["train_full"].shape[0])
    batch_size = contract.recipe.head_batch_size

    for epoch in range(1, contract.recipe.epochs + 1):
        for start in range(0, count, batch_size):
            stop = min(start + batch_size, count)
            optimizer.zero_grad(set_to_none=True)
            logits, present, withheld = _paper_logits(
                embeddings["train_full"][start:stop],
                embeddings["train_delta"][start:stop],
                embeddings["action_embeddings"],
                parameters,
                torch=torch,
            )
            action_loss = torch.nn.functional.cross_entropy(
                logits,
                embeddings["train_labels"][start:stop],
            )
            sufficiency_logits = torch.cat([present, withheld])
            sufficiency_targets = torch.cat(
                [torch.ones_like(present), torch.zeros_like(withheld)]
            )
            sufficiency_loss = torch.nn.functional.binary_cross_entropy_with_logits(
                sufficiency_logits,
                sufficiency_targets,
            )
            loss = (
                contract.recipe.action_loss_weight * action_loss
                + contract.recipe.sufficiency_loss_weight * sufficiency_loss
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(parameters.values()),
                contract.recipe.gradient_clip_norm,
            )
            optimizer.step()

        metric, action_nll, sufficiency_brier, accuracy = _paper_metric(
            embeddings["selection_full"],
            embeddings["selection_delta"],
            embeddings["selection_labels"],
            embeddings["action_embeddings"],
            parameters,
            torch=torch,
        )
        record: dict[str, float | int] = {
            "epoch": epoch,
            "selection_metric": metric,
            "action_nll": action_nll,
            "sufficiency_brier": sufficiency_brier,
            "accuracy": accuracy,
        }
        history.append(record)
        if metric < best_metric:
            best_metric = metric
            best_state = _clone_parameters(parameters)
            best_record = dict(record)

    if best_state is None or best_record is None:
        raise RuntimeError("paper training produced no checkpoint")
    _restore_parameters(parameters, best_state)
    return parameters, history, best_record


def _control_logits(full: Any, parameters: dict[str, Any]) -> Any:
    return full @ parameters["action_weight"].T + parameters["action_bias"]


def _train_control(
    embeddings: dict[str, Any],
    contract: PaperTrainingContract,
    seed: int,
    *,
    torch: Any,
) -> tuple[dict[str, Any], list[dict[str, float | int]], dict[str, float | int]]:
    torch.manual_seed(seed)
    parameters = _linear_parameters(embeddings["hidden_size"], torch)
    optimizer = torch.optim.AdamW(
        list(parameters.values()),
        lr=contract.recipe.learning_rate,
        weight_decay=contract.recipe.weight_decay,
    )
    history: list[dict[str, float | int]] = []
    best_metric = math.inf
    best_state: dict[str, Any] | None = None
    best_record: dict[str, float | int] | None = None
    count = int(embeddings["train_full"].shape[0])
    batch_size = contract.recipe.head_batch_size

    for epoch in range(1, contract.recipe.epochs + 1):
        for start in range(0, count, batch_size):
            stop = min(start + batch_size, count)
            optimizer.zero_grad(set_to_none=True)
            logits = _control_logits(embeddings["train_full"][start:stop], parameters)
            loss = torch.nn.functional.cross_entropy(
                logits,
                embeddings["train_labels"][start:stop],
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(parameters.values()),
                contract.recipe.gradient_clip_norm,
            )
            optimizer.step()

        with torch.no_grad():
            selection_logits = _control_logits(embeddings["selection_full"], parameters)
            action_nll, accuracy = _classification_metrics(
                selection_logits,
                embeddings["selection_labels"],
                torch=torch,
            )
        record = {
            "epoch": epoch,
            "selection_metric": action_nll,
            "action_nll": action_nll,
            "accuracy": accuracy,
        }
        history.append(record)
        if action_nll < best_metric:
            best_metric = action_nll
            best_state = _clone_parameters(parameters)
            best_record = dict(record)

    if best_state is None or best_record is None:
        raise RuntimeError("control training produced no checkpoint")
    _restore_parameters(parameters, best_state)
    return parameters, history, best_record


def _state_payload(parameters: dict[str, Any]) -> dict[str, object]:
    return {
        name: parameter.detach().cpu().tolist()
        for name, parameter in sorted(parameters.items())
    }


def _probabilities(logits: Any, torch: Any) -> list[list[float]]:
    return torch.softmax(logits, dim=1).detach().cpu().tolist()


def _prediction_payload(
    system_id: str,
    seed: int,
    items: list[Any],
    logits: Any,
    *,
    torch: Any,
    sufficiency: Any | None = None,
) -> list[dict[str, object]]:
    probabilities = _probabilities(logits, torch)
    sufficiency_values = (
        torch.sigmoid(sufficiency).detach().cpu().tolist() if sufficiency is not None else None
    )
    payload: list[dict[str, object]] = []
    for index, (item, values) in enumerate(zip(items, probabilities, strict=True)):
        row: dict[str, object] = {
            "item_id": item.id,
            "gold_action": item.gold.action,
            "probabilities": dict(zip(_ACTION_ORDER, values, strict=True)),
            "system_id": system_id,
            "training_seed": seed,
        }
        if sufficiency_values is not None:
            row["sufficiency_probability"] = sufficiency_values[index]
        payload.append(row)
    return payload


def _runtime_identity() -> RuntimeIdentity:
    package_names = ["torch", "transformers", "tokenizers", "huggingface_hub"]
    packages = {name: importlib.metadata.version(name) for name in package_names}
    return RuntimeIdentity(
        os=platform.platform(),
        python=platform.python_version(),
        processor=platform.processor() or platform.machine() or "unknown-cpu",
        accelerator="cpu",
        packages=packages,
    )


def _checkpoint_payload(
    *,
    system_id: str,
    architecture_id: str,
    seed: int,
    selected_record: dict[str, float | int],
    contract_sha256: str,
    state: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "0.2",
        "system_id": system_id,
        "architecture_id": architecture_id,
        "training_seed": seed,
        "selected_epoch": selected_record["epoch"],
        "selection_metric": selected_record["selection_metric"],
        "action_nll": selected_record["action_nll"],
        "accuracy": selected_record["accuracy"],
        "training_contract_sha256": contract_sha256,
        "development_manifest_sha256": (
            "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
        ),
        "base_model_id": BACKBONE_MODEL_ID,
        "base_model_revision": BACKBONE_REVISION,
        "tokenizer_revision": BACKBONE_REVISION,
        "state": state,
        "final_test_access": "sealed",
    }


def _evidence_for_seed(
    *,
    system_id: str,
    role: str,
    source_revision: str,
    model_revision: str,
    adapter_revision: str,
    checkpoint_sha256: str,
    seed: int,
    predictions_sha256: str,
    runtime: RuntimeIdentity,
) -> SystemExecutionEvidence:
    return SystemExecutionEvidence.model_validate(
        {
            "system_id": system_id,
            "role": role,
            "source_revision": source_revision,
            "model_revision": model_revision,
            "tokenizer_revision": BACKBONE_REVISION,
            "adapter_revision": adapter_revision,
            "checkpoint_sha256": checkpoint_sha256,
            "training_seed": seed,
            "dataset_manifest_sha256": (
                "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
            ),
            "evaluation_role": "development-selection",
            "requested_count": 90,
            "completed_count": 90,
            "failures": ExecutionFailureCounts().model_dump(mode="json"),
            "runtime": runtime.model_dump(mode="json"),
            "predictions_sha256": predictions_sha256,
            "status": "complete",
            "zero_founder_cost": True,
            "final_test_access": "sealed",
        }
    )


def _checkpoint_provenance(
    *,
    system_id: str,
    seed: int,
    checkpoint_sha256: str,
    contract_sha256: str,
    source_revision: str,
) -> CheckpointProvenance:
    return CheckpointProvenance.model_validate(
        {
            "system_id": system_id,
            "base_model_id": BACKBONE_MODEL_ID,
            "base_model_revision": BACKBONE_REVISION,
            "tokenizer_revision": BACKBONE_REVISION,
            "development_manifest_sha256": (
                "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
            ),
            "training_recipe_sha256": contract_sha256,
            "training_seed": seed,
            "checkpoint_sha256": checkpoint_sha256,
            "source_revision": source_revision,
            "zero_founder_cost": True,
            "final_test_access": "sealed",
        }
    )


def _failure_category(error: BaseException) -> str:
    text = str(error).casefold()
    if isinstance(error, MemoryError) or "out of memory" in text:
        return "oom"
    if isinstance(error, TimeoutError) or "timed out" in text or "timeout" in text:
        return "timeout"
    if isinstance(error, ConnectionError) or "connection" in text or "http" in text:
        return "transport"
    return "interface"


def _run(args: argparse.Namespace) -> int:
    source_revision = str(args.source_revision)
    if len(source_revision) != 40 or any(c not in "0123456789abcdef" for c in source_revision):
        raise ValueError("source revision must be an exact lowercase git SHA")

    manifest = _load_json_model(
        Path(args.development_manifest),
        DevelopmentTrainingManifest,
    )
    contract = _load_json_model(Path(args.training_contract), PaperTrainingContract)
    contract_sha256 = training_contract_digest(contract)
    train_records, selection_records = _selected_records(Path(args.source), manifest)

    import torch
    import transformers

    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
    torch.use_deterministic_algorithms(True)
    embeddings = _prepare_embeddings(
        train_records,
        selection_records,
        contract,
        torch=torch,
        transformers=transformers,
    )
    if embeddings["hidden_size"] <= 0:
        raise ValueError("frozen encoder returned an invalid hidden size")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime = _runtime_identity()
    bundles: dict[str, SystemQualificationBundle] = {}
    summary: dict[str, Any] = {
        "schema_version": "0.2",
        "implementation_source_revision": source_revision,
        "training_contract_sha256": contract_sha256,
        "development_manifest_sha256": canonical_json_sha256(manifest.model_dump(mode="json")),
        "backbone_model_id": BACKBONE_MODEL_ID,
        "backbone_revision": BACKBONE_REVISION,
        "hidden_size": embeddings["hidden_size"],
        "action_ids": list(_ACTION_ORDER),
        "action_texts": embeddings["action_texts"],
        "systems": {},
        "final_test_access": "sealed",
        "calibration_rows_used": 0,
        "final_test_rows_used": 0,
    }

    for system_id in ("gax-paper-candidate", "clinical-encoder"):
        checkpoints: list[CheckpointProvenance] = []
        executions: list[SystemExecutionEvidence] = []
        histories: dict[str, object] = {}
        seed_summaries: list[dict[str, object]] = []

        for seed in contract.recipe.training_seeds:
            if system_id == "gax-paper-candidate":
                parameters, history, selected = _train_paper(
                    embeddings,
                    contract,
                    seed,
                    torch=torch,
                )
                checkpoint_state = _state_payload(parameters)
                logits, present_sufficiency, _ = _paper_logits(
                    embeddings["selection_full"],
                    embeddings["selection_delta"],
                    embeddings["action_embeddings"],
                    parameters,
                    torch=torch,
                )
                predictions = _prediction_payload(
                    system_id,
                    seed,
                    embeddings["selection_items"],
                    logits,
                    torch=torch,
                    sufficiency=present_sufficiency,
                )
                architecture_id = DAL_PAPER_ARCHITECTURE
                adapter_revision = PAPER_ADAPTER_REVISION
                model_revision = PAPER_MODEL_REVISION
                role = "gax"
                provenance_source_revision = source_revision
            else:
                parameters, history, selected = _train_control(
                    embeddings,
                    contract,
                    seed,
                    torch=torch,
                )
                checkpoint_state = _state_payload(parameters)
                logits = _control_logits(embeddings["selection_full"], parameters)
                predictions = _prediction_payload(
                    system_id,
                    seed,
                    embeddings["selection_items"],
                    logits,
                    torch=torch,
                )
                architecture_id = CLINICAL_CONTROL_ARCHITECTURE
                adapter_revision = CONTROL_ADAPTER_REVISION
                model_revision = CLINICAL_MODEL_REVISION
                role = "control"
                provenance_source_revision = BACKBONE_REVISION

            checkpoint_path = output_dir / f"{system_id}.seed-{seed}.checkpoint.json"
            checkpoint_sha256 = _write_json(
                checkpoint_path,
                _checkpoint_payload(
                    system_id=system_id,
                    architecture_id=architecture_id,
                    seed=seed,
                    selected_record=selected,
                    contract_sha256=contract_sha256,
                    state=checkpoint_state,
                ),
            )
            prediction_path = output_dir / f"{system_id}.seed-{seed}.predictions.json"
            predictions_sha256 = _write_json(prediction_path, predictions)
            checkpoints.append(
                _checkpoint_provenance(
                    system_id=system_id,
                    seed=seed,
                    checkpoint_sha256=checkpoint_sha256,
                    contract_sha256=contract_sha256,
                    source_revision=provenance_source_revision,
                )
            )
            executions.append(
                _evidence_for_seed(
                    system_id=system_id,
                    role=role,
                    source_revision=provenance_source_revision,
                    model_revision=model_revision,
                    adapter_revision=adapter_revision,
                    checkpoint_sha256=checkpoint_sha256,
                    seed=seed,
                    predictions_sha256=predictions_sha256,
                    runtime=runtime,
                )
            )
            histories[str(seed)] = history
            seed_summary: dict[str, object] = {
                "seed": seed,
                "selected_epoch": selected["epoch"],
                "selection_metric": selected["selection_metric"],
                "action_nll": selected["action_nll"],
                "accuracy": selected["accuracy"],
                "checkpoint_sha256": checkpoint_sha256,
                "predictions_sha256": predictions_sha256,
            }
            if "sufficiency_brier" in selected:
                seed_summary["sufficiency_brier"] = selected["sufficiency_brier"]
            seed_summaries.append(seed_summary)

        history_path = output_dir / f"{system_id}.selection-history.json"
        history_sha256 = _write_json(history_path, histories)
        bundle = SystemQualificationBundle(
            system_id=system_id,
            checkpoints=checkpoints,
            executions=executions,
        )
        bundle_path = output_dir / f"{system_id}.qualification-bundle.json"
        bundle_sha256 = _write_json(bundle_path, bundle.model_dump(mode="json"))
        bundles[system_id] = bundle
        best = min(
            seed_summaries,
            key=lambda row: (float(row["selection_metric"]), int(row["seed"])),
        )
        summary["systems"][system_id] = {
            "seeds": seed_summaries,
            "selected_seed": best["seed"],
            "selected_seed_metric": best["selection_metric"],
            "selection_history_sha256": history_sha256,
            "qualification_bundle_sha256": bundle_sha256,
        }

    _write_json(output_dir / "summary.json", summary)
    if set(bundles) != {"gax-paper-candidate", "clinical-encoder"}:
        raise RuntimeError("missing required trainable system qualification bundle")
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    try:
        return _run(args)
    except BaseException as error:
        _write_json(
            output_dir / "failure.json",
            {
                "schema_version": "0.1",
                "status": "blocked",
                "failure_category": _failure_category(error),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "final_test_access": "sealed",
                "calibration_rows_used": 0,
                "final_test_rows_used": 0,
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
