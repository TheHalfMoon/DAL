from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.update_sg000018_inventory import transform

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "registry" / "p08_real_inventory.json"


def _payload() -> dict[str, object]:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_sg000018_inventory_transform_is_idempotent() -> None:
    payload = _payload()
    assert transform(payload) == payload
    assert transform(transform(payload)) == payload


def test_sg000018_inventory_transform_fails_closed_on_native_conflict() -> None:
    payload = _payload()
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    native = next(
        entry
        for entry in datasets
        if isinstance(entry, dict) and entry.get("id") == "gax-native-abstention-pqal"
    )
    native["source_revision"] = "tampered"

    with pytest.raises(ValueError, match="conflicts with frozen SG-000018 definition"):
        transform(payload)


def test_sg000018_inventory_transform_rejects_duplicate_native_dataset() -> None:
    payload = _payload()
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    native = next(
        entry
        for entry in datasets
        if isinstance(entry, dict) and entry.get("id") == "gax-native-abstention-pqal"
    )
    datasets.append(copy.deepcopy(native))

    with pytest.raises(ValueError, match="appears more than once"):
        transform(payload)
