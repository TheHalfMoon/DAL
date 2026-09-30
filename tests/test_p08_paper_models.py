from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.p08_paper_models import (
    BACKBONE_REVISION,
    CLINICAL_CONTROL_ARCHITECTURE,
    DAL_PAPER_ARCHITECTURE,
    PaperTrainingContract,
    canonical_training_contract,
    training_contract_digest,
)

ROOT = Path(__file__).parents[1]
CONTRACT_PATH = ROOT / "registry" / "p08_paper_training_contract_sg000019.json"


def _persisted() -> PaperTrainingContract:
    return PaperTrainingContract.model_validate(
        json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    )


def test_persisted_contract_matches_canonical_builder() -> None:
    persisted = _persisted()
    canonical = canonical_training_contract()

    assert persisted == canonical
    assert training_contract_digest(persisted) == training_contract_digest(canonical)
    assert len(training_contract_digest(persisted)) == 64
    assert persisted.final_test_access == "sealed"
    assert persisted.recipe.training_seeds == [0, 1, 2]
    assert persisted.recipe.calibration_rows_used_for_training is False
    assert persisted.recipe.final_test_rows_used_for_training_or_selection is False


def test_paper_and_control_share_exact_frozen_backbone_and_input_policy() -> None:
    contract = _persisted()
    paper, control = contract.systems

    assert paper.architecture.frozen_backbone == control.architecture.frozen_backbone
    assert paper.architecture.encoder_input == control.architecture.encoder_input
    assert paper.architecture.frozen_backbone.model_revision == BACKBONE_REVISION
    assert paper.architecture.frozen_backbone.tokenizer_revision == BACKBONE_REVISION
    assert paper.architecture.frozen_backbone.trainable is False
    assert paper.architecture.frozen_backbone.embedding_normalization == "l2"
    assert paper.architecture.encoder_input.max_length == 512
    assert paper.architecture.encoder_input.encoding_mode == (
        "tokenizer-pair-question-evidence"
    )
    assert paper.architecture.encoder_input.truncation_policy == (
        "preserve-question-truncate-evidence"
    )


def test_shadow_assurance_candidate_cannot_replace_the_control_action_head() -> None:
    contract = _persisted()
    paper, control = contract.systems

    assert paper.architecture.architecture_id == DAL_PAPER_ARCHITECTURE
    assert control.architecture.architecture_id == CLINICAL_CONTROL_ARCHITECTURE
    assert paper.architecture.trainable_parameter_formula == "3H+9"
    assert control.architecture.trainable_parameter_formula == "3H+3"
    assert contract.capacity_matching_note == (
        "paper-candidate=3H+9; clinical-control=3H+3; "
        "delta=6 scalar assurance parameters"
    )
    assert paper.architecture.autoregressive_generation is False
    assert paper.architecture.abstain_is_candidate_action is False
    assert paper.architecture.action_scoring == (
        "nested-clinical-action-head+shadow-typed-evidence-critic"
    )
    assert paper.architecture.output_action_policy == (
        "identical-to-same-seed-clinical-control"
    )
    assert paper.action_head_training_policy == (
        "clone-selected-same-seed-control-then-freeze"
    )
    assert control.action_head_training_policy == "train-on-evidence-present"
    assert paper.architecture.sufficiency_mechanism == (
        "logistic-head-over-evidence-delta-norm"
    )
    assert control.architecture.sufficiency_mechanism == "none"


def test_d03_is_the_final_development_architecture_search_revision() -> None:
    recipe = _persisted().recipe

    assert recipe.schema_version == "0.3"
    assert recipe.recipe_revision == "dal-p08-paper-training-v0.3"
    assert recipe.architecture_search_boundary == "D03-final-development-candidate"
    assert recipe.architecture_search_closed_after_this_revision is True
    assert recipe.paper_action_head_source == "same-seed-selected-clinical-control"
    assert recipe.paper_action_head_trainable_during_assurance_stage is False
    assert recipe.assurance_epoch_zero_included is True
    assert recipe.critic_initialization == "zero-residual-to-control-logits"
    assert recipe.paper_action_equivalence_required is True
    assert recipe.critic_nll_nondegradation_required is True
    assert recipe.critic_nll_tolerance == 1e-9
    assert recipe.sufficiency_brier_acceptance_ceiling == 0.25


def test_checkpoint_and_seed_selection_are_prospectively_frozen() -> None:
    recipe = _persisted().recipe

    assert recipe.batch_order == "manifest-order-no-shuffle"
    assert recipe.initialization == (
        "xavier-linear-zero-bias-zero-critic-scale-unit-suff-scale"
    )
    assert recipe.deterministic_algorithms is True
    assert recipe.control_epoch_selection_rule == "minimum-development-action-nll"
    assert recipe.paper_assurance_epoch_selection_rule == (
        "minimum-development-assurance-metric-subject-to-critic-nll-nondegradation"
    )
    assert recipe.epoch_selection_tie_break == "lower-epoch"
    assert recipe.control_seed_selection_rule == "minimum-development-action-nll"
    assert recipe.paper_seed_selection_rule == "same-as-control-selected-seed"
    assert recipe.seed_selection_tie_break == "lower-seed"


def test_contract_rejects_unmatched_backbone() -> None:
    payload = _persisted().model_dump(mode="json")
    payload["systems"][1]["architecture"]["frozen_backbone"]["model_revision"] = "0" * 40
    payload["systems"][1]["architecture"]["frozen_backbone"]["tokenizer_revision"] = "0" * 40

    with pytest.raises(ValidationError):
        PaperTrainingContract.model_validate(payload)


def test_contract_rejects_final_test_use() -> None:
    payload = _persisted().model_dump(mode="json")
    payload["recipe"]["final_test_rows_used_for_training_or_selection"] = True

    with pytest.raises(ValidationError):
        PaperTrainingContract.model_validate(payload)


def test_contract_rejects_replacing_paper_candidate_with_control_architecture() -> None:
    payload = _persisted().model_dump(mode="json")
    payload["systems"][0]["architecture"]["architecture_id"] = (
        CLINICAL_CONTROL_ARCHITECTURE
    )

    with pytest.raises(ValidationError, match="paper candidate"):
        PaperTrainingContract.model_validate(payload)


def test_contract_rejects_action_head_policy_drift() -> None:
    payload = _persisted().model_dump(mode="json")
    payload["systems"][0]["action_head_training_policy"] = "train-on-evidence-present"

    with pytest.raises(ValidationError, match="action-head training policy"):
        PaperTrainingContract.model_validate(payload)
