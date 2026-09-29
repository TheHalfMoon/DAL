from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from gaxbench.native_abstention import NATIVE_ABSTENTION_TRANSFORM_REVISION
from gaxbench.provenance import canonical_json_sha256
from gaxbench.pubmedqa import PubMedQALeakageAudit, PubMedQASplitManifest
from gaxbench.schema import StrictModel

PARENT_SPLIT_MANIFEST_SHA256 = "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
PARENT_LEAKAGE_AUDIT_SHA256 = "7a8a576c0485b351190b58a49ac6662e614470b5b414a0d437ca761da3e76443"


class RoleCount(StrictModel):
    source_count: int = Field(ge=0)
    pair_count: int = Field(ge=0)


class NativeAbstentionRoleManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["gax-native-abstention-pqal"] = "gax-native-abstention-pqal"
    parent_dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    parent_split_manifest_sha256: str
    transform_revision: Literal["gax-native-abstention-pqal-v0.1"] = (
        "gax-native-abstention-pqal-v0.1"
    )
    variants: list[Literal["evidence-present", "evidence-withheld"]]
    roles: dict[Literal["validation", "calibration", "test"], RoleCount]
    membership_sha256: str
    final_test_access: Literal["sealed"] = "sealed"
    test_supervision_serialized: Literal[False] = False
    task_scope: str


class NativeAbstentionLeakageAudit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["gax-native-abstention-pqal"] = "gax-native-abstention-pqal"
    transform_revision: Literal["gax-native-abstention-pqal-v0.1"] = (
        "gax-native-abstention-pqal-v0.1"
    )
    parent_leakage_audit_sha256: str
    parent_cross_role_exact_overlap_count: Literal[0] = 0
    parent_cross_role_near_duplicate_count: Literal[0] = 0
    intentional_within_source_pair_count: Literal[1000] = 1000
    cross_role_pair_overlap_count: Literal[0] = 0
    abstain_candidate_action_count: Literal[0] = 0
    test_supervision_serialized: Literal[False] = False
    public_pretraining_contamination_risk: Literal["unresolved-public-benchmark"] = (
        "unresolved-public-benchmark"
    )
    final_test_access: Literal["sealed"] = "sealed"


class NativeAbstentionQualification(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["gax-native-abstention-pqal"] = "gax-native-abstention-pqal"
    source_repository: Literal["pubmedqa/pubmedqa"] = "pubmedqa/pubmedqa"
    source_revision: Literal["1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"] = (
        "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"
    )
    license: Literal["MIT"] = "MIT"
    transform_revision: Literal["gax-native-abstention-pqal-v0.1"] = (
        "gax-native-abstention-pqal-v0.1"
    )
    source_item_count: Literal[1000] = 1000
    derived_item_count: Literal[2000] = 2000
    validation_count: Literal[900] = 900
    calibration_count: Literal[100] = 100
    test_count: Literal[1000] = 1000
    role_manifest_sha256: str
    leakage_audit_sha256: str
    status: Literal["qualified"] = "qualified"
    final_test_access: Literal["sealed"] = "sealed"
    test_supervision_serialized: Literal[False] = False
    scope_limitation: str


def qualify_native_abstention(
    parent_split_path: str | Path,
    parent_leakage_path: str | Path,
) -> tuple[
    NativeAbstentionRoleManifest,
    NativeAbstentionLeakageAudit,
    NativeAbstentionQualification,
]:
    parent_split = PubMedQASplitManifest.model_validate(
        json.loads(Path(parent_split_path).read_text(encoding="utf-8"))
    )
    parent_leakage = PubMedQALeakageAudit.model_validate(
        json.loads(Path(parent_leakage_path).read_text(encoding="utf-8"))
    )
    parent_split_sha = canonical_json_sha256(parent_split.model_dump(mode="json"))
    parent_leakage_sha = canonical_json_sha256(parent_leakage.model_dump(mode="json"))
    if parent_split_sha != PARENT_SPLIT_MANIFEST_SHA256:
        raise ValueError("parent PubMedQA split manifest digest is not canonical")
    if parent_leakage_sha != PARENT_LEAKAGE_AUDIT_SHA256:
        raise ValueError("parent PubMedQA leakage audit digest is not canonical")
    if (
        parent_leakage.exact_duplicate_item_ids
        or parent_leakage.exact_cross_split_source_ids
        or parent_leakage.exact_cross_split_input_fingerprints
        or parent_leakage.exact_cross_split_counterfactual_groups
        or parent_leakage.cross_split_near_duplicates
    ):
        raise ValueError("parent PubMedQA leakage audit is not clean")

    roles = {
        "calibration": RoleCount(
            source_count=len(parent_split.calibration_ids),
            pair_count=2 * len(parent_split.calibration_ids),
        ),
        "test": RoleCount(
            source_count=len(parent_split.test_ids),
            pair_count=2 * len(parent_split.test_ids),
        ),
        "validation": RoleCount(
            source_count=len(parent_split.validation_ids),
            pair_count=2 * len(parent_split.validation_ids),
        ),
    }
    membership_sha = canonical_json_sha256(
        {
            "parent_split_manifest_sha256": parent_split_sha,
            "transform_revision": NATIVE_ABSTENTION_TRANSFORM_REVISION,
            "variants": ["evidence-present", "evidence-withheld"],
        }
    )
    role_manifest = NativeAbstentionRoleManifest(
        parent_split_manifest_sha256=parent_split_sha,
        variants=["evidence-present", "evidence-withheld"],
        roles=roles,
        membership_sha256=membership_sha,
        task_scope=(
            "evidence-availability insufficiency/selective-decision evaluation; "
            "not generic clinical safety"
        ),
    )
    leakage = NativeAbstentionLeakageAudit(
        parent_leakage_audit_sha256=parent_leakage_sha,
    )
    qualification = NativeAbstentionQualification(
        role_manifest_sha256=canonical_json_sha256(role_manifest.model_dump(mode="json")),
        leakage_audit_sha256=canonical_json_sha256(leakage.model_dump(mode="json")),
        scope_limitation=(
            "Evidence-withheld variants test authorization under intentionally missing "
            "benchmark evidence; they do not establish generic clinical insufficiency "
            "or clinical safety."
        ),
    )
    return role_manifest, leakage, qualification
