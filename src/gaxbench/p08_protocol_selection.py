from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

SG000020_ACTIVATION_REVISION = "851a4ebdd3bf1654cd5259c6a5e4121965b66144"
SG000019_CLOSEOUT_REVISION = "3ca0dd2aae85a68473849108764a45a538de1019"
SG000020_CONTRACT_SHA256 = "6910e2ef834b799d4d05f9b313c2eefcd0d326ee94de8fd3dec8814c03f49471"
CALIBRATION_MANIFEST_SHA256 = "89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230"
PAPER_CHECKPOINT_SHA256 = "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
PAPER_TRAINING_CONTRACT_SHA256 = (
    "0b9b9bef795d1af39f94e45f89913038f68446f90c045e3747573d11c4a9dc2b"
)

ECAL_CANDIDATES = (
    "evidence",
    "hard-negative",
    "proper-scoring",
    "replay-retention",
    "state-action-contrastive",
)
FHIR_CANDIDATES = (
    "canonical-structured",
    "canonical-with-narrative",
    "flat-text",
    "source-order-json",
)
COVERAGE_TARGETS = (0.5, 0.8, 0.9)


class ArchitectureSearchBoundary(StrictModel):
    closed_after: Literal["D03"] = "D03"
    reopen_forbidden: Literal[True] = True
    model_retraining_from_calibration_forbidden: Literal[True] = True
    checkpoint_reselection_from_calibration_forbidden: Literal[True] = True
    prompt_reselection_from_calibration_forbidden: Literal[True] = True


class PaperCheckpointBinding(StrictModel):
    system_id: Literal["gax-paper-candidate"] = "gax-paper-candidate"
    training_seed: Literal[0] = 0
    checkpoint_sha256: str
    training_contract_sha256: str
    reconstruction_policy: Literal[
        "deterministic-rebuild-allowed-only-if-checkpoint-digest-matches"
    ] = "deterministic-rebuild-allowed-only-if-checkpoint-digest-matches"
    digest_mismatch_policy: Literal["fail-closed"] = "fail-closed"

    @model_validator(mode="after")
    def validate_digests(self) -> PaperCheckpointBinding:
        _require_sha256(self.checkpoint_sha256, "checkpoint_sha256")
        _require_sha256(self.training_contract_sha256, "training_contract_sha256")
        if self.checkpoint_sha256 != PAPER_CHECKPOINT_SHA256:
            raise ValueError("paper checkpoint digest drift")
        if self.training_contract_sha256 != PAPER_TRAINING_CONTRACT_SHA256:
            raise ValueError("paper training contract digest drift")
        return self


class CalibrationRoleAssignment(StrictModel):
    dataset_id: Literal[
        "pubmedqa-pqal", "gax-native-abstention-pqal", "fhir-agentbench"
    ]
    count: int = Field(ge=1)
    purpose: Literal[
        "action-temperature-fit",
        "sufficiency-platt-fit",
        "fhir-representation-selection-only",
    ]
    action_space: list[str] | None = None
    pair_policy: str | None = None


class TemperatureOptimizer(StrictModel):
    parameterization: Literal["log-temperature"] = "log-temperature"
    objective: Literal["multiclass-negative-log-likelihood"] = (
        "multiclass-negative-log-likelihood"
    )
    domain: list[float]
    algorithm: Literal["golden-section-search"] = "golden-section-search"
    iterations: Literal[128] = 128
    tie_break: Literal["lower-log-temperature"] = "lower-log-temperature"

    @model_validator(mode="after")
    def validate_domain(self) -> TemperatureOptimizer:
        if self.domain != [-5.0, 5.0]:
            raise ValueError("temperature search domain drift")
        return self


class PlattOptimizer(StrictModel):
    form: Literal["sigmoid(a*raw_logit+b)"] = "sigmoid(a*raw_logit+b)"
    objective: Literal["binary-cross-entropy+l2"] = "binary-cross-entropy+l2"
    l2: float = Field(default=1e-6, ge=1e-6, le=1e-6)
    algorithm: Literal["damped-newton-2d"] = "damped-newton-2d"
    iterations: Literal[100] = 100
    gradient_tolerance: float = Field(default=1e-12, ge=1e-12, le=1e-12)
    damping: float = Field(default=1e-8, ge=1e-8, le=1e-8)
    initial_a: float = Field(default=1.0, ge=1.0, le=1.0)
    initial_b: float = Field(default=0.0, ge=0.0, le=0.0)


class CalibrationContract(StrictModel):
    method: Literal["temperature-scaling-action+platt-sufficiency-v0.1"] = (
        "temperature-scaling-action+platt-sufficiency-v0.1"
    )
    manifest_sha256: str
    coverage_targets: list[float]
    role_assignments: list[CalibrationRoleAssignment]
    action_temperature_optimizer: TemperatureOptimizer
    sufficiency_platt_optimizer: PlattOptimizer
    forbidden: list[str]

    @model_validator(mode="after")
    def validate_contract(self) -> CalibrationContract:
        if self.manifest_sha256 != CALIBRATION_MANIFEST_SHA256:
            raise ValueError("calibration manifest digest drift")
        if self.coverage_targets != list(COVERAGE_TARGETS):
            raise ValueError("coverage targets must remain exactly [0.5, 0.8, 0.9]")
        expected = [
            ("pubmedqa-pqal", 50, "action-temperature-fit"),
            ("gax-native-abstention-pqal", 100, "sufficiency-platt-fit"),
            ("fhir-agentbench", 341, "fhir-representation-selection-only"),
        ]
        actual = [
            (row.dataset_id, row.count, row.purpose) for row in self.role_assignments
        ]
        if actual != expected:
            raise ValueError("calibration role assignment drift")
        if self.role_assignments[0].action_space != ["maybe", "no", "yes"]:
            raise ValueError("PubMedQA action space drift")
        if self.role_assignments[1].pair_policy != (
            "50-evidence-present+50-evidence-withheld"
        ):
            raise ValueError("native abstention calibration pair policy drift")
        required_forbidden = {
            "architecture-selection",
            "checkpoint-selection",
            "seed-selection",
            "backbone-selection",
            "prompt-family-selection",
            "final-test-threshold-selection",
        }
        if set(self.forbidden) != required_forbidden:
            raise ValueError("calibration forbidden-operation set drift")
        return self


