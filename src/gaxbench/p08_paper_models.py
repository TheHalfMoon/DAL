from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

DAL_PAPER_ARCHITECTURE = "dal-shadow-assurance-critic-v0.3"
CLINICAL_CONTROL_ARCHITECTURE = "bioclinical-linear-control-v0.1"
BACKBONE_MODEL_ID = "thomas-sounack/BioClinical-ModernBERT-base"
BACKBONE_REVISION = "5e17e2f25260b6993e0fb60485f94678ff29779a"
DEVELOPMENT_MANIFEST_SHA256 = "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
DEVELOPMENT_LEAKAGE_SHA256 = "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
TRAINING_SEEDS = (0, 1, 2)

SystemID = Literal["gax-paper-candidate", "clinical-encoder"]
ArchitectureID = Literal[
    "dal-shadow-assurance-critic-v0.3",
    "bioclinical-linear-control-v0.1",
]
SelectionMetric = Literal[
    "critic-nll+0.5-sufficiency-brier",
    "action-nll",
]


class FrozenBackboneIdentity(StrictModel):
    model_id: Literal["thomas-sounack/BioClinical-ModernBERT-base"] = (
        "thomas-sounack/BioClinical-ModernBERT-base"
    )
    model_revision: Literal["5e17e2f25260b6993e0fb60485f94678ff29779a"] = (
        "5e17e2f25260b6993e0fb60485f94678ff29779a"
    )
    tokenizer_revision: Literal["5e17e2f25260b6993e0fb60485f94678ff29779a"] = (
        "5e17e2f25260b6993e0fb60485f94678ff29779a"
    )
    trainable: Literal[False] = False
    pooling: Literal["attention-mask-mean"] = "attention-mask-mean"
    embedding_normalization: Literal["l2"] = "l2"


class EncoderInputPolicy(StrictModel):
    max_length: Literal[512] = 512
    encoding_mode: Literal["tokenizer-pair-question-evidence"] = (
        "tokenizer-pair-question-evidence"
    )
    evidence_joiner: Literal["\n"] = "\n"
    truncation_policy: Literal["preserve-question-truncate-evidence"] = (
        "preserve-question-truncate-evidence"
    )
    action_text_source: Literal["benchmark-action-description"] = (
        "benchmark-action-description"
    )
    withheld_representation: Literal["question-only"] = "question-only"


class ModelArchitectureContract(StrictModel):
    system_id: SystemID
    architecture_id: ArchitectureID
    frozen_backbone: FrozenBackboneIdentity = Field(default_factory=FrozenBackboneIdentity)
    encoder_input: EncoderInputPolicy = Field(default_factory=EncoderInputPolicy)
    action_distribution: Literal["closed-typed-softmax"] = "closed-typed-softmax"
    autoregressive_generation: Literal[False] = False
    abstain_is_candidate_action: Literal[False] = False
    state_representation: str = Field(min_length=1)
    action_scoring: str = Field(min_length=1)
    output_action_policy: str = Field(min_length=1)
    sufficiency_mechanism: str = Field(min_length=1)
    trainable_parameter_formula: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_system_contract(self) -> ModelArchitectureContract:
        if self.system_id == "gax-paper-candidate":
            if self.architecture_id != DAL_PAPER_ARCHITECTURE:
                raise ValueError("paper candidate must use the frozen DAL paper architecture")
            if self.state_representation != "full-state+question-only+evidence-delta":
                raise ValueError("paper candidate state representation drift")
            if self.action_scoring != "nested-clinical-action-head+shadow-typed-evidence-critic":
                raise ValueError("paper candidate action scoring drift")
            if self.output_action_policy != "identical-to-same-seed-clinical-control":
                raise ValueError("paper candidate output action policy drift")
            if self.sufficiency_mechanism != "logistic-head-over-evidence-delta-norm":
                raise ValueError("paper candidate sufficiency mechanism drift")
            if self.trainable_parameter_formula != "3H+9":
                raise ValueError("paper candidate parameter formula drift")
        else:
            if self.architecture_id != CLINICAL_CONTROL_ARCHITECTURE:
                raise ValueError("clinical control must use the frozen control architecture")
            if self.state_representation != "full-state":
                raise ValueError("clinical control state representation drift")
            if self.action_scoring != "three-class-linear-head-over-frozen-state":
                raise ValueError("clinical control action scoring drift")
            if self.output_action_policy != "selected-linear-head":
                raise ValueError("clinical control output action policy drift")
            if self.sufficiency_mechanism != "none":
                raise ValueError("clinical control must not include a sufficiency head")
            if self.trainable_parameter_formula != "3H+3":
                raise ValueError("clinical control parameter formula drift")
        return self


