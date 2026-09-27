from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from gaxbench.audit import CrossSplitFinding, audit_split_integrity
from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import Action, BenchmarkItem, Evidence, Gold, Provenance, StrictModel

PUBMEDQA_REPOSITORY = "pubmedqa/pubmedqa"
PUBMEDQA_SOURCE_COMMIT = "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"
PUBMEDQA_SOURCE_PATH = "data/ori_pqal.json"
PUBMEDQA_SOURCE_BLOB_SHA1 = "38db7750761c78950ed32303e7545bdaa513390c"
PUBMEDQA_LICENSE = "MIT"
PUBMEDQA_TRANSFORM_REVISION = "gax-pqal-v0.1"
PUBMEDQA_EXPECTED_RECORDS = 1000
PUBMEDQA_SPLIT_SEED = 0
PUBMEDQA_NEAR_DUPLICATE_SHINGLES = 5
PUBMEDQA_NEAR_DUPLICATE_THRESHOLD = 0.80
PUBMEDQA_RAW_URL = (
    "https://raw.githubusercontent.com/"
    f"{PUBMEDQA_REPOSITORY}/{PUBMEDQA_SOURCE_COMMIT}/{PUBMEDQA_SOURCE_PATH}"
)

Decision = Literal["maybe", "no", "yes"]
RecordEntry = tuple[str, "PubMedQARecord"]

_ACTIONS = (
    Action(id="maybe", description="The biomedical research question is answered maybe."),
    Action(id="no", description="The biomedical research question is answered no."),
    Action(id="yes", description="The biomedical research question is answered yes."),
)


class PubMedQARecord(StrictModel):
    QUESTION: str = Field(min_length=1)
    CONTEXTS: list[str] = Field(min_length=1)
    LABELS: list[str] = Field(default_factory=list)
    MESHES: list[str] = Field(default_factory=list)
    YEAR: str | None = None
    reasoning_required_pred: str | None = None
    reasoning_free_pred: str | None = None
    final_decision: Decision
    LONG_ANSWER: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contexts(self) -> PubMedQARecord:
        if any(not context.strip() for context in self.CONTEXTS):
            raise ValueError("CONTEXTS must contain non-empty strings")
        return self


class PubMedQASplitManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    source_repository: Literal["pubmedqa/pubmedqa"] = PUBMEDQA_REPOSITORY
    source_commit: Literal["1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"] = (
        PUBMEDQA_SOURCE_COMMIT
    )
    source_blob_sha1: Literal["38db7750761c78950ed32303e7545bdaa513390c"] = (
        PUBMEDQA_SOURCE_BLOB_SHA1
    )
    transform_revision: Literal["gax-pqal-v0.1"] = PUBMEDQA_TRANSFORM_REVISION
    upstream_seed: Literal[0] = PUBMEDQA_SPLIT_SEED
    training_ids: list[str] = Field(default_factory=list)
    validation_ids: list[str]
    calibration_ids: list[str]
    test_ids: list[str]
    final_test_access: Literal["sealed"] = "sealed"
    test_labels_serialized: Literal[False] = False

    @model_validator(mode="after")
    def validate_membership(self) -> PubMedQASplitManifest:
        if self.training_ids:
            raise ValueError("PQA-L training_ids must remain empty under SG-000014")
        role_ids = {
            "validation": self.validation_ids,
            "calibration": self.calibration_ids,
            "test": self.test_ids,
        }
        for role, ids in role_ids.items():
            if ids != sorted(set(ids)):
                raise ValueError(f"{role}_ids must be unique and sorted")
        memberships: dict[str, str] = {}
        for role, ids in role_ids.items():
            for item_id in ids:
                prior = memberships.setdefault(item_id, role)
                if prior != role:
                    raise ValueError(f"PMID {item_id!r} appears in multiple roles")
        if len(memberships) != PUBMEDQA_EXPECTED_RECORDS:
            raise ValueError(
                f"split manifest must contain {PUBMEDQA_EXPECTED_RECORDS} unique PMIDs"
            )
        if len(self.test_ids) != 500:
            raise ValueError("official PQA-L outer test role must contain 500 items")
        if len(self.calibration_ids) != 50:
            raise ValueError("PQA-L calibration role must contain upstream CV fold 0 (50 items)")
        if len(self.validation_ids) != 450:
            raise ValueError("PQA-L validation role must contain upstream CV folds 1-9 (450 items)")
        return self