class EcalContract(StrictModel):
    candidate_order: list[str]
    selection_scope: Literal[
        "paper-mechanism-reporting-freeze-not-paper-checkpoint-mutation"
    ] = "paper-mechanism-reporting-freeze-not-paper-checkpoint-mutation"
    decision_rule: list[str] = Field(min_length=5)
    tie_break: Literal["candidate_order"] = "candidate_order"
    historical_mapping: dict[str, str]

    @model_validator(mode="after")
    def validate_candidates(self) -> EcalContract:
        if self.candidate_order != list(ECAL_CANDIDATES):
            raise ValueError("ECAL candidate order drift")
        if set(self.historical_mapping) != set(ECAL_CANDIDATES):
            raise ValueError("ECAL historical mapping must cover every candidate")
        return self


class FhirSourceContract(StrictModel):
    fhir_agentbench_repository: Literal["glee4810/FHIR-AgentBench"] = (
        "glee4810/FHIR-AgentBench"
    )
    fhir_agentbench_revision: Literal[
        "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    ] = "bbb42909a5a7eb907d1cd91f72a560729e7037ea"
    fhir_agentbench_calibration_rows: Literal[341] = 341
    mimic_fhir_demo_project: Literal["mimic-iv-fhir-demo"] = "mimic-iv-fhir-demo"
    mimic_fhir_demo_version: Literal["2.1.0"] = "2.1.0"
    mimic_fhir_demo_license: Literal["ODbL-1.0"] = "ODbL-1.0"
    mimic_fhir_demo_access: Literal["open"] = "open"
    mimic_fhir_demo_expected_uncompressed_bytes_class: Literal["49.5-MB-release"] = (
        "49.5-MB-release"
    )
    source_checksum_policy: Literal[
        "record-and-verify-PhysioNet-SHA256SUMS-before-selection"
    ] = "record-and-verify-PhysioNet-SHA256SUMS-before-selection"


class FhirSelectionContract(StrictModel):
    candidate_order: list[str]
    source: FhirSourceContract
    eligibility_rule: list[str] = Field(min_length=7)
    selection_objective: Literal[
        "minimum-median-rendered-bytes-among-eligible-representations"
    ] = "minimum-median-rendered-bytes-among-eligible-representations"
    tie_break: Literal["candidate_order"] = "candidate_order"

    @model_validator(mode="after")
    def validate_candidates(self) -> FhirSelectionContract:
        if self.candidate_order != list(FHIR_CANDIDATES):
            raise ValueError("FHIR candidate order drift")
        return self


class AuthorizationCandidateContract(StrictModel):
    state: Literal["candidate-only"] = "candidate-only"
    must_bind: list[str] = Field(min_length=9)
    final_test_access: Literal["sealed"] = "sealed"
    can_authorize_inference: Literal[False] = False
    separate_authorization_grain_required: Literal[True] = True


class P08ProtocolSelectionContract(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    contract_id: Literal["dal-p08-sg000020-pre-results-v0.1"] = (
        "dal-p08-sg000020-pre-results-v0.1"
    )
    research_issue: Literal[69] = 69
    activation_revision: Literal["851a4ebdd3bf1654cd5259c6a5e4121965b66144"] = (
        "851a4ebdd3bf1654cd5259c6a5e4121965b66144"
    )
    canonical_dependency: Literal[
        "3ca0dd2aae85a68473849108764a45a538de1019"
    ] = "3ca0dd2aae85a68473849108764a45a538de1019"
    final_test_access: Literal["sealed"] = "sealed"
    architecture_search: ArchitectureSearchBoundary
    required_system_bundle_digests: dict[str, str]
    selected_paper_checkpoint: PaperCheckpointBinding
    calibration: CalibrationContract
    ecal: EcalContract
    fhir: FhirSelectionContract
    hardware_protocol_revision: Literal["p08-hardware-stratified-v0.1"] = (
        "p08-hardware-stratified-v0.1"
    )
    multiplicity_policy: Literal["holm-primary-family-v0.1"] = (
        "holm-primary-family-v0.1"
    )
    failure_categories: list[str]
    authorization_candidate: AuthorizationCandidateContract

    @model_validator(mode="after")
    def validate_frozen_bindings(self) -> P08ProtocolSelectionContract:
        expected_systems = {
            "gax-paper-candidate": (
                "0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b"
            ),
            "clinical-encoder": (
                "b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388"
            ),
            "laya": "b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534",
        }
        if self.required_system_bundle_digests != expected_systems:
            raise ValueError("required-system bundle digest drift")
        for name, digest in self.required_system_bundle_digests.items():
            _require_sha256(digest, f"required_system_bundle_digests[{name}]")
        expected_failures = [
            "timeout",
            "oom",
            "transport",
            "interface",
            "parse",
            "missing-resource",
            "other",
        ]
        if self.failure_categories != expected_failures:
            raise ValueError("failure category order drift")
        return self


def protocol_selection_contract_digest(contract: P08ProtocolSelectionContract) -> str:
    return canonical_json_sha256(contract.model_dump(mode="json"))


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
