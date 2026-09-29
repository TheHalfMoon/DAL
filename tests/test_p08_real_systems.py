from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_real_systems import (
    CheckpointProvenance,
    ExecutionFailureCounts,
    RuntimeIdentity,
    SystemExecutionEvidence,
    build_development_training_manifest,
    development_manifest_digest,
)
from gaxbench.pubmedqa import PubMedQARecord, PubMedQASplitManifest

ROOT = Path(__file__).parents[1]
PARENT_MANIFEST = ROOT / "registry" / "pubmedqa_pqal_split_manifest.json"
SHA256 = "a" * 64


def _parent() -> PubMedQASplitManifest:
    return PubMedQASplitManifest.model_validate(
        json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
    )


def _records(parent: PubMedQASplitManifest) -> list[tuple[str, PubMedQARecord]]:
    decisions = ("yes", "no", "maybe")
    return [
        (
            pmid,
            PubMedQARecord(
                QUESTION=f"Question {pmid}?",
                CONTEXTS=[f"Evidence {pmid}."],
                final_decision=decisions[index % len(decisions)],
                LONG_ANSWER=f"Answer {pmid}.",
            ),
        )
        for index, pmid in enumerate(parent.validation_ids)
    ]


def _runtime() -> RuntimeIdentity:
    return RuntimeIdentity(
        os="linux",
        python="3.12.11",
        processor="x86_64",
        accelerator="cpu",
        packages={"gaxbench": "0.1.0"},
    )


def test_nested_development_split_is_deterministic_disjoint_and_complete() -> None:
    parent = _parent()
    records = _records(parent)

    first = build_development_training_manifest(records, parent)
    second = build_development_training_manifest(list(reversed(records)), parent)

    assert first == second
    assert len(first.train_ids) == 360
    assert len(first.selection_ids) == 90
    assert sum(first.train_action_counts.values()) == 360
    assert sum(first.selection_action_counts.values()) == 90
    assert first.train_action_counts == {"yes": 120, "no": 120, "maybe": 120}
    assert first.selection_action_counts == {"yes": 30, "no": 30, "maybe": 30}
    assert set(first.train_ids).isdisjoint(first.selection_ids)
    assert set(first.train_ids).isdisjoint(parent.calibration_ids)
    assert set(first.train_ids).isdisjoint(parent.test_ids)
    assert set(first.selection_ids).isdisjoint(parent.calibration_ids)
    assert set(first.selection_ids).isdisjoint(parent.test_ids)
    assert set(first.train_ids) | set(first.selection_ids) == set(parent.validation_ids)
    assert len(development_manifest_digest(first)) == 64
    assert first.final_test_access == "sealed"


def test_nested_development_split_rejects_missing_source_rows() -> None:
    parent = _parent()
    records = _records(parent)

    with pytest.raises(ValueError, match="missing development PMIDs"):
        build_development_training_manifest(records[:-1], parent)


def test_nested_development_split_rejects_parent_manifest_drift() -> None:
    parent = _parent()
    payload = parent.model_dump(mode="json")
    validation_ids = list(payload["validation_ids"])
    calibration_ids = list(payload["calibration_ids"])
    validation_ids[0], calibration_ids[0] = calibration_ids[0], validation_ids[0]
    payload["validation_ids"] = sorted(validation_ids)
    payload["calibration_ids"] = sorted(calibration_ids)
    drifted = PubMedQASplitManifest.model_validate(payload)

    with pytest.raises(ValueError, match="frozen digest"):
        build_development_training_manifest(_records(drifted), drifted)


def test_complete_paper_candidate_execution_evidence_is_digest_bound() -> None:
    evidence = SystemExecutionEvidence(
        system_id="gax-paper-candidate",
        role="gax",
        source_revision="ef8f2f08a0149029f31d8213f07233b3168b8f2d",
        model_revision="dal-paper-candidate-v0.1",
        tokenizer_revision="5e17e2f25260b6993e0fb60485f94678ff29779a",
        adapter_revision="dal-p08-real-system-v0.1",
        checkpoint_sha256=SHA256,
        training_seed=0,
        dataset_manifest_sha256=SHA256,
        evaluation_role="development-selection",
        requested_count=90,
        completed_count=90,
        failures=ExecutionFailureCounts(),
        runtime=_runtime(),
        predictions_sha256=SHA256,
        status="complete",
    )

    assert evidence.final_test_access == "sealed"
    assert evidence.failures.total() == 0


def test_execution_evidence_preserves_failures_and_rejects_count_loss() -> None:
    partial = SystemExecutionEvidence(
        system_id="laya",
        role="baseline",
        source_revision="3c68ca2ccf6a83640ab80c20379503fe72c772fd",
        model_revision="immutable-hf-revision",
        adapter_revision="dal-p08-real-system-v0.1",
        dataset_manifest_sha256=SHA256,
        evaluation_role="development-selection",
        requested_count=90,
        completed_count=88,
        failures=ExecutionFailureCounts(timeout=2),
        runtime=_runtime(),
        predictions_sha256=SHA256,
        status="partial",
    )
    assert partial.failures.total() == 2

    with pytest.raises(ValidationError, match="requested_count"):
        SystemExecutionEvidence(
            system_id="laya",
            role="baseline",
            model_revision="immutable-hf-revision",
            adapter_revision="dal-p08-real-system-v0.1",
            dataset_manifest_sha256=SHA256,
            evaluation_role="development-selection",
            requested_count=90,
            completed_count=88,
            failures=ExecutionFailureCounts(timeout=1),
            runtime=_runtime(),
            predictions_sha256=SHA256,
            status="partial",
        )


def test_paper_candidate_evidence_requires_preregistered_seed_and_checkpoint() -> None:
    with pytest.raises(ValidationError, match="checkpoint_sha256"):
        SystemExecutionEvidence(
            system_id="gax-paper-candidate",
            role="gax",
            model_revision="dal-paper-candidate-v0.1",
            adapter_revision="dal-p08-real-system-v0.1",
            training_seed=0,
            dataset_manifest_sha256=SHA256,
            evaluation_role="development-selection",
            requested_count=1,
            completed_count=1,
            failures=ExecutionFailureCounts(),
            runtime=_runtime(),
            predictions_sha256=SHA256,
            status="complete",
        )

    with pytest.raises(ValidationError, match="preregistered"):
        SystemExecutionEvidence(
            system_id="gax-paper-candidate",
            role="gax",
            model_revision="dal-paper-candidate-v0.1",
            adapter_revision="dal-p08-real-system-v0.1",
            checkpoint_sha256=SHA256,
            training_seed=7,
            dataset_manifest_sha256=SHA256,
            evaluation_role="development-selection",
            requested_count=1,
            completed_count=1,
            failures=ExecutionFailureCounts(),
            runtime=_runtime(),
            predictions_sha256=SHA256,
            status="complete",
        )


def test_checkpoint_provenance_rejects_non_preregistered_seed() -> None:
    with pytest.raises(ValidationError, match="preregistered"):
        CheckpointProvenance(
            system_id="clinical-encoder",
            base_model_id="thomas-sounack/BioClinical-ModernBERT-base",
            base_model_revision="5e17e2f25260b6993e0fb60485f94678ff29779a",
            tokenizer_revision="5e17e2f25260b6993e0fb60485f94678ff29779a",
            development_manifest_sha256=SHA256,
            training_recipe_sha256=SHA256,
            training_seed=5,
            checkpoint_sha256=SHA256,
            source_revision="ef8f2f08a0149029f31d8213f07233b3168b8f2d",
        )