class ExactCrossSplitFinding(StrictModel):
    key: str
    splits: list[str]
    item_ids: list[str]


class PubMedQANearDuplicateFinding(StrictModel):
    left_id: str
    left_split: str
    right_id: str
    right_split: str
    jaccard: float = Field(ge=PUBMEDQA_NEAR_DUPLICATE_THRESHOLD, le=1.0)


class PubMedQALeakageAudit(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    transform_revision: Literal["gax-pqal-v0.1"] = PUBMEDQA_TRANSFORM_REVISION
    exact_duplicate_item_ids: list[str]
    exact_cross_split_source_ids: list[ExactCrossSplitFinding]
    exact_cross_split_input_fingerprints: list[ExactCrossSplitFinding]
    exact_cross_split_counterfactual_groups: list[ExactCrossSplitFinding]
    near_duplicate_normalization: Literal["lowercase-unicode-word-tokens"] = (
        "lowercase-unicode-word-tokens"
    )
    near_duplicate_shingle_size: Literal[5] = PUBMEDQA_NEAR_DUPLICATE_SHINGLES
    near_duplicate_jaccard_threshold: Literal[0.8] = PUBMEDQA_NEAR_DUPLICATE_THRESHOLD
    cross_split_near_duplicates: list[PubMedQANearDuplicateFinding]
    public_pretraining_contamination_risk: Literal["unresolved-public-benchmark"] = (
        "unresolved-public-benchmark"
    )
    final_test_access: Literal["sealed"] = "sealed"
    test_tuning_forbidden: Literal[True] = True


class PubMedQAQualificationReport(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["pubmedqa-pqal"] = "pubmedqa-pqal"
    source_commit: Literal["1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"] = (
        PUBMEDQA_SOURCE_COMMIT
    )
    source_blob_sha1: Literal["38db7750761c78950ed32303e7545bdaa513390c"] = (
        PUBMEDQA_SOURCE_BLOB_SHA1
    )
    source_sha256: str
    record_count: Literal[1000] = PUBMEDQA_EXPECTED_RECORDS
    validation_count: Literal[450] = 450
    calibration_count: Literal[50] = 50
    test_count: Literal[500] = 500
    split_manifest_sha256: str
    leakage_audit_sha256: str
    status: Literal["qualified", "blocked"]
    final_test_access: Literal["sealed"] = "sealed"
    public_pretraining_contamination_risk: Literal["unresolved-public-benchmark"] = (
        "unresolved-public-benchmark"
    )

    @model_validator(mode="after")
    def validate_hashes(self) -> PubMedQAQualificationReport:
        for name, value in (
            ("source_sha256", self.source_sha256),
            ("split_manifest_sha256", self.split_manifest_sha256),
            ("leakage_audit_sha256", self.leakage_audit_sha256),
        ):
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        return self


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_frozen_source(data: bytes, *, expected_blob_sha1: str = PUBMEDQA_SOURCE_BLOB_SHA1) -> None:
    actual = git_blob_sha1(data)
    if actual != expected_blob_sha1:
        raise ValueError(
            "PubMedQA source Git blob mismatch: "
            f"expected {expected_blob_sha1}, got {actual}"
        )


def load_frozen_pqal(
    path: str | Path,
    *,
    expected_blob_sha1: str = PUBMEDQA_SOURCE_BLOB_SHA1,
    expected_records: int = PUBMEDQA_EXPECTED_RECORDS,
) -> list[RecordEntry]:
    raw = Path(path).read_bytes()
    verify_frozen_source(raw, expected_blob_sha1=expected_blob_sha1)
    payload: object = json.loads(raw, object_pairs_hook=_object_pairs_without_duplicates)
    if not isinstance(payload, dict):
        raise ValueError("PQA-L source must be one JSON object keyed by PMID")
    if len(payload) != expected_records:
        raise ValueError(f"expected {expected_records} PQA-L records, got {len(payload)}")

    records: list[RecordEntry] = []
    for raw_pmid, raw_record in payload.items():
        if not isinstance(raw_pmid, str) or not raw_pmid:
            raise ValueError("PQA-L PMID keys must be non-empty strings")
        records.append((raw_pmid, PubMedQARecord.model_validate(raw_record)))
    return records


def build_split_manifest(records: Sequence[RecordEntry]) -> PubMedQASplitManifest:
    if len(records) != PUBMEDQA_EXPECTED_RECORDS:
        raise ValueError(f"expected {PUBMEDQA_EXPECTED_RECORDS} records")
    rng = random.Random(PUBMEDQA_SPLIT_SEED)
    outer = _upstream_label_stratified_split(records, 2, rng)
    cv_records, test_records = outer[0], outer[1]
    cv_folds = _upstream_label_stratified_split(cv_records, 10, rng)
    calibration_records = cv_folds[0]
    validation_records = [member for fold in cv_folds[1:] for member in fold]

    return PubMedQASplitManifest(
        validation_ids=sorted(pmid for pmid, _ in validation_records),
        calibration_ids=sorted(pmid for pmid, _ in calibration_records),
        test_ids=sorted(pmid for pmid, _ in test_records),
    )


def convert_record(
    pmid: str,
    record: PubMedQARecord,
    *,
    split: Literal["validation", "calibration", "test"],
    include_gold: bool,
) -> BenchmarkItem:
    if split == "test" and include_gold:
        raise ValueError("SG-000014 forbids serializing final-test gold labels")

    evidence: list[Evidence] = []
    for index, context in enumerate(record.CONTEXTS):
        section = record.LABELS[index] if index < len(record.LABELS) else None
        structured = {"section": section} if section else None
        evidence.append(
            Evidence(
                id=f"abstract-section-{index:03d}",
                relation="unknown",
                text=context,
                structured=structured,
            )
        )

    gold = Gold(action=record.final_decision) if include_gold else None
    return BenchmarkItem(
        id=f"pubmedqa-pqal-{pmid}",
        source_id=pmid,
        split=split,
        task_family="biomedical-closed-qa",
        state={"question": record.QUESTION},
        actions=list(_ACTIONS),
        gold=gold,
        evidence=evidence,
        provenance=Provenance(
            dataset="PubMedQA PQA-L",
            revision=PUBMEDQA_SOURCE_COMMIT,
            license=PUBMEDQA_LICENSE,
            transform_revision=PUBMEDQA_TRANSFORM_REVISION,
            source_url=f"https://github.com/{PUBMEDQA_REPOSITORY}",
        ),
    )


def build_qualification_items(
    records: Sequence[RecordEntry],
    manifest: PubMedQASplitManifest,
) -> list[BenchmarkItem]:
    by_pmid = dict(records)
    items: list[BenchmarkItem] = []
    for split, ids in (
        ("validation", manifest.validation_ids),
        ("calibration", manifest.calibration_ids),
        ("test", manifest.test_ids),
    ):
        for pmid in ids:
            record = by_pmid[pmid]
            items.append(
                convert_record(
                    pmid,
                    record,
                    split=split,
                    include_gold=split != "test",
                )
            )
    return items


def audit_pubmedqa_items(items: Sequence[BenchmarkItem]) -> PubMedQALeakageAudit:
    exact = audit_split_integrity(items)
    return PubMedQALeakageAudit(
        exact_duplicate_item_ids=list(exact.duplicate_item_ids),
        exact_cross_split_source_ids=_convert_exact_findings(exact.cross_split_source_ids),
        exact_cross_split_input_fingerprints=_convert_exact_findings(
            exact.cross_split_input_fingerprints
        ),
        exact_cross_split_counterfactual_groups=_convert_exact_findings(
            exact.cross_split_counterfactual_groups
        ),
        cross_split_near_duplicates=_near_duplicate_findings(items),
    )


def leakage_audit_ok(audit: PubMedQALeakageAudit) -> bool:
    return not (
        audit.exact_duplicate_item_ids
        or audit.exact_cross_split_source_ids
        or audit.exact_cross_split_input_fingerprints
        or audit.exact_cross_split_counterfactual_groups
        or audit.cross_split_near_duplicates
    )


def qualify_pubmedqa_source(
    path: str | Path,
    *,
    expected_blob_sha1: str = PUBMEDQA_SOURCE_BLOB_SHA1,
    expected_records: int = PUBMEDQA_EXPECTED_RECORDS,
) -> tuple[PubMedQASplitManifest, PubMedQALeakageAudit, PubMedQAQualificationReport]:
    source_path = Path(path)
    source_bytes = source_path.read_bytes()
    records = load_frozen_pqal(
        source_path,
        expected_blob_sha1=expected_blob_sha1,
        expected_records=expected_records,
    )
    manifest = build_split_manifest(records)
    items = build_qualification_items(records, manifest)
    audit = audit_pubmedqa_items(items)
    report = PubMedQAQualificationReport(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        split_manifest_sha256=canonical_json_sha256(manifest.model_dump(mode="json")),
        leakage_audit_sha256=canonical_json_sha256(audit.model_dump(mode="json")),
        status="qualified" if leakage_audit_ok(audit) else "blocked",
    )
    return manifest, audit, report


def _upstream_label_stratified_split(
    records: Sequence[RecordEntry],
    fold_count: int,
    rng: random.Random,
) -> list[list[RecordEntry]]:
    if fold_count < 2:
        raise ValueError("fold_count must be at least 2")
    groups: dict[Decision, list[RecordEntry]] = {"yes": [], "no": [], "maybe": []}
    for member in records:
        groups[member[1].final_decision].append(member)

    split_groups: dict[Decision, list[list[RecordEntry]]] = {}
    for decision in ("yes", "no", "maybe"):
        members = list(groups[decision])
        rng.shuffle(members)
        per_fold = math.ceil(len(members) / fold_count)
        decision_folds: list[list[RecordEntry]] = []
        for index in range(fold_count):
            if index == fold_count - 1:
                decision_folds.append(members[index * per_fold :])
            else:
                decision_folds.append(members[index * per_fold : (index + 1) * per_fold])
        split_groups[decision] = decision_folds

    output: list[list[RecordEntry]] = []
    for index in range(fold_count):
        fold: list[RecordEntry] = []
        for decision in ("yes", "no", "maybe"):
            fold.extend(split_groups[decision][index])
        output.append(fold)

    if len(output[-1]) != len(output[0]):
        for index in range(fold_count - 1):
            if not output[index]:
                raise ValueError("cannot rebalance an empty upstream split")
            chosen_index = rng.randrange(len(output[index]))
            output[-1].append(output[index].pop(chosen_index))
    return output


def _near_duplicate_findings(
    items: Sequence[BenchmarkItem],
) -> list[PubMedQANearDuplicateFinding]:
    prepared = [
        (item.id, item.split, _text_shingles(_model_visible_text(item)))
        for item in sorted(items, key=lambda candidate: candidate.id)
    ]
    findings: list[PubMedQANearDuplicateFinding] = []
    for left_index, (left_id, left_split, left_shingles) in enumerate(prepared):
        for right_id, right_split, right_shingles in prepared[left_index + 1 :]:
            if left_split == right_split:
                continue
            maximum = max(len(left_shingles), len(right_shingles))
            minimum = min(len(left_shingles), len(right_shingles))
            if maximum == 0 or minimum / maximum < PUBMEDQA_NEAR_DUPLICATE_THRESHOLD:
                continue
            union = left_shingles | right_shingles
            if not union:
                continue
            score = len(left_shingles & right_shingles) / len(union)
            if score >= PUBMEDQA_NEAR_DUPLICATE_THRESHOLD:
                findings.append(
                    PubMedQANearDuplicateFinding(
                        left_id=left_id,
                        left_split=left_split,
                        right_id=right_id,
                        right_split=right_split,
                        jaccard=round(score, 12),
                    )
                )
    return findings


def _model_visible_text(item: BenchmarkItem) -> str:
    state = item.state
    question = ""
    if isinstance(state, dict):
        raw_question = state.get("question")
        if isinstance(raw_question, str):
            question = raw_question
    evidence_text = " ".join(
        evidence.text for evidence in item.evidence if evidence.text is not None
    )
    return f"{question} {evidence_text}".strip()


def _text_shingles(text: str) -> frozenset[tuple[str, ...]]:
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    if not tokens:
        return frozenset()
    size = PUBMEDQA_NEAR_DUPLICATE_SHINGLES
    if len(tokens) < size:
        return frozenset({tuple(tokens)})
    return frozenset(tuple(tokens[index : index + size]) for index in range(len(tokens) - size + 1))


def _convert_exact_findings(
    findings: Sequence[CrossSplitFinding],
) -> list[ExactCrossSplitFinding]:
    return [
        ExactCrossSplitFinding(
            key=finding.key,
            splits=list(finding.splits),
            item_ids=list(finding.item_ids),
        )
        for finding in findings
    ]


def _object_pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result
