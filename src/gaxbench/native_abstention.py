from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from gaxbench.pubmedqa import (
    PUBMEDQA_LICENSE,
    PUBMEDQA_REPOSITORY,
    PUBMEDQA_SOURCE_COMMIT,
    PUBMEDQA_TRANSFORM_REVISION,
)
from gaxbench.schema import BenchmarkItem, Gold, Provenance

NATIVE_ABSTENTION_TRANSFORM_REVISION = "gax-native-abstention-pqal-v0.1"
NativeAbstentionVariant = Literal["evidence-present", "evidence-withheld"]
_ALLOWED_SOURCE_SPLITS = frozenset({"validation", "calibration", "test"})


@dataclass(frozen=True)
class NativeAbstentionPair:
    sufficient: BenchmarkItem
    insufficient: BenchmarkItem


def build_pubmedqa_evidence_pair(item: BenchmarkItem) -> NativeAbstentionPair:
    """Build a deterministic evidence-present/evidence-withheld pair.

    This constructor deliberately keeps abstention outside the candidate-action
    space. Development/calibration supervision uses ``Gold.sufficient`` while
    sealed final-test items remain entirely supervision-free.
    """

    _validate_pubmedqa_item(item)
    supervision = _pair_supervision(item)
    group = f"gax-native-abstention::{item.source_id}"
    provenance = _native_provenance(item.provenance)

    sufficient = BenchmarkItem(
        id=f"{item.id}::evidence-present",
        source_id=item.source_id,
        split=item.split,
        task_family="biomedical-evidence-availability",
        state=item.state,
        actions=list(item.actions),
        gold=supervision[0],
        evidence=list(item.evidence),
        counterfactual_group=group,
        provenance=provenance,
    )
    insufficient = BenchmarkItem(
        id=f"{item.id}::evidence-withheld",
        source_id=item.source_id,
        split=item.split,
        task_family="biomedical-evidence-availability",
        state=item.state,
        actions=list(item.actions),
        gold=supervision[1],
        evidence=[],
        counterfactual_group=group,
        provenance=provenance,
    )
    return NativeAbstentionPair(sufficient=sufficient, insufficient=insufficient)


def _validate_pubmedqa_item(item: BenchmarkItem) -> None:
    provenance = item.provenance
    if provenance.dataset != "PubMedQA PQA-L":
        raise ValueError("native evidence-abstention pairs require PubMedQA PQA-L provenance")
    if provenance.revision != PUBMEDQA_SOURCE_COMMIT:
        raise ValueError("native evidence-abstention pairs require the frozen PubMedQA revision")
    if provenance.license != PUBMEDQA_LICENSE:
        raise ValueError("native evidence-abstention pairs require the qualified PubMedQA license")
    if provenance.transform_revision != PUBMEDQA_TRANSFORM_REVISION:
        raise ValueError(
            "native evidence-abstention pairs require the qualified PubMedQA transform"
        )
    if provenance.source_url != f"https://github.com/{PUBMEDQA_REPOSITORY}":
        raise ValueError("native evidence-abstention pairs require the frozen PubMedQA source URL")
    if item.split not in _ALLOWED_SOURCE_SPLITS:
        raise ValueError("native evidence-abstention pairs reject non-qualified PubMedQA roles")
    if item.task_family != "biomedical-closed-qa":
        raise ValueError("native evidence-abstention pairs require biomedical-closed-qa input")
    if not item.evidence:
        raise ValueError("source item must contain model-visible evidence before withholding")
    if any(action.id == "abstain" for action in item.actions):
        raise ValueError("abstain must remain a policy output, not a candidate action")
    if item.split == "test":
        if item.gold is not None:
            raise ValueError("sealed final-test source items must not contain serialized gold")
        return
    if item.gold is None or item.gold.action is None:
        raise ValueError("development/calibration source items require typed action supervision")


def _pair_supervision(item: BenchmarkItem) -> tuple[Gold | None, Gold | None]:
    if item.split == "test":
        return None, None
    assert item.gold is not None and item.gold.action is not None
    return (
        Gold(action=item.gold.action, sufficient=True),
        Gold(action=None, sufficient=False),
    )


def _native_provenance(source: Provenance) -> Provenance:
    return Provenance(
        dataset="GAX Native Abstention / PubMedQA PQA-L",
        revision=source.revision,
        license=source.license,
        transform_revision=NATIVE_ABSTENTION_TRANSFORM_REVISION,
        source_url=source.source_url,
        access_requirements=(
            "Evidence-withheld variants evaluate authorization under intentionally missing "
            "benchmark evidence; they are not generic clinical-safety labels."
        ),
    )
