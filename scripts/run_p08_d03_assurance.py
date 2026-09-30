from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from gaxbench.p08_paper_models import (
    BACKBONE_REVISION,
    DAL_PAPER_ARCHITECTURE,
    PaperTrainingContract,
    training_contract_digest,
)
from gaxbench.p08_real_systems import (
    CheckpointProvenance,
    DevelopmentTrainingManifest,
    SystemExecutionEvidence,
)
from gaxbench.p08_system_qualification import (
    PAPER_ADAPTER_REVISION,
    PAPER_MODEL_REVISION,
    SystemQualificationBundle,
)
from gaxbench.provenance import canonical_json_sha256, sha256_file


def _shared() -> Any:
    path = Path(__file__).with_name("run_p08_paper_training.py")
    spec = importlib.util.spec_from_file_location("dal_p08_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen P08 shared training runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S: Any = _shared()


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--training-contract", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _assurance(torch: Any) -> dict[str, Any]:
    return {
        "critic_scale": torch.nn.Parameter(torch.zeros(1)),
        "critic_bias": torch.nn.Parameter(torch.zeros(3)),
        "suff_scale": torch.nn.Parameter(torch.ones(1)),
        "suff_bias": torch.nn.Parameter(torch.zeros(1)),
    }


def _critic(base: Any, delta: Any, actions: Any, params: dict[str, Any]) -> Any:
    return base + params["critic_scale"] * (delta @ actions.T) + params["critic_bias"]


def _suff(delta: Any, params: dict[str, Any], torch: Any) -> tuple[Any, Any]:
    norm = torch.linalg.vector_norm(delta, ord=2, dim=1)
    present = params["suff_scale"] * norm + params["suff_bias"]
    return present, torch.zeros_like(present) + params["suff_bias"]


def _metrics(
    base: Any,
    delta: Any,
    labels: Any,
    actions: Any,
    params: dict[str, Any],
    torch: Any,
) -> dict[str, float]:
    with torch.no_grad():
        logits = _critic(base, delta, actions, params)
        nll, accuracy = S._classification_metrics(logits, labels, torch=torch)
        present, withheld = _suff(delta, params, torch)
        brier = float(
            torch.cat(
                [
                    (torch.sigmoid(present) - 1.0).square(),
                    torch.sigmoid(withheld).square(),
                ]
            )
            .mean()
            .item()
        )
    return {
        "selection_metric": nll + 0.5 * brier,
        "critic_nll": nll,
        "critic_accuracy": accuracy,
        "sufficiency_brier": brier,
    }


def _train_assurance(
    embeddings: dict[str, Any],
    contract: PaperTrainingContract,
    control: dict[str, Any],
    torch: Any,
) -> tuple[dict[str, Any], list[dict[str, float | int]], dict[str, float | int]]:
    params = _assurance(torch)
    optimizer = torch.optim.AdamW(
        list(params.values()),
        lr=contract.recipe.learning_rate,
        weight_decay=contract.recipe.weight_decay,
    )
    train_base = S._control_logits(embeddings["train_full"], control).detach()
    select_base = S._control_logits(embeddings["selection_full"], control).detach()
    control_nll, control_accuracy = S._classification_metrics(
        select_base, embeddings["selection_labels"], torch=torch
    )
    tolerance = contract.recipe.critic_nll_tolerance
    first = _metrics(
        select_base,
        embeddings["selection_delta"],
        embeddings["selection_labels"],
        embeddings["action_embeddings"],
        params,
        torch,
    )
    if abs(first["critic_nll"] - control_nll) > tolerance:
        raise RuntimeError("epoch-zero shadow critic must reproduce control NLL")
    record: dict[str, float | int] = {
        "epoch": 0,
        **first,
        "action_nll": control_nll,
        "accuracy": control_accuracy,
    }
    history = [record]
    best_metric = first["selection_metric"]
    best_state = S._clone_parameters(params)
    best_record = dict(record)
    count = int(embeddings["train_full"].shape[0])
    batch = contract.recipe.head_batch_size

    for epoch in range(1, contract.recipe.epochs + 1):
        for start in range(0, count, batch):
            stop = min(start + batch, count)
            optimizer.zero_grad(set_to_none=True)
            critic_logits = _critic(
                train_base[start:stop],
                embeddings["train_delta"][start:stop],
                embeddings["action_embeddings"],
                params,
            )
            critic_loss = torch.nn.functional.cross_entropy(
                critic_logits, embeddings["train_labels"][start:stop]
            )
            present, withheld = _suff(
                embeddings["train_delta"][start:stop], params, torch
            )
            suff_loss = torch.nn.functional.binary_cross_entropy_with_logits(
                torch.cat([present, withheld]),
                torch.cat([torch.ones_like(present), torch.zeros_like(withheld)]),
            )
            loss = (
                contract.recipe.assurance_loss_weight * critic_loss
                + contract.recipe.sufficiency_loss_weight * suff_loss
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(params.values()), contract.recipe.gradient_clip_norm
            )
            optimizer.step()

        seen = _metrics(
            select_base,
            embeddings["selection_delta"],
            embeddings["selection_labels"],
            embeddings["action_embeddings"],
            params,
            torch,
        )
        record = {
            "epoch": epoch,
            **seen,
            "action_nll": control_nll,
            "accuracy": control_accuracy,
        }
        history.append(record)
        if seen["critic_nll"] <= control_nll + tolerance and (
            seen["selection_metric"] < best_metric
        ):
            best_metric = seen["selection_metric"]
            best_state = S._clone_parameters(params)
            best_record = dict(record)

    S._restore_parameters(params, best_state)
    return params, history, best_record


def _paper_predictions(
    seed: int,
    items: list[Any],
    action_logits: Any,
    critic_logits: Any,
    sufficiency: Any,
    torch: Any,
) -> list[dict[str, object]]:
    action_probs = S._probabilities(action_logits, torch)
    critic_probs = S._probabilities(critic_logits, torch)
    suff_probs = torch.sigmoid(sufficiency).detach().cpu().tolist()
    rows: list[dict[str, object]] = []
    for index, item in enumerate(items):
        action = action_probs[index]
        critic = critic_probs[index]
        rows.append(
            {
                "item_id": item.id,
                "gold_action": item.gold.action,
                "probabilities": dict(zip(S._ACTION_ORDER, action, strict=True)),
                "critic_probabilities": dict(
                    zip(S._ACTION_ORDER, critic, strict=True)
                ),
                "critic_disagrees_with_action": (
                    max(range(3), key=lambda choice: action[choice])
                    != max(range(3), key=lambda choice: critic[choice])
                ),
                "sufficiency_probability": suff_probs[index],
                "system_id": "gax-paper-candidate",
                "training_seed": seed,
            }
        )
    return rows


def _run(args: argparse.Namespace) -> int:
    source_revision = str(args.source_revision)
    if len(source_revision) != 40 or any(
        char not in "0123456789abcdef" for char in source_revision
    ):
        raise ValueError("source revision must be an exact lowercase git SHA")

    manifest = S._load_json_model(
        Path(args.development_manifest), DevelopmentTrainingManifest
    )
    contract = S._load_json_model(Path(args.training_contract), PaperTrainingContract)
    contract_sha = training_contract_digest(contract)
    train, selection = S._selected_records(Path(args.source), manifest)

    import torch
    import transformers

    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
    torch.use_deterministic_algorithms(True)
    embeddings = S._prepare_embeddings(
        train, selection, contract, torch=torch, transformers=transformers
    )
    runtime = S._runtime_identity()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    control_cp: list[CheckpointProvenance] = []
    control_ev: list[SystemExecutionEvidence] = []
    paper_cp: list[CheckpointProvenance] = []
    paper_ev: list[SystemExecutionEvidence] = []
    control_rows: list[dict[str, object]] = []
    paper_rows: list[dict[str, object]] = []

    for seed in contract.recipe.training_seeds:
        control, control_history, control_selected = S._train_control(
            embeddings, contract, seed, torch=torch
        )
        control_logits = S._control_logits(embeddings["selection_full"], control)
        control_checkpoint = S._write_json(
            out / f"clinical-encoder.seed-{seed}.checkpoint.json",
            S._checkpoint_payload(
                system_id="clinical-encoder",
                architecture_id=S.CLINICAL_CONTROL_ARCHITECTURE,
                seed=seed,
                selected_record=control_selected,
                contract_sha256=contract_sha,
                state=S._state_payload(control),
            ),
        )
        control_predictions = S._write_json(
            out / f"clinical-encoder.seed-{seed}.predictions.json",
            S._prediction_payload(
                "clinical-encoder",
                seed,
                embeddings["selection_items"],
                control_logits,
                torch=torch,
            ),
        )
        S._write_json(
            out / f"clinical-encoder.seed-{seed}.selection-history.json",
            control_history,
        )
        control_cp.append(
            S._checkpoint_provenance(
                system_id="clinical-encoder",
                seed=seed,
                checkpoint_sha256=control_checkpoint,
                contract_sha256=contract_sha,
                source_revision=BACKBONE_REVISION,
            )
        )
        control_ev.append(
            S._evidence_for_seed(
                system_id="clinical-encoder",
                role="control",
                source_revision=BACKBONE_REVISION,
                model_revision=S.CLINICAL_MODEL_REVISION,
                adapter_revision=S.CONTROL_ADAPTER_REVISION,
                checkpoint_sha256=control_checkpoint,
                seed=seed,
                predictions_sha256=control_predictions,
                runtime=runtime,
            )
        )
        control_rows.append(
            {
                "seed": seed,
                "selected_epoch": control_selected["epoch"],
                "selection_metric": control_selected["selection_metric"],
                "action_nll": control_selected["action_nll"],
                "accuracy": control_selected["accuracy"],
                "checkpoint_sha256": control_checkpoint,
                "predictions_sha256": control_predictions,
            }
        )

        assurance, paper_history, paper_selected = _train_assurance(
            embeddings, contract, control, torch
        )
        paper_action = S._control_logits(embeddings["selection_full"], control)
        if not bool(torch.equal(control_logits, paper_action)):
            raise RuntimeError("D03 action output drifted from same-seed control")
        critic_logits = _critic(
            paper_action,
            embeddings["selection_delta"],
            embeddings["action_embeddings"],
            assurance,
        )
        present, _ = _suff(embeddings["selection_delta"], assurance, torch)
        paper_state = S._clone_parameters(control)
        paper_state.update(S._clone_parameters(assurance))
        checkpoint_payload = {
            "schema_version": "0.3",
            "system_id": "gax-paper-candidate",
            "architecture_id": DAL_PAPER_ARCHITECTURE,
            "training_seed": seed,
            "selected_epoch": paper_selected["epoch"],
            "selection_metric": paper_selected["selection_metric"],
            "action_nll": paper_selected["action_nll"],
            "accuracy": paper_selected["accuracy"],
            "critic_nll": paper_selected["critic_nll"],
            "critic_accuracy": paper_selected["critic_accuracy"],
            "sufficiency_brier": paper_selected["sufficiency_brier"],
            "training_contract_sha256": contract_sha,
            "development_manifest_sha256": (
                "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
            ),
            "base_model_id": S.BACKBONE_MODEL_ID,
            "base_model_revision": BACKBONE_REVISION,
            "tokenizer_revision": BACKBONE_REVISION,
            "state": S._state_payload(paper_state),
            "final_test_access": "sealed",
        }
        paper_checkpoint = S._write_json(
            out / f"gax-paper-candidate.seed-{seed}.checkpoint.json",
            checkpoint_payload,
        )
        paper_predictions = S._write_json(
            out / f"gax-paper-candidate.seed-{seed}.predictions.json",
            _paper_predictions(
                seed,
                embeddings["selection_items"],
                paper_action,
                critic_logits,
                present,
                torch,
            ),
        )
        S._write_json(
            out / f"gax-paper-candidate.seed-{seed}.selection-history.json",
            paper_history,
        )
        paper_cp.append(
            S._checkpoint_provenance(
                system_id="gax-paper-candidate",
                seed=seed,
                checkpoint_sha256=paper_checkpoint,
                contract_sha256=contract_sha,
                source_revision=source_revision,
            )
        )
        paper_ev.append(
            S._evidence_for_seed(
                system_id="gax-paper-candidate",
                role="gax",
                source_revision=source_revision,
                model_revision=PAPER_MODEL_REVISION,
                adapter_revision=PAPER_ADAPTER_REVISION,
                checkpoint_sha256=paper_checkpoint,
                seed=seed,
                predictions_sha256=paper_predictions,
                runtime=runtime,
            )
        )
        paper_rows.append(
            {
                "seed": seed,
                "selected_epoch": paper_selected["epoch"],
                "selection_metric": paper_selected["selection_metric"],
                "action_nll": paper_selected["action_nll"],
                "accuracy": paper_selected["accuracy"],
                "critic_nll": paper_selected["critic_nll"],
                "critic_accuracy": paper_selected["critic_accuracy"],
                "sufficiency_brier": paper_selected["sufficiency_brier"],
                "action_equivalent_to_control": True,
                "checkpoint_sha256": paper_checkpoint,
                "predictions_sha256": paper_predictions,
            }
        )

    control_bundle = SystemQualificationBundle(
        system_id="clinical-encoder", checkpoints=control_cp, executions=control_ev
    )
    paper_bundle = SystemQualificationBundle(
        system_id="gax-paper-candidate", checkpoints=paper_cp, executions=paper_ev
    )
    control_bundle_sha = S._write_json(
        out / "clinical-encoder.qualification-bundle.json",
        control_bundle.model_dump(mode="json"),
    )
    paper_bundle_sha = S._write_json(
        out / "gax-paper-candidate.qualification-bundle.json",
        paper_bundle.model_dump(mode="json"),
    )

    control_selected = min(
        control_rows,
        key=lambda row: (float(row["action_nll"]), int(row["seed"])),
    )
    selected_seed = int(control_selected["seed"])
    paper_selected = next(
        row for row in paper_rows if int(row["seed"]) == selected_seed
    )
    equivalent = all(bool(row["action_equivalent_to_control"]) for row in paper_rows)
    nondegrading = (
        float(paper_selected["critic_nll"])
        <= float(control_selected["action_nll"])
        + contract.recipe.critic_nll_tolerance
    )
    sufficient = (
        float(paper_selected["sufficiency_brier"])
        <= contract.recipe.sufficiency_brier_acceptance_ceiling
    )
    accepted = equivalent and nondegrading and sufficient
    summary = {
        "schema_version": "0.3",
        "implementation_source_revision": source_revision,
        "training_contract_sha256": contract_sha,
        "development_manifest_sha256": canonical_json_sha256(
            manifest.model_dump(mode="json")
        ),
        "architecture_search_boundary": contract.recipe.architecture_search_boundary,
        "architecture_search_closed_after_d03": True,
        "systems": {
            "clinical-encoder": {
                "seeds": control_rows,
                "selected_seed": selected_seed,
                "selected_seed_metric": control_selected["action_nll"],
                "qualification_bundle_sha256": control_bundle_sha,
            },
            "gax-paper-candidate": {
                "seeds": paper_rows,
                "selected_seed": selected_seed,
                "selected_seed_metric": paper_selected["selection_metric"],
                "selected_seed_matches_control": True,
                "qualification_bundle_sha256": paper_bundle_sha,
            },
        },
        "paper_action_equivalence_verified": equivalent,
        "paper_selected_seed_matches_control": True,
        "paper_selected_critic_nll_nondegradation": nondegrading,
        "paper_selected_sufficiency_brier_accepted": sufficient,
        "paper_development_decision": "accepted" if accepted else "rejected",
        "paper_acceptance_criteria": {
            "critic_nll_tolerance": contract.recipe.critic_nll_tolerance,
            "sufficiency_brier_ceiling": (
                contract.recipe.sufficiency_brier_acceptance_ceiling
            ),
        },
        "final_test_access": "sealed",
        "calibration_rows_used": 0,
        "final_test_rows_used": 0,
    }
    S._write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    args = _args()
    out = Path(args.output_dir)
    try:
        return _run(args)
    except BaseException as error:
        out.mkdir(parents=True, exist_ok=True)
        path = out / "failure.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "0.3",
                    "status": "blocked",
                    "failure_category": S._failure_category(error),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "final_test_access": "sealed",
                    "calibration_rows_used": 0,
                    "final_test_rows_used": 0,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        sha256_file(path)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
