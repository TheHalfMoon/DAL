from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from gaxbench.p08_calibration_execution import (
    AuthorizationCandidate,
    CalibrationEvidence,
    EcalDecisionLedger,
    FhirSelectionEvidence,
)
from gaxbench.p08_inventory import audit_real_inventory, load_real_inventory
from gaxbench.p08_system_qualification import (
    load_qualification_bundle,
    qualification_bundle_digest,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

SG000020_CLOSEOUT_SHA = "ebe981db8b2554a2b52037b8d3cdfc48ef42ba78"
SG000021_ACTIVATION_SHA = "f8ac88c34557902d760d49b36227010d4fdc46a9"
PAPER_CHECKPOINT_SHA256 = "351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b"
CALIBRATION_SEMANTIC_SHA256 = "025d92c2d704dfa3889e267be8fac17037d034b5760e635886c536d198c8c8dc"
ECAL_SEMANTIC_SHA256 = "3bfb069bfdd3ee50890f97c3e4744024af14cb9c9a62211cca008eb4c5ef9bb8"
FHIR_SEMANTIC_SHA256 = "79ddfd4336b5b8a8376ff9761d40ae46fe890eef9962bc6205e8622533b85b9a"
FHIR_SELECTED_SEMANTIC_SHA256 = (
    "10665e1fec0be7ec6d2bf6e3710f54b26ded79a16dc48d032a15c8862112963b"
)
AUTHORIZATION_CANDIDATE_SEMANTIC_SHA256 = (
    "3f4000cb5616578332a85d00aeda18e120c2b959d59e32375696cd53486b5484"
)
CALIBRATION_MANIFEST_SHA256 = "89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230"
HARDWARE_PROTOCOL_REVISION = "p08-hardware-stratified-v0.1"
MULTIPLICITY_POLICY = "holm-primary-family-v0.1"
COVERAGE_TARGETS = [0.5, 0.8, 0.9]

REQUIRED_SYSTEM_DIGESTS = {
    "gax-paper-candidate": "0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b",
    "clinical-encoder": "b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388",
    "laya": "b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534",
}

REQUIRED_DATASETS: dict[str, dict[str, Any]] = {
    "pubmedqa-pqal": {
        "source_revision": "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997",
        "data_revision_sha256": "8b3276be8942ebbd77f3ddcda12c1749bf0e490045a736fd8438ee40cf37a41d",
        "split_manifest_sha256": "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723",
        "leakage_audit_sha256": "7a8a576c0485b351190b58a49ac6662e614470b5b414a0d437ca761da3e76443",
        "final_test_count": 500,
    },
    "gax-native-abstention-pqal": {
        "source_revision": "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997",
        "data_revision_sha256": "7ce6787ef0d9c936cf11b39a13e8d73b8e740e1555ec5167ff6badb1a8b8bdc0",
        "split_manifest_sha256": "d64bfdf057afeaae35fb4209a8513dfc48a6c52e2abd08260dbf111afec1474f",
        "leakage_audit_sha256": "e4c105bb1315138310f9b10432430fc753f5d0bfa87d8378dad97399a37cb8d8",
        "final_test_count": 1000,
    },
    "fhir-agentbench": {
        "source_revision": "bbb42909a5a7eb907d1cd91f72a560729e7037ea",
        "data_revision_sha256": "e2045692fef7f5f4f77496935160f5fc727e162d213e94feed61401948e512a0",
        "split_manifest_sha256": "7065cede39bdfea3db33d025687210f30f26683a38063f7150a807cd89f5e76c",
        "leakage_audit_sha256": "1e45851f334cf5ab0522ac96766080566cb7609462d6917d625814a5612c6490",
        "final_test_count": 173,
    },
}

_FAILURE_ACCOUNTING = [
    "requested",
    "completed",
    "timeout",
    "oom",
    "transport",
    "interface",
    "parse",
]


class DatasetAuthorizationBinding(StrictModel):
    id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    data_revision_sha256: str
    split_manifest_sha256: str
    leakage_audit_sha256: str
    final_test_count: int = Field(gt=0)
    license_status: Literal["verified"] = "verified"
    test_labels_sealed_before_authorization: Literal[True] = True


class FinalTestAuthorizationArtifact(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    grain_id: Literal["SG-000021"] = "SG-000021"
    research_issue: Literal[80] = 80
    state: Literal["authorized-for-next-grain"] = "authorized-for-next-grain"
    authorized_grain: Literal["SG-000022"] = "SG-000022"
    sg000020_closeout_sha: str = SG000020_CLOSEOUT_SHA
    sg000021_activation_sha: str = SG000021_ACTIVATION_SHA
    required_system_bundle_digests: dict[str, str]
    paper_checkpoint_sha256: str = PAPER_CHECKPOINT_SHA256
    required_datasets: list[DatasetAuthorizationBinding]
    calibration_manifest_sha256: str = CALIBRATION_MANIFEST_SHA256
    calibration_evidence_semantic_sha256: str = CALIBRATION_SEMANTIC_SHA256
    ecal_selection_semantic_sha256: str = ECAL_SEMANTIC_SHA256
    fhir_selection_semantic_sha256: str = FHIR_SEMANTIC_SHA256
    selected_fhir_representation_semantic_sha256: str = FHIR_SELECTED_SEMANTIC_SHA256
    authorization_candidate_semantic_sha256: str = AUTHORIZATION_CANDIDATE_SEMANTIC_SHA256
    coverage_targets: list[float] = Field(default_factory=lambda: list(COVERAGE_TARGETS))
    hardware_protocol_revision: str = HARDWARE_PROTOCOL_REVISION
    multiplicity_policy: str = MULTIPLICITY_POLICY
    failure_accounting: list[str] = Field(default_factory=lambda: list(_FAILURE_ACCOUNTING))
    no_post_test_tuning: Literal[True] = True
    architecture_reopening_forbidden: Literal[True] = True
    calibration_refit_forbidden: Literal[True] = True
    ecal_reselection_forbidden: Literal[True] = True
    fhir_reselection_forbidden: Literal[True] = True
    final_test_access: Literal["authorized"] = "authorized"
    final_test_inference_executed: Literal[False] = False
    final_test_rows_used: Literal[0] = 0
    zero_founder_cost: Literal[True] = True
    authorization_digest: str

    @model_validator(mode="after")
    def validate_frozen_authorization(self) -> FinalTestAuthorizationArtifact:
        scalar_bindings = {
            "sg000020_closeout_sha": (self.sg000020_closeout_sha, SG000020_CLOSEOUT_SHA),
            "sg000021_activation_sha": (self.sg000021_activation_sha, SG000021_ACTIVATION_SHA),
            "paper_checkpoint_sha256": (self.paper_checkpoint_sha256, PAPER_CHECKPOINT_SHA256),
            "calibration_manifest_sha256": (
                self.calibration_manifest_sha256,
                CALIBRATION_MANIFEST_SHA256,
            ),
            "calibration_evidence_semantic_sha256": (
                self.calibration_evidence_semantic_sha256,
                CALIBRATION_SEMANTIC_SHA256,
            ),
            "ecal_selection_semantic_sha256": (
                self.ecal_selection_semantic_sha256,
                ECAL_SEMANTIC_SHA256,
            ),
            "fhir_selection_semantic_sha256": (
                self.fhir_selection_semantic_sha256,
                FHIR_SEMANTIC_SHA256,
            ),
            "selected_fhir_representation_semantic_sha256": (
                self.selected_fhir_representation_semantic_sha256,
                FHIR_SELECTED_SEMANTIC_SHA256,
            ),
            "authorization_candidate_semantic_sha256": (
                self.authorization_candidate_semantic_sha256,
                AUTHORIZATION_CANDIDATE_SEMANTIC_SHA256,
            ),
            "hardware_protocol_revision": (
                self.hardware_protocol_revision,
                HARDWARE_PROTOCOL_REVISION,
            ),
            "multiplicity_policy": (self.multiplicity_policy, MULTIPLICITY_POLICY),
        }
        for name, (actual, expected) in scalar_bindings.items():
            if actual != expected:
                raise ValueError(f"{name} drift")
        if self.required_system_bundle_digests != REQUIRED_SYSTEM_DIGESTS:
            raise ValueError("required system bundle digest drift")
        if self.coverage_targets != COVERAGE_TARGETS:
            raise ValueError("coverage target drift")
        if self.failure_accounting != _FAILURE_ACCOUNTING:
            raise ValueError("failure-accounting policy drift")
        expected_datasets = [
            DatasetAuthorizationBinding(id=dataset_id, **values)
            for dataset_id, values in REQUIRED_DATASETS.items()
        ]
        if self.required_datasets != expected_datasets:
            raise ValueError("required dataset authorization binding drift")
        _require_sha256(self.authorization_digest, "authorization_digest")
        if self.authorization_digest != authorization_digest(self):
            raise ValueError("authorization digest does not match frozen payload")
        return self


def authorization_digest(artifact: FinalTestAuthorizationArtifact) -> str:
    payload = artifact.model_dump(mode="json")
    payload["authorization_digest"] = None
    return canonical_json_sha256(payload)


def build_final_test_authorization(root: str | Path) -> FinalTestAuthorizationArtifact:
    root_path = Path(root)
    _verify_inventory(root_path)
    _verify_systems(root_path)
    _verify_sg000020_evidence(root_path)
    _verify_dataset_evidence(root_path)

    payload: dict[str, Any] = {
        "required_system_bundle_digests": dict(REQUIRED_SYSTEM_DIGESTS),
        "required_datasets": [
            {"id": dataset_id, **values} for dataset_id, values in REQUIRED_DATASETS.items()
        ],
        "authorization_digest": "0" * 64,
    }
    provisional = FinalTestAuthorizationArtifact.model_construct(**payload)
    payload["authorization_digest"] = authorization_digest(provisional)
    return FinalTestAuthorizationArtifact.model_validate(payload)


def load_final_test_authorization(path: str | Path) -> FinalTestAuthorizationArtifact:
    return FinalTestAuthorizationArtifact.model_validate(_load_json(Path(path)))


def _verify_inventory(root: Path) -> None:
    inventory = load_real_inventory(root / "registry" / "p08_real_inventory.json")
    audit = audit_real_inventory(inventory)
    if not audit.ready_for_authorization or audit.blockers:
        raise ValueError(f"P08 inventory is not authorization-ready: {audit.blockers}")
    if inventory.final_test_access != "sealed":
        raise ValueError("inventory final-test access must still be sealed")
    required_datasets = {
        entry.id: entry for entry in inventory.datasets if entry.required_for_authorization
    }
    if set(required_datasets) != set(REQUIRED_DATASETS):
        raise ValueError("authorization-critical dataset set drift")
    for dataset_id, expected in REQUIRED_DATASETS.items():
        entry = required_datasets[dataset_id]
        if entry.status != "qualified" or entry.license_status != "verified":
            raise ValueError(f"required dataset is not qualified: {dataset_id}")
        if entry.source_revision != expected["source_revision"]:
            raise ValueError(f"source revision drift: {dataset_id}")
        if entry.data_revision != f"sha256:{expected['data_revision_sha256']}":
            raise ValueError(f"data revision drift: {dataset_id}")
        if entry.split_manifest_sha256 != expected["split_manifest_sha256"]:
            raise ValueError(f"split manifest drift: {dataset_id}")
        if entry.leakage_audit_sha256 != expected["leakage_audit_sha256"]:
            raise ValueError(f"leakage audit drift: {dataset_id}")
        if entry.test_labels_sealed is not True:
            raise ValueError(f"test labels are not sealed: {dataset_id}")


def _verify_systems(root: Path) -> None:
    paths = {
        "gax-paper-candidate": "p08_gax_paper_candidate_qualification_bundle_sg000019.json",
        "clinical-encoder": "p08_clinical_encoder_qualification_bundle_sg000019.json",
        "laya": "p08_laya_qualification_bundle_sg000019.json",
    }
    bundles = {
        system_id: load_qualification_bundle(root / "registry" / filename)
        for system_id, filename in paths.items()
    }
    actual = {
        system_id: qualification_bundle_digest(bundle)
        for system_id, bundle in bundles.items()
    }
    if actual != REQUIRED_SYSTEM_DIGESTS:
        raise ValueError("required system qualification bundle digest drift")
    paper = bundles["gax-paper-candidate"]
    seed_zero = [row for row in paper.checkpoints if row.training_seed == 0]
    if len(seed_zero) != 1 or seed_zero[0].checkpoint_sha256 != PAPER_CHECKPOINT_SHA256:
        raise ValueError("frozen paper checkpoint drift")
    if any(bundle.final_test_access != "sealed" for bundle in bundles.values()):
        raise ValueError("required system qualification bundle opened final-test access")


def _verify_sg000020_evidence(root: Path) -> None:
    registry = root / "registry"
    calibration = CalibrationEvidence.model_validate(
        _load_json(registry / "p08_calibration_evidence_sg000020.json")
    )
    ecal = EcalDecisionLedger.model_validate(
        _load_json(registry / "p08_ecal_selection_ledger_sg000020.json")
    )
    fhir = FhirSelectionEvidence.model_validate(
        _load_json(registry / "p08_fhir_selection_ledger_sg000020.json")
    )
    candidate = AuthorizationCandidate.model_validate(
        _load_json(registry / "p08_final_test_authorization_candidate_sg000020.json")
    )
    if canonical_json_sha256(calibration.model_dump(mode="json")) != CALIBRATION_SEMANTIC_SHA256:
        raise ValueError("calibration semantic digest drift")
    if canonical_json_sha256(ecal.model_dump(mode="json")) != ECAL_SEMANTIC_SHA256:
        raise ValueError("ECAL semantic digest drift")
    if canonical_json_sha256(fhir.model_dump(mode="json")) != FHIR_SEMANTIC_SHA256:
        raise ValueError("FHIR semantic digest drift")
    selected = next(
        row for row in fhir.representations if row.representation == fhir.selected_representation
    )
    if canonical_json_sha256(selected.model_dump(mode="json")) != FHIR_SELECTED_SEMANTIC_SHA256:
        raise ValueError("selected FHIR representation semantic digest drift")
    candidate_digest = canonical_json_sha256(candidate.model_dump(mode="json"))
    if candidate_digest != AUTHORIZATION_CANDIDATE_SEMANTIC_SHA256:
        raise ValueError("SG-000020 authorization-candidate semantic digest drift")
    if candidate.final_test_access != "sealed" or candidate.can_authorize_inference is not False:
        raise ValueError("SG-000020 candidate must remain sealed and non-executable")
    execution = _load_json(registry / "p08_sg000020_execution_manifest.json")
    if execution.get("final_test_access") != "sealed" or execution.get("final_test_rows_used") != 0:
        raise ValueError("SG-000020 execution manifest violated the sealed boundary")
    if execution.get("zero_founder_cost") is not True:
        raise ValueError("SG-000020 execution was not zero-founder-cost")


def _verify_dataset_evidence(root: Path) -> None:
    registry = root / "registry"
    bindings = {
        "pubmedqa-pqal": (
            "pubmedqa_pqal_split_manifest.json",
            "pubmedqa_pqal_leakage_audit.json",
            "pubmedqa_pqal_qualification.json",
        ),
        "gax-native-abstention-pqal": (
            "gax_native_abstention_role_manifest.json",
            "gax_native_abstention_leakage_audit.json",
            "gax_native_abstention_qualification.json",
        ),
        "fhir-agentbench": (
            "fhir_agentbench_role_manifest.json",
            "fhir_agentbench_leakage_audit.json",
            "fhir_agentbench_qualification.json",
        ),
    }
    for dataset_id, (split_name, leakage_name, qualification_name) in bindings.items():
        expected = REQUIRED_DATASETS[dataset_id]
        split = _load_json(registry / split_name)
        leakage = _load_json(registry / leakage_name)
        qualification = _load_json(registry / qualification_name)
        if canonical_json_sha256(split) != expected["split_manifest_sha256"]:
            raise ValueError(f"canonical split/role manifest drift: {dataset_id}")
        if canonical_json_sha256(leakage) != expected["leakage_audit_sha256"]:
            raise ValueError(f"canonical leakage audit drift: {dataset_id}")
        if qualification.get("status") != "qualified":
            raise ValueError(f"dataset qualification is not qualified: {dataset_id}")
        if qualification.get("final_test_access") != "sealed":
            raise ValueError(f"dataset qualification opened final-test access: {dataset_id}")
        if dataset_id == "pubmedqa-pqal":
            if qualification.get("test_count") != expected["final_test_count"]:
                raise ValueError("PubMedQA final-test count drift")
            if qualification.get("source_sha256") != expected["data_revision_sha256"]:
                raise ValueError("PubMedQA source digest drift")
        elif dataset_id == "gax-native-abstention-pqal":
            if qualification.get("test_count") != expected["final_test_count"]:
                raise ValueError("native abstention final-test count drift")
            if split.get("membership_sha256") != expected["data_revision_sha256"]:
                raise ValueError("native abstention membership digest drift")
            if qualification.get("test_supervision_serialized") is not False:
                raise ValueError("native abstention test supervision is not sealed")
        else:
            if split.get("test_row_count") != expected["final_test_count"]:
                raise ValueError("FHIR-AgentBench final-test count drift")
            if qualification.get("source_sha256") != expected["data_revision_sha256"]:
                raise ValueError("FHIR-AgentBench source digest drift")
            if qualification.get("qualification_logic_uses_test_supervision") is not False:
                raise ValueError("FHIR-AgentBench qualification used test supervision")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
