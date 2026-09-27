from __future__ import annotations

import json
from pathlib import Path

import pytest

from gaxbench.external_adapters import render_model_state
from gaxbench.pubmedqa import (
    PUBMEDQA_NEAR_DUPLICATE_THRESHOLD,
    PubMedQARecord,
    audit_pubmedqa_items,
    build_qualification_items,
    build_split_manifest,
    convert_record,
    git_blob_sha1,
    leakage_audit_ok,
    load_frozen_pqal,
    qualify_pubmedqa_source,
)


def _record(index: int, *, decision: str | None = None, text: str | None = None) -> dict[str, object]:
    resolved_decision = decision or ("yes", "no", "maybe")[index % 3]
    context = text or (
        f"Study {index} enrolled participants and measured a unique endpoint number {index}. "
        f"The reported abstract body contains controlled observation token {index}."
    )
    return {
        "QUESTION": f"Does intervention {index} change endpoint {index}?",
        "CONTEXTS": [context],
        "LABELS": ["RESULTS"],
        "MESHES": [f"Mesh-{index}"],
        "YEAR": "2024",
        "reasoning_required_pred": resolved_decision,
        "reasoning_free_pred": resolved_decision,
        "final_decision": resolved_decision,
        "LONG_ANSWER": f"SECRET CONCLUSION {index} {resolved_decision}",
    }


def _fixture_bytes(count: int = 1000) -> bytes:
    payload = {str(10_000_000 + index): _record(index) for index in range(count)}
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fixture_records(count: int = 1000) -> list[tuple[str, PubMedQARecord]]:
    return [
        (str(10_000_000 + index), PubMedQARecord.model_validate(_record(index)))
        for index in range(count)
    ]


def test_git_blob_sha1_matches_known_git_fixture() -> None:
    assert git_blob_sha1(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_load_frozen_pqal_rejects_wrong_blob(tmp_path: Path) -> None:
    source = tmp_path / "ori_pqal.json"
    source.write_bytes(_fixture_bytes())
    with pytest.raises(ValueError, match="Git blob mismatch"):
        load_frozen_pqal(source)


def test_split_policy_is_deterministic_and_preregistered() -> None:
    records = _fixture_records()
    first = build_split_manifest(records)
    second = build_split_manifest(records)
    assert first == second
    assert first.training_ids == []
    assert len(first.validation_ids) == 450
    assert len(first.calibration_ids) == 50
    assert len(first.test_ids) == 500
    assert not (set(first.validation_ids) & set(first.calibration_ids))
    assert not (set(first.validation_ids) & set(first.test_ids))
    assert not (set(first.calibration_ids) & set(first.test_ids))
    assert first.final_test_access == "sealed"
    assert first.test_labels_serialized is False


def test_converter_keeps_answer_adjacent_fields_out_of_model_visible_state() -> None:
    pmid = "12345678"
    record = PubMedQARecord.model_validate(_record(7, decision="yes"))
    item = convert_record(pmid, record, split="validation", include_gold=True)
    visible = json.dumps(render_model_state(item), sort_keys=True)
    assert "SECRET CONCLUSION" not in visible
    assert pmid not in visible
    assert "reasoning_required_pred" not in visible
    assert "reasoning_free_pred" not in visible
    assert "Mesh-7" not in visible
    assert "2024" not in visible
    assert record.QUESTION in visible
    assert record.CONTEXTS[0] in visible


def test_maybe_is_task_answer_not_abstention_or_sufficiency_label() -> None:
    record = PubMedQARecord.model_validate(_record(2, decision="maybe"))
    item = convert_record("123", record, split="calibration", include_gold=True)
    assert [action.id for action in item.actions] == ["maybe", "no", "yes"]
    assert item.gold is not None
    assert item.gold.action == "maybe"
    assert item.gold.sufficient is None


def test_final_test_item_cannot_serialize_gold() -> None:
    record = PubMedQARecord.model_validate(_record(1, decision="no"))
    with pytest.raises(ValueError, match="forbids serializing final-test gold"):
        convert_record("123", record, split="test", include_gold=True)


def test_qualification_items_keep_test_gold_sealed() -> None:
    records = _fixture_records()
    manifest = build_split_manifest(records)
    items = build_qualification_items(records, manifest)
    assert len(items) == 1000
    assert all(item.gold is None for item in items if item.split == "test")
    assert all(item.gold is not None for item in items if item.split != "test")


def test_near_duplicate_cross_split_fails_closed() -> None:
    repeated = (
        "This intentionally repeated biomedical passage contains enough tokens to create "
        "several identical five token shingles across two benchmark roles."
    )
    left_record = PubMedQARecord.model_validate(_record(1, text=repeated))
    right_record = PubMedQARecord.model_validate(_record(2, text=repeated))
    left = convert_record("111", left_record, split="validation", include_gold=True)
    right = convert_record("222", right_record, split="calibration", include_gold=True)
    right = right.model_copy(update={"state": left.state})
    audit = audit_pubmedqa_items([left, right])
    assert audit.cross_split_near_duplicates
    assert audit.cross_split_near_duplicates[0].jaccard >= PUBMEDQA_NEAR_DUPLICATE_THRESHOLD
    assert leakage_audit_ok(audit) is False


def test_real_qualification_shape_works_with_integrity_bound_fixture(tmp_path: Path) -> None:
    raw = _fixture_bytes()
    source = tmp_path / "ori_pqal.json"
    source.write_bytes(raw)
    manifest, audit, report = qualify_pubmedqa_source(
        source,
        expected_blob_sha1=git_blob_sha1(raw),
        expected_records=1000,
    )
    assert len(manifest.test_ids) == 500
    assert report.record_count == 1000
    assert report.final_test_access == "sealed"
    assert len(report.source_sha256) == 64
    assert len(report.split_manifest_sha256) == 64
    assert len(report.leakage_audit_sha256) == 64
    assert audit.public_pretraining_contamination_risk == "unresolved-public-benchmark"
