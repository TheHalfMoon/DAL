from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.p08_real_systems import (
    PUBMEDQA_PARENT_ROLE_MANIFEST_SHA256,
    DevelopmentTrainingManifest,
)
from gaxbench.provenance import canonical_json_sha256
from gaxbench.pubmedqa import (
    ExactCrossSplitFinding,
    PubMedQANearDuplicateFinding,
    PubMedQARecord,
    PubMedQASplitManifest,
    RecordEntry,
    audit_pubmedqa_items,
    convert_record,
    leakage_audit_ok,
)
from gaxbench.schema import BenchmarkItem, StrictModel


class DevelopmentLeakageAudit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    transform_revision: Literal["dal-p08-nested-dev-v0.1"] = "dal-p08-nested-dev-v0.1"
    parent_role_manifest_sha256: Literal[
        "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    ] = "7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723"
    train_count: Literal[360] = 360
    selection_count: Literal[90] = 90
    exact_duplicate_item_ids: list[str]
    exact_cross_role_source_ids: list[ExactCrossSplitFinding]
    exact_cross_role_input_fingerprints: list[ExactCrossSplitFinding]
    exact_cross_role_counterfactual_groups: list[ExactCrossSplitFinding]
    near_duplicate_normalization: Literal["lowercase-unicode-word-tokens"] = (
        "lowercase-unicode-word-tokens"
    )
    near_duplicate_shingle_size: Literal[5] = 5
    near_duplicate_jaccard_threshold: float = Field(default=0.8, ge=0.8, le=0.8)
    cross_role_near_duplicates: list[PubMedQANearDuplicateFinding]
    clean: bool
    final_test_access: Literal["sealed"] = "sealed"
    calibration_rows_included: Literal[False] = False
    final_test_rows_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_clean_flag(self) -> DevelopmentLeakageAudit:
        if self.parent_role_manifest_sha256 != PUBMEDQA_PARENT_ROLE_MANIFEST_SHA256:
            raise ValueError("parent role manifest digest drift")
        has_findings = bool(
            self.exact_duplicate_item_ids
            or self.exact_cross_role_source_ids
            or self.exact_cross_role_input_fingerprints
            or self.exact_cross_role_counterfactual_groups
            or self.cross_role_near_duplicates
        )
        if self.clean == has_findings:
            raise ValueError("clean must be true exactly when all leakage finding lists are empty")
        return self


def audit_development_training_split(
    records: Sequence[RecordEntry],
    parent: PubMedQASplitManifest,
    manifest: DevelopmentTrainingManifest,
) -> DevelopmentLeakageAudit:
    parent_digest = canonical_json_sha256(parent.model_dump(mode="json"))
    if parent_digest != manifest.parent_role_manifest_sha256:
        raise ValueError("development manifest parent digest does not match the supplied parent")

    by_pmid: dict[str, PubMedQARecord] = dict(records)
    if len(by_pmid) != len(records):
        raise ValueError("PubMedQA source records contain duplicate PMIDs")

    child_ids = set(manifest.train_ids) | set(manifest.selection_ids)
    if child_ids != set(parent.validation_ids):
        raise ValueError("child manifest must cover exactly the parent development role")
    forbidden = set(parent.calibration_ids) | set(parent.test_ids)
    if child_ids & forbidden:
        raise ValueError("child manifest overlaps calibration or final-test membership")

    items: list[BenchmarkItem] = []
    for split, ids in (("train", manifest.train_ids), ("validation", manifest.selection_ids)):
        for pmid in ids:
            try:
                record = by_pmid[pmid]
            except KeyError as exc:
                raise ValueError(f"source is missing nested development PMID {pmid!r}") from exc
            base = convert_record(pmid, record, split="validation", include_gold=True)
            payload = base.model_dump(mode="json")
            payload["split"] = split
            items.append(BenchmarkItem.model_validate(payload))

    audit = audit_pubmedqa_items(items)
    return DevelopmentLeakageAudit(
        exact_duplicate_item_ids=list(audit.exact_duplicate_item_ids),
        exact_cross_role_source_ids=list(audit.exact_cross_split_source_ids),
        exact_cross_role_input_fingerprints=list(audit.exact_cross_split_input_fingerprints),
        exact_cross_role_counterfactual_groups=list(audit.exact_cross_split_counterfactual_groups),
        cross_role_near_duplicates=list(audit.cross_split_near_duplicates),
        clean=leakage_audit_ok(audit),
    )


def development_leakage_audit_digest(audit: DevelopmentLeakageAudit) -> str:
    return canonical_json_sha256(audit.model_dump(mode="json"))