class TrainingRecipe(StrictModel):
    schema_version: Literal["0.3"] = "0.3"
    recipe_revision: Literal["dal-p08-paper-training-v0.3"] = "dal-p08-paper-training-v0.3"
    architecture_search_boundary: Literal["D03-final-development-candidate"] = (
        "D03-final-development-candidate"
    )
    development_manifest_sha256: Literal[
        "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
    ] = "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
    development_leakage_audit_sha256: Literal[
        "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
    ] = "1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76"
    train_count: Literal[360] = 360
    selection_count: Literal[90] = 90
    training_seeds: list[int] = Field(default_factory=lambda: list(TRAINING_SEEDS))
    encoder_batch_size: Literal[8] = 8
    head_batch_size: Literal[32] = 32
    batch_order: Literal["manifest-order-no-shuffle"] = "manifest-order-no-shuffle"
    epochs: Literal[80] = 80
    optimizer: Literal["adamw"] = "adamw"
    learning_rate: float = Field(default=0.02, ge=0.02, le=0.02)
    weight_decay: float = Field(default=0.0001, ge=0.0001, le=0.0001)
    gradient_clip_norm: float = Field(default=1.0, ge=1.0, le=1.0)
    assurance_loss_weight: float = Field(default=1.0, ge=1.0, le=1.0)
    sufficiency_loss_weight: float = Field(default=0.5, ge=0.5, le=0.5)
    initialization: Literal[
        "xavier-linear-zero-bias-zero-critic-scale-unit-suff-scale"
    ] = "xavier-linear-zero-bias-zero-critic-scale-unit-suff-scale"
    deterministic_algorithms: Literal[True] = True
    control_epoch_selection_rule: Literal["minimum-development-action-nll"] = (
        "minimum-development-action-nll"
    )
    paper_action_head_source: Literal["same-seed-selected-clinical-control"] = (
        "same-seed-selected-clinical-control"
    )
    paper_action_head_trainable_during_assurance_stage: Literal[False] = False
    assurance_epoch_zero_included: Literal[True] = True
    critic_initialization: Literal["zero-residual-to-control-logits"] = (
        "zero-residual-to-control-logits"
    )
    paper_assurance_epoch_selection_rule: Literal[
        "minimum-development-assurance-metric-subject-to-critic-nll-nondegradation"
    ] = "minimum-development-assurance-metric-subject-to-critic-nll-nondegradation"
    epoch_selection_tie_break: Literal["lower-epoch"] = "lower-epoch"
    control_seed_selection_rule: Literal["minimum-development-action-nll"] = (
        "minimum-development-action-nll"
    )
    paper_seed_selection_rule: Literal["same-as-control-selected-seed"] = (
        "same-as-control-selected-seed"
    )
    seed_selection_tie_break: Literal["lower-seed"] = "lower-seed"
    paper_action_equivalence_required: Literal[True] = True
    critic_nll_nondegradation_required: Literal[True] = True
    critic_nll_tolerance: float = Field(default=1e-9, ge=1e-9, le=1e-9)
    sufficiency_brier_acceptance_ceiling: float = Field(
        default=0.25, ge=0.25, le=0.25
    )
    architecture_search_closed_after_this_revision: Literal[True] = True
    final_test_access: Literal["sealed"] = "sealed"
    calibration_rows_used_for_training: Literal[False] = False
    final_test_rows_used_for_training_or_selection: Literal[False] = False

    @model_validator(mode="after")
    def validate_frozen_recipe(self) -> TrainingRecipe:
        if self.training_seeds != list(TRAINING_SEEDS):
            raise ValueError("training seeds must remain exactly [0, 1, 2]")
        return self


