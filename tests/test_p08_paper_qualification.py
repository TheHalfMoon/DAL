from __future__ import annotations

import pytest
from pydantic import ValidationError

from gaxbench.p08_paper_models import BACKBONE_MODEL_ID, BACKBONE_REVISION
from gaxbench.p08_real_systems import (
    CheckpointProvenance,
    ExecutionFailureCounts,
    RuntimeIdentity,
    SystemExecutionEvidence,
)
from gaxbench.p08_system_qualification import (
    PAPER_ADAPTER_REVISION,
    PAPER_MODEL_REVISION,
    SG000019_DEVELOPMENT_MANIFEST_SHA256,
    SG000019_PAPER_TRAINING_CONTRACT_SHA256,
    SystemQualificationBundle,
)

SOURCE_REVISION = "1" * 40


def _runtime() -> RuntimeIdentity:
    return RuntimeIdentity(
        os="linux",
        python="3.12",
        processor="x86_64",
        accelerator="cpu",
        packages={"torch": "2.8.0"},
    )


def _paper_bundle() -> SystemQualificationBundle:
    checkpoints: list[CheckpointProvenance] = []
    executions: list[SystemExecutionEvidence] = []
    for seed in (0, 1, 2):
        checkpoint_sha = f"{seed + 1:064x}"
        prediction_sha = f"{seed + 11:064x}"
        checkpoints.append(
            CheckpointProvenance(
                system_id="gax-paper-candidate",
                base_model_id=BACKBONE_MODEL_ID,
                base_model_revision=BACKBONE_REVISION,
                tokenizer_revision=BACKBONE_REVISION,
                development_manifest_sha256=SG000019_DEVELOPMENT_MANIFEST_SHA256,
                training_recipe_sha256=SG000019_PAPER_TRAINING_CONTRACT_SHA256,
                training_seed=seed,
                checkpoint_sha256=checkpoint_sha,
                source_revision=SOURCE_REVISION,
            )
        )
        executions.append(
            SystemExecutionEvidence(
                system_id="gax-paper-candidate",
                role="gax",
                source_revision=SOURCE_REVISION,
                model_revision=PAPER_MODEL_REVISION,
                tokenizer_revision=BACKBONE_REVISION,
                adapter_revision=PAPER_ADAPTER_REVISION,
                checkpoint_sha256=checkpoint_sha,
                training_seed=seed,
                dataset_manifest_sha256=SG000019_DEVELOPMENT_MANIFEST_SHA256,
                evaluation_role="development-selection",
                requested_count=90,
                completed_count=90,
                failures=ExecutionFailureCounts(),
                runtime=_runtime(),
                predictions_sha256=prediction_sha,
                status="complete",
            )
        )
    return SystemQualificationBundle(
        system_id="gax-paper-candidate",
        checkpoints=checkpoints,
        executions=executions,
    )


def test_exact_paper_bundle_is_accepted() -> None:
    bundle = _paper_bundle()

    assert bundle.qualification_status == "qualified"
    assert [checkpoint.training_seed for checkpoint in bundle.checkpoints] == [0, 1, 2]
    assert [execution.training_seed for execution in bundle.executions] == [0, 1, 2]


def test_paper_bundle_rejects_forged_training_contract_digest() -> None:
    payload = _paper_bundle().model_dump(mode="json")
    payload["checkpoints"][0]["training_recipe_sha256"] = "0" * 64

    with pytest.raises(ValidationError, match="training contract digest"):
        SystemQualificationBundle.model_validate(payload)


def test_paper_bundle_rejects_stale_adapter_revision() -> None:
    payload = _paper_bundle().model_dump(mode="json")
    payload["executions"][1]["adapter_revision"] = "stale-paper-adapter"

    with pytest.raises(ValidationError, match="adapter revision"):
        SystemQualificationBundle.model_validate(payload)


def test_paper_bundle_rejects_wrong_model_revision() -> None:
    payload = _paper_bundle().model_dump(mode="json")
    payload["executions"][2]["model_revision"] = "wrong-paper-model"

    with pytest.raises(ValidationError, match="model revision"):
        SystemQualificationBundle.model_validate(payload)
