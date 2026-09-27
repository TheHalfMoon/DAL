from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from gaxbench.fhir_agentbench_qualification import (
    FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD,
    FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
    GAXRole,
    _assign_patient_roles,
    _fingerprint_text,
    _read_source,
    _text_shingles,
)
from gaxbench.schema import StrictModel


class FHIRAgentBenchNearDuplicateClassification(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["fhir-agentbench"] = "fhir-agentbench"
    role_revision: Literal["gax-fhir-agentbench-patient-disjoint-v0.1"] = (
        "gax-fhir-agentbench-patient-disjoint-v0.1"
    )
    jaccard_threshold: float = Field(default=0.8, ge=0.8, le=0.8)
    total_cross_role_near_duplicate_pairs: int = Field(ge=0)
    same_template_near_duplicate_pairs: int = Field(ge=0)
    cross_template_near_duplicate_pairs: int = Field(ge=0)
    classification: Literal["benchmark-native-template-only", "requires-review", "none"]
    raw_questions_serialized: Literal[False] = False
    raw_templates_serialized: Literal[False] = False
    raw_patient_identifiers_serialized: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"


def classify_frozen_near_duplicates(
    path: str | Path,
    *,
    expected_blob_sha1: str = FHIR_AGENTBENCH_SOURCE_BLOB_SHA1,
) -> FHIRAgentBenchNearDuplicateClassification:
    _, _, rows, _ = _read_source(Path(path), expected_blob_sha1=expected_blob_sha1)
    patient_digests = sorted({row.patient_digest for row in rows})
    roles_by_patient = _assign_patient_roles(patient_digests)
    prepared: list[tuple[GAXRole, str, frozenset[tuple[str, ...]]]] = []
    for row in rows:
        prepared.append(
            (
                roles_by_patient[row.patient_digest],
                _fingerprint_text(row.template),
                _text_shingles(row.question),
            )
        )

    total = 0
    same_template = 0
    cross_template = 0
    for left_index, (left_role, left_template, left_shingles) in enumerate(prepared):
        for right_role, right_template, right_shingles in prepared[left_index + 1 :]:
            if left_role == right_role:
                continue
            maximum = max(len(left_shingles), len(right_shingles))
            minimum = min(len(left_shingles), len(right_shingles))
            if maximum == 0 or minimum / maximum < FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD:
                continue
            intersection = len(left_shingles & right_shingles)
            union_size = len(left_shingles) + len(right_shingles) - intersection
            if union_size == 0:
                continue
            score = intersection / union_size
            if score < FHIR_AGENTBENCH_NEAR_DUPLICATE_THRESHOLD:
                continue
            total += 1
            if left_template == right_template:
                same_template += 1
            else:
                cross_template += 1

    if total == 0:
        classification: Literal[
            "benchmark-native-template-only", "requires-review", "none"
        ] = "none"
    elif cross_template == 0:
        classification = "benchmark-native-template-only"
    else:
        classification = "requires-review"

    return FHIRAgentBenchNearDuplicateClassification(
        total_cross_role_near_duplicate_pairs=total,
        same_template_near_duplicate_pairs=same_template,
        cross_template_near_duplicate_pairs=cross_template,
        classification=classification,
    )