class SystemTrainingPlan(StrictModel):
    system_id: SystemID
    architecture: ModelArchitectureContract
    selection_metric: SelectionMetric
    action_head_training_policy: Literal[
        "clone-selected-same-seed-control-then-freeze",
        "train-on-evidence-present",
    ]
    train_sufficiency_on_present_withheld_pairs: bool

    @model_validator(mode="after")
    def validate_plan(self) -> SystemTrainingPlan:
        if self.architecture.system_id != self.system_id:
            raise ValueError("system id must match architecture contract")
        if self.system_id == "gax-paper-candidate":
            if self.selection_metric != "critic-nll+0.5-sufficiency-brier":
                raise ValueError("paper candidate selection metric drift")
            if self.action_head_training_policy != (
                "clone-selected-same-seed-control-then-freeze"
            ):
                raise ValueError("paper candidate action-head training policy drift")
            if not self.train_sufficiency_on_present_withheld_pairs:
                raise ValueError(
                    "paper candidate must train the sufficiency head on paired evidence"
                )
        else:
            if self.selection_metric != "action-nll":
                raise ValueError("clinical control selection metric drift")
            if self.action_head_training_policy != "train-on-evidence-present":
                raise ValueError("clinical control action-head training policy drift")
            if self.train_sufficiency_on_present_withheld_pairs:
                raise ValueError("clinical control must not train a sufficiency head")
        return self


class PaperTrainingContract(StrictModel):
    schema_version: Literal["0.3"] = "0.3"
    backbone: FrozenBackboneIdentity = Field(default_factory=FrozenBackboneIdentity)
    encoder_input: EncoderInputPolicy = Field(default_factory=EncoderInputPolicy)
    recipe: TrainingRecipe = Field(default_factory=TrainingRecipe)
    systems: list[SystemTrainingPlan]
    matched_backbone_and_input_policy: Literal[True] = True
    capacity_matching_note: Literal[
        "paper-candidate=3H+9; clinical-control=3H+3; delta=6 scalar assurance parameters"
    ] = "paper-candidate=3H+9; clinical-control=3H+3; delta=6 scalar assurance parameters"
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_system_set(self) -> PaperTrainingContract:
        ids = [system.system_id for system in self.systems]
        if ids != ["gax-paper-candidate", "clinical-encoder"]:
            raise ValueError("training contract must contain paper candidate then clinical control")
        for system in self.systems:
            if system.architecture.frozen_backbone != self.backbone:
                raise ValueError("all systems must use the exact same frozen backbone")
            if system.architecture.encoder_input != self.encoder_input:
                raise ValueError("all systems must use the exact same encoder input policy")
        return self


def canonical_training_contract() -> PaperTrainingContract:
    paper_architecture = ModelArchitectureContract(
        system_id="gax-paper-candidate",
        architecture_id="dal-shadow-assurance-critic-v0.3",
        state_representation="full-state+question-only+evidence-delta",
        action_scoring="nested-clinical-action-head+shadow-typed-evidence-critic",
        output_action_policy="identical-to-same-seed-clinical-control",
        sufficiency_mechanism="logistic-head-over-evidence-delta-norm",
        trainable_parameter_formula="3H+9",
    )
    control_architecture = ModelArchitectureContract(
        system_id="clinical-encoder",
        architecture_id="bioclinical-linear-control-v0.1",
        state_representation="full-state",
        action_scoring="three-class-linear-head-over-frozen-state",
        output_action_policy="selected-linear-head",
        sufficiency_mechanism="none",
        trainable_parameter_formula="3H+3",
    )
    return PaperTrainingContract(
        systems=[
            SystemTrainingPlan(
                system_id="gax-paper-candidate",
                architecture=paper_architecture,
                selection_metric="critic-nll+0.5-sufficiency-brier",
                action_head_training_policy=(
                    "clone-selected-same-seed-control-then-freeze"
                ),
                train_sufficiency_on_present_withheld_pairs=True,
            ),
            SystemTrainingPlan(
                system_id="clinical-encoder",
                architecture=control_architecture,
                selection_metric="action-nll",
                action_head_training_policy="train-on-evidence-present",
                train_sufficiency_on_present_withheld_pairs=False,
            ),
        ]
    )


def training_contract_digest(contract: PaperTrainingContract) -> str:
    return canonical_json_sha256(contract.model_dump(mode="json"))
