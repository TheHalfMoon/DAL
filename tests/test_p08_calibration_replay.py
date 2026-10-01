from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from gaxbench.provenance import sha256_file

_RAW_PATH = Path("registry/p08_calibration_raw_logits_sg000020.json")
_RAW_SHA256 = "6aca49fd1a94be649737bc6076a9d818b6b67718fb1dac2412766ea8e286f109"


def _module() -> Any:
    path = Path("scripts/run_p08_sg000020_from_checkpoint.py")
    spec = importlib.util.spec_from_file_location("dal_sg20_replay_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SG-000020 replay script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows() -> list[dict[str, object]]:
    payload = json.loads(_RAW_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def _live(rows: list[dict[str, object]]) -> tuple[
    list[list[float]],
    list[int],
    list[float],
    list[int],
    list[dict[str, object]],
]:
    action_logits: list[list[float]] = []
    action_labels: list[int] = []
    suff_logits: list[float] = []
    for index, row in enumerate(rows):
        raw = row["present_sufficiency_raw_logit"]
        assert isinstance(raw, (int, float))
        suff_logits.append(float(raw))
        if index < 50:
            logits = row["action_logits"]
            label = row["gold_action_index"]
            assert isinstance(logits, list)
            assert isinstance(label, int)
            action_logits.append([float(value) for value in logits])
            action_labels.append(label)
    return action_logits, action_labels, suff_logits, [1] * 50 + [0] * 50, rows


def test_canonical_calibration_logits_are_content_addressed() -> None:
    assert sha256_file(_RAW_PATH) == _RAW_SHA256
    rows = _rows()
    assert len(rows) == 100
    assert all(row["action_logits"] is not None for row in rows[:50])
    assert all(row["action_logits"] is None for row in rows[50:])


def test_replay_accepts_small_host_float_drift_and_returns_canonical() -> None:
    module = _module()
    canonical = _rows()
    observed = deepcopy(canonical)
    first = observed[0]
    logits = first["action_logits"]
    assert isinstance(logits, list)
    logits[0] = float(logits[0]) + 5e-5
    first["present_sufficiency_raw_logit"] = (
        float(first["present_sufficiency_raw_logit"]) - 5e-5
    )

    replayed = module._canonicalize_calibration_result(_live(observed))
    assert replayed[0] == _live(canonical)[0]
    assert replayed[2] == _live(canonical)[2]
    assert replayed[4] == canonical


def test_replay_fails_closed_on_material_host_float_drift() -> None:
    module = _module()
    observed = deepcopy(_rows())
    first = observed[0]
    logits = first["action_logits"]
    assert isinstance(logits, list)
    logits[0] = float(logits[0]) + 2e-4

    with pytest.raises(RuntimeError, match="exceeded tolerance"):
        module._canonicalize_calibration_result(_live(observed))
