from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

_SPACE = re.compile(r"\s+")


def normalize(value: object) -> str:
    return _SPACE.sub(" ", str(value).strip().casefold())


def parse_options(raw: object) -> dict[str, str]:
    if isinstance(raw, dict):
        value = raw
    elif isinstance(raw, list):
        return {str(index): str(item) for index, item in enumerate(raw)}
    elif isinstance(raw, str):
        value: Any
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(raw)
            except (ValueError, SyntaxError) as exc:
                raise ValueError("option payload is neither JSON nor a Python literal") from exc
    else:
        raise ValueError("unsupported option payload type")

    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    if isinstance(value, list):
        return {str(index): str(item) for index, item in enumerate(value)}
    raise ValueError("parsed option payload must be a mapping or list")


def resolve_answer(answer: object, options: dict[str, str]) -> str:
    text = str(answer)
    if text in options:
        return options[text]
    upper = text.strip().upper()
    if upper in options:
        return options[upper]
    return text


def load_rows(path: Path, role: str) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    needed = {
        "id",
        "dataset",
        "options",
        "answer",
        "original_options",
        "original_answer",
    }
    missing = needed - set(table.column_names)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    for raw in table.select(sorted(needed)).to_pylist():
        raw["_role"] = role
        rows.append(raw)
    return rows


def digest_keys(keys: set[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(keys), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    component_counts: Counter[str] = Counter()
    composite_keys: list[str] = []
    original_gold_visible = Counter[str]()
    transformed_gold_missing = Counter[str]()
    abstention_gold = Counter[str]()
    option_count_changed = Counter[str]()
    parse_failures = Counter[str]()
    role_keys: dict[str, set[str]] = defaultdict(set)
    quarantine_keys: dict[str, set[str]] = defaultdict(set)
    eligible_keys: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        component = str(row["dataset"])
        item_id = str(row["id"])
        role = str(row["_role"])
        key = f"{component}\u0000{item_id}"
        component_counts[component] += 1
        composite_keys.append(key)
        role_keys[role].add(key)
        anomaly = False
        try:
            original_options = parse_options(row["original_options"])
            transformed_options = parse_options(row["options"])
        except ValueError:
            parse_failures[component] += 1
            anomaly = True
            original_options = {}
            transformed_options = {}

        if not anomaly:
            original_gold = normalize(resolve_answer(row["original_answer"], original_options))
            transformed_gold = normalize(resolve_answer(row["answer"], transformed_options))
            visible_values = {normalize(value) for value in transformed_options.values()}

            if original_gold in visible_values:
                original_gold_visible[component] += 1
                anomaly = True
            if transformed_gold not in visible_values:
                transformed_gold_missing[component] += 1
                anomaly = True
            if transformed_gold == "i abstain":
                abstention_gold[component] += 1
            else:
                anomaly = True
            if len(original_options) != len(transformed_options):
                option_count_changed[component] += 1
                anomaly = True

        if anomaly:
            quarantine_keys[component].add(key)
        else:
            eligible_keys[component].add(key)

    duplicate_composite_keys = len(composite_keys) - len(set(composite_keys))
    cross_role_overlap = len(
        role_keys.get("life-threatening", set()) & role_keys.get("safe", set())
    )
    components = sorted(component_counts)
    all_quarantine = set().union(*(quarantine_keys[c] for c in components))
    all_eligible = set().union(*(eligible_keys[c] for c in components))

    result = {
        "schema_version": "0.2",
        "dataset_id": "disi-unibo-nlp/MedQAbstain",
        "dataset_revision": "d215847217bb5f4124b9110379d33b9eb2f8d3f7",
        "lineage_key": "dataset+id",
        "row_count": len(rows),
        "component_counts": dict(sorted(component_counts.items())),
        "duplicate_composite_key_count": duplicate_composite_keys,
        "cross_lt_safe_composite_key_overlap_count": cross_role_overlap,
        "membership_sha256": digest_keys(set(composite_keys)),
        "eligible_item_count": len(all_eligible),
        "eligible_membership_sha256": digest_keys(all_eligible),
        "quarantined_item_count": len(all_quarantine),
        "quarantine_membership_sha256": digest_keys(all_quarantine),
        "quarantine_rule": (
            "parse-failure-or-original-gold-visible-or-transformed-gold-not-visible-or-"
            "transformed-gold-not-i-abstain-or-option-count-changed"
        ),
        "per_component": {
            component: {
                "row_count": component_counts[component],
                "option_parse_failure_count": parse_failures[component],
                "original_gold_still_visible_count": original_gold_visible[component],
                "transformed_gold_not_visible_count": transformed_gold_missing[component],
                "abstention_gold_count": abstention_gold[component],
                "non_abstention_gold_count": (
                    component_counts[component] - abstention_gold[component]
                ),
                "option_count_changed_count": option_count_changed[component],
                "eligible_item_count": len(eligible_keys[component]),
                "eligible_membership_sha256": digest_keys(eligible_keys[component]),
                "quarantined_item_count": len(quarantine_keys[component]),
                "quarantine_membership_sha256": digest_keys(quarantine_keys[component]),
            }
            for component in components
        },
        "raw_rows_serialized": False,
        "raw_questions_serialized": False,
        "raw_answers_serialized": False,
        "raw_item_ids_serialized": False,
        "final_test_access": "sealed",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lt", required=True)
    parser.add_argument("--safe", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = load_rows(Path(args.lt), "life-threatening") + load_rows(Path(args.safe), "safe")
    result = audit(rows)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "row_count": result["row_count"],
                "eligible_item_count": result["eligible_item_count"],
                "quarantined_item_count": result["quarantined_item_count"],
                "duplicate_composite_key_count": result["duplicate_composite_key_count"],
                "cross_lt_safe_composite_key_overlap_count": result[
                    "cross_lt_safe_composite_key_overlap_count"
                ],
                "per_component": result["per_component"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
