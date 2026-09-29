from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_value(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )


def probe(path: Path, role: str) -> dict[str, Any]:
    table = pq.read_table(path)
    columns = list(table.column_names)
    result: dict[str, Any] = {
        "role": role,
        "file_name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "row_count": table.num_rows,
        "column_count": table.num_columns,
        "columns": columns,
        "schema": {field.name: str(field.type) for field in table.schema},
        "null_counts": {name: table[name].null_count for name in columns},
    }

    if "dataset" in columns:
        values = [str(value) for value in table["dataset"].to_pylist() if value is not None]
        result["component_counts"] = dict(sorted(Counter(values).items()))
    else:
        result["component_counts"] = {}

    if "id" in columns:
        ids = [str(value) for value in table["id"].to_pylist() if value is not None]
        result["non_null_id_count"] = len(ids)
        result["unique_id_count"] = len(set(ids))
        result["duplicate_id_count"] = len(ids) - len(set(ids))
        result["id_membership_sha256"] = hashlib.sha256(
            stable_value(sorted(ids)).encode("utf-8")
        ).hexdigest()
    else:
        result["non_null_id_count"] = 0
        result["unique_id_count"] = 0
        result["duplicate_id_count"] = 0
        result["id_membership_sha256"] = None

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lt", required=True)
    parser.add_argument("--safe", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lt = probe(Path(args.lt), "life-threatening")
    safe = probe(Path(args.safe), "safe")
    combined_components: Counter[str] = Counter()
    combined_components.update(lt["component_counts"])
    combined_components.update(safe["component_counts"])

    payload = {
        "schema_version": "0.1",
        "dataset_id": "disi-unibo-nlp/MedQAbstain",
        "dataset_revision": "d215847217bb5f4124b9110379d33b9eb2f8d3f7",
        "files": [lt, safe],
        "total_rows": lt["row_count"] + safe["row_count"],
        "component_counts": dict(sorted(combined_components.items())),
        "raw_rows_serialized": False,
        "raw_questions_serialized": False,
        "raw_answers_serialized": False,
        "final_test_access": "sealed",
    }
    Path(args.output).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "total_rows": payload["total_rows"],
                "component_counts": payload["component_counts"],
                "lt_sha256": lt["sha256"],
                "safe_sha256": safe["sha256"],
                "columns": lt["columns"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
