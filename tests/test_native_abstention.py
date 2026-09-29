from __future__ import annotations

import pytest

from gaxbench.native_abstention import (
    NATIVE_ABSTENTION_TRANSFORM_REVISION,
    build_pubmedqa_evidence_pair,
)
from gaxbench.pubmedqa import (
    PUBMEDQA_LICENSE,
    PUBMEDQA_REPOSITORY,
    PUBMEDQA_SOURCE_COMMIT,
    PUBMEDQA_TRANSFORM_REVISION,
)
from gaxbench.schema import Action, BenchmarkItem, Evidence, Gold, Provenance


def make_item(*, split: str = "validation", gold: bool = True) -> BenchmarkItem:
    return BenchmarkItem(
        id="pubmedqa-pqal-123",
        source_id="123",
        split=split,  # type: ignore[arg-type]
        task_family="biomedical-closed-qa",
        state={"question": "Does the supplied study evidence support the conclusion?"},
        actions=[
            Action(id="maybe", description="maybe"),
            Action(id="no", description="no"),
            Action(id="yes", description="yes"),
        ],
        gold=Gold(action="yes") if gold else None,
        evidence=[Evidence(id="abstract-section-000", text="Study evidence.")],
        provenance=Provenance(
            dataset="PubMedQA PQA-L",
            revision=PUBMEDQA_SOURCE_COMMIT,
            license=PUBMEDQA_LICENSE,
            transform_revision=PUBMEDQA_TRANSFORM_REVISION,
            source_url=f"https://github.com/{PUBMEDQA_REPOSITORY}",
        ),
    )


def test_pair_keeps_abstention_outside_action_space() -> None:
    pair = build_pubmedqa_evidence_pair(make_item())
    expected_actions = {"maybe", "no", "yes"}
    assert {action.id for action in pair.sufficient.actions} == expected_actions
    assert {action.id for action in pair.insufficient.actions} == expected_actions
    assert all(action.id != "abstain" for action in pair.sufficient.actions)
    assert all(action.id != "abstain" for action in pair.insufficient.actions)


def test_pair_changes_only_evidence_and_supervision_role() -> None:
    pair = build_pubmedqa_evidence_pair(make_item())
    assert pair.sufficient.state == pair.insufficient.state
    assert pair.sufficient.actions == pair.insufficient.actions
    assert pair.sufficient.source_id == pair.insufficient.source_id == "123"
    assert pair.sufficient.counterfactual_group == pair.insufficient.counterfactual_group
    assert pair.sufficient.evidence
    assert pair.insufficient.evidence == []
    assert pair.sufficient.gold == Gold(action="yes", sufficient=True)
    assert pair.insufficient.gold == Gold(action=None, sufficient=False)
    assert pair.sufficient.provenance.transform_revision == NATIVE_ABSTENTION_TRANSFORM_REVISION
    assert pair.insufficient.provenance == pair.sufficient.provenance


def test_final_test_pair_is_supervision_free() -> None:
    pair = build_pubmedqa_evidence_pair(make_item(split="test", gold=False))
    assert pair.sufficient.gold is None
    assert pair.insufficient.gold is None
    assert pair.sufficient.evidence
    assert pair.insufficient.evidence == []


def test_final_test_source_rejects_serialized_gold() -> None:
    with pytest.raises(ValueError, match="must not contain serialized gold"):
        build_pubmedqa_evidence_pair(make_item(split="test", gold=True))


def test_wrong_source_is_rejected() -> None:
    item = make_item().model_copy(
        update={
            "provenance": make_item().provenance.model_copy(update={"dataset": "Other"})
        }
    )
    with pytest.raises(ValueError, match="require PubMedQA PQA-L provenance"):
        build_pubmedqa_evidence_pair(item)


def test_wrong_source_revision_is_rejected() -> None:
    item = make_item().model_copy(
        update={
            "provenance": make_item().provenance.model_copy(update={"revision": "0" * 40})
        }
    )
    with pytest.raises(ValueError, match="frozen PubMedQA revision"):
        build_pubmedqa_evidence_pair(item)


def test_wrong_source_license_is_rejected() -> None:
    item = make_item().model_copy(
        update={"provenance": make_item().provenance.model_copy(update={"license": "Other"})}
    )
    with pytest.raises(ValueError, match="qualified PubMedQA license"):
        build_pubmedqa_evidence_pair(item)


def test_wrong_parent_transform_is_rejected() -> None:
    item = make_item().model_copy(
        update={
            "provenance": make_item().provenance.model_copy(
                update={"transform_revision": "other-v1"}
            )
        }
    )
    with pytest.raises(ValueError, match="qualified PubMedQA transform"):
        build_pubmedqa_evidence_pair(item)


def test_wrong_source_url_is_rejected() -> None:
    item = make_item().model_copy(
        update={
            "provenance": make_item().provenance.model_copy(
                update={"source_url": "https://github.com/example/example"}
            )
        }
    )
    with pytest.raises(ValueError, match="frozen PubMedQA source URL"):
        build_pubmedqa_evidence_pair(item)


def test_train_role_is_rejected() -> None:
    with pytest.raises(ValueError, match="reject non-qualified PubMedQA roles"):
        build_pubmedqa_evidence_pair(make_item(split="train"))


def test_source_without_evidence_is_rejected() -> None:
    item = make_item().model_copy(update={"evidence": []})
    with pytest.raises(ValueError, match="must contain model-visible evidence"):
        build_pubmedqa_evidence_pair(item)


def test_source_with_abstain_action_is_rejected() -> None:
    item = make_item()
    item = item.model_copy(
        update={
            "actions": [
                *item.actions,
                Action(id="abstain", description="abstain"),
            ]
        }
    )
    with pytest.raises(ValueError, match="policy output"):
        build_pubmedqa_evidence_pair(item)


def test_non_test_source_without_action_gold_is_rejected() -> None:
    with pytest.raises(ValueError, match="require typed action supervision"):
        build_pubmedqa_evidence_pair(make_item(gold=False))
