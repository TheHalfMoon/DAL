from __future__ import annotations

from scripts.audit_medqabstain_leakage import audit


def row(
    *,
    item_id: str,
    component: str,
    role: str,
    question: str,
    options: str = '{"A":"alpha","B":"beta","C":"I abstain"}',
) -> dict[str, object]:
    return {
        "id": item_id,
        "dataset": component,
        "question": question,
        "options": options,
        "_role": role,
    }


def test_exact_duplicate_audit_is_cross_component_and_cross_role() -> None:
    rows = [
        row(
            item_id="a",
            component="source-a",
            role="life-threatening",
            question="one two three four five six seven eight nine ten",
        ),
        row(
            item_id="b",
            component="source-b",
            role="safe",
            question="one two three four five six seven eight nine ten",
        ),
    ]
    report = audit(rows)
    assert report["exact_duplicate_pair_count"] == 1
    assert report["exact_cross_component_pair_count"] == 1
    assert report["exact_cross_role_pair_count"] == 1
    assert report["near_duplicate_pair_count"] == 0


def test_near_duplicate_audit_excludes_exact_pairs() -> None:
    prefix = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen"
    rows = [
        row(
            item_id="a",
            component="source-a",
            role="safe",
            question=f"{prefix} fifteen sixteen seventeen eighteen nineteen twenty",
        ),
        row(
            item_id="b",
            component="source-b",
            role="safe",
            question=f"{prefix} fifteen sixteen seventeen eighteen nineteen changed",
        ),
    ]
    report = audit(rows)
    assert report["exact_duplicate_pair_count"] == 0
    assert report["near_duplicate_pair_count"] == 1
    assert report["near_cross_component_pair_count"] == 1
    assert report["near_cross_role_pair_count"] == 0


def test_leakage_audit_serializes_no_raw_content() -> None:
    report = audit(
        [
            row(
                item_id="secret-id",
                component="source-a",
                role="safe",
                question="private source text must not appear in evidence",
            )
        ]
    )
    serialized = str(report)
    assert "secret-id" not in serialized
    assert "private source text" not in serialized
    assert report["raw_questions_serialized"] is False
    assert report["raw_item_ids_serialized"] is False
