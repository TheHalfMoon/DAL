from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from gaxbench.schema import BenchmarkItem, Gold, Provenance

NATIVE_ABSTENTION_TRANSFORM_REVISION = "gax-native-abstention-pqal-v0.1"
NativeAbstentionVariant = Literal["evidence-present", "evidence-withheld"]


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

    common = {
        "source_id": item.source_id,
        "split": item.split,
        "state": item.state,
        "actions": list(item.actions),
        "counterfactual_group": group,
        "provenance": _native_provenance(item.provenance),
    }
    sufficient = BenchmarkItem(
        id=f"{item.id}::evidence-present",
        task_family="biomedical-evidence-availability",
        gold=supervision[0],
        evidence=list(item.evidence),
        **common,
    )
    insufficient = BenchmarkItem(
        id=f"{item.id}::evidence-withheld",
        task_family="biomedical-evidence-availability",
        gold=supervision[1],
        evidence=[],
        **common,
    )
    return NativeAbstentionPair(sufficient=sufficient, insufficient=insufficient)


def _validate_pubmedqa_item(item: BenchmarkItem) -> None:
    if item.provenance.dataset != "PubMedQA PQA-L":
        raise ValueError("native evidence-abstention pairs require PubMedQA PQA-L provenance")
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
