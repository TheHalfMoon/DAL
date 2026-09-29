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

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
SHINGLE_SIZE = 5
NEAR_DUPLICATE_THRESHOLD = 0.80


def normalize(value: object) -> str:
    return " ".join(_TOKEN_RE.findall(str(value).casefold()))


def parse_options(raw: object) -> dict[str, str]:
    if isinstance(raw, dict):
        value = raw
    elif isinstance(raw, list):
        return {str(index): str(item) for index, item in enumerate(raw)}
    elif isinstance(raw, str):
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


def shingles(text: str) -> set[str]:
    tokens = text.split()
    if not tokens:
        return set()
    if len(tokens) < SHINGLE_SIZE:
        return {" ".join(tokens)}
    return {
        " ".join(tokens[index : index + SHINGLE_SIZE])
        for index in range(len(tokens) - SHINGLE_SIZE + 1)
    }


def pair_digest(keys: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(keys), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_rows(path: Path, role: str) -> list[dict[str, Any]]:
    table = pq.read_table(path, columns=["id", "dataset", "question", "options"])
    rows = table.to_pylist()
    for row in rows:
        row["_role"] = role
    return rows


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys: list[str] = []
    components: list[str] = []
    roles: list[str] = []
    fingerprints: list[str] = []
    shingle_sets: list[set[str]] = []
    parse_failures: Counter[str] = Counter()

    for row in rows:
        component = str(row["dataset"])
        item_id = str(row["id"])
        role = str(row["_role"])
        try:
            options = parse_options(row["options"])
        except ValueError:
            parse_failures[component] += 1
            options = {}

        question = normalize(row["question"])
        option_values = sorted(normalize(value) for value in options.values())
        visible_payload = {"question": question, "options": option_values}
        fingerprint = hashlib.sha256(
            json.dumps(visible_payload, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        visible_text = " ".join([question, *option_values]).strip()

        keys.append(f"{component}\u0000{item_id}")
        components.append(component)
        roles.append(role)
        fingerprints.append(fingerprint)
        shingle_sets.append(shingles(visible_text))

    fingerprint_groups: dict[str, list[int]] = defaultdict(list)
    for index, fingerprint in enumerate(fingerprints):
        fingerprint_groups[fingerprint].append(index)

    exact_pair_tokens: list[str] = []
    exact_cross_component = 0
    exact_cross_role = 0
    exact_pair_count = 0
    exact_duplicate_group_count = 0
    for indices in fingerprint_groups.values():
        if len(indices) < 2:
            continue
        exact_duplicate_group_count += 1
        for offset, left in enumerate(indices):
            for right in indices[offset + 1 :]:
                exact_pair_count += 1
                if components[left] != components[right]:
                    exact_cross_component += 1
                if roles[left] != roles[right]:
                    exact_cross_role += 1
                token = hashlib.sha256(
                    f"{keys[left]}\u0000{keys[right]}".encode("utf-8")
                ).hexdigest()
                exact_pair_tokens.append(token)

    postings: dict[str, list[int]] = defaultdict(list)
    intersections: dict[tuple[int, int], int] = defaultdict(int)
    for index, current in enumerate(shingle_sets):
        current_size = len(current)
        for shingle in current:
            for other in postings[shingle]:
                other_size = len(shingle_sets[other])
                largest = max(current_size, other_size)
                if largest == 0:
                    continue
                if min(current_size, other_size) / largest < NEAR_DUPLICATE_THRESHOLD:
                    continue
                intersections[(other, index)] += 1
            postings[shingle].append(index)

    near_pair_tokens: list[str] = []
    near_cross_component = 0
    near_cross_role = 0
    near_pair_count = 0
    component_pair_counts: Counter[str] = Counter()
    for (left, right), intersection in intersections.items():
        if fingerprints[left] == fingerprints[right]:
            continue
        union = len(shingle_sets[left]) + len(shingle_sets[right]) - intersection
        if union == 0 or intersection / union < NEAR_DUPLICATE_THRESHOLD:
            continue
        near_pair_count += 1
        if components[left] != components[right]:
            near_cross_component += 1
        if roles[left] != roles[right]:
            near_cross_role += 1
        pair_name = "|".join(sorted((components[left], components[right])))
        component_pair_counts[pair_name] += 1
        token = hashlib.sha256(
            f"{keys[left]}\u0000{keys[right]}".encode("utf-8")
        ).hexdigest()
        near_pair_tokens.append(token)

    composite_key_count = len(set(keys))
    result = {
        "schema_version": "0.1",
        "dataset_id": "disi-unibo-nlp/MedQAbstain",
        "dataset_revision": "d215847217bb5f4124b9110379d33b9eb2f8d3f7",
        "lineage_key": "dataset+id",
        "model_visible_surface": "normalized-question+transformed-option-values",
        "row_count": len(rows),
        "unique_composite_key_count": composite_key_count,
        "duplicate_composite_key_count": len(rows) - composite_key_count,
        "option_parse_failure_counts": dict(sorted(parse_failures.items())),
        "exact_duplicate_group_count": exact_duplicate_group_count,
        "exact_duplicate_pair_count": exact_pair_count,
        "exact_cross_component_pair_count": exact_cross_component,
        "exact_cross_role_pair_count": exact_cross_role,
        "exact_pair_digest": pair_digest(exact_pair_tokens),
        "near_duplicate_rule": {
            "normalization": "unicode-word-casefold",
            "shingle_size": SHINGLE_SIZE,
            "jaccard_threshold": NEAR_DUPLICATE_THRESHOLD,
            "exact_duplicates_excluded": True,
        },
        "near_duplicate_pair_count": near_pair_count,
        "near_cross_component_pair_count": near_cross_component,
        "near_cross_role_pair_count": near_cross_role,
        "near_component_pair_counts": dict(sorted(component_pair_counts.items())),
        "near_pair_digest": pair_digest(near_pair_tokens),
        "public_pretraining_contamination": "unresolved-public-benchmark",
        "raw_rows_serialized": False,
        "raw_questions_serialized": False,
        "raw_options_serialized": False,
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
                "exact_duplicate_pair_count": result["exact_duplicate_pair_count"],
                "near_duplicate_pair_count": result["near_duplicate_pair_count"],
                "near_cross_component_pair_count": result[
                    "near_cross_component_pair_count"
                ],
                "near_cross_role_pair_count": result["near_cross_role_pair_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
