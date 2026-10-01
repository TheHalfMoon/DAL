from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any

from gaxbench.p08_paper_models import (
    BACKBONE_MODEL_ID,
    BACKBONE_REVISION,
    DAL_PAPER_ARCHITECTURE,
    PaperTrainingContract,
    training_contract_digest,
)
from gaxbench.p08_protocol_selection import PAPER_CHECKPOINT_SHA256
from gaxbench.provenance import sha256_file

CHECKPOINT_PATH = Path(
    "registry/p08_gax_paper_candidate_seed0_checkpoint_sg000019.json"
)
CANONICAL_CALIBRATION_RAW_PATH = Path(
    "registry/p08_calibration_raw_logits_sg000020.json"
)
CANONICAL_CALIBRATION_RAW_SHA256 = (
    "6aca49fd1a94be649737bc6076a9d818b6b67718fb1dac2412766ea8e286f109"
)
MAX_ABS_CALIBRATION_DRIFT = 1e-4
_EXPECTED_STATE_KEYS = {
    "action_bias",
    "action_weight",
    "critic_bias",
    "critic_scale",
    "suff_bias",
    "suff_scale",
}


def _load_script(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_frozen_checkpoint(
    *,
    source: Path,
    development_manifest_path: Path,
    training_contract_path: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], PaperTrainingContract, Any, Any]:
    del source, development_manifest_path, output_dir
    if not CHECKPOINT_PATH.is_file():
        raise FileNotFoundError(f"canonical frozen checkpoint missing: {CHECKPOINT_PATH}")
    actual_sha = sha256_file(CHECKPOINT_PATH)
    if actual_sha != PAPER_CHECKPOINT_SHA256:
        raise RuntimeError(
            "canonical frozen checkpoint SHA-256 mismatch: "
            f"expected {PAPER_CHECKPOINT_SHA256}, got {actual_sha}"
        )

    payload = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    contract = PaperTrainingContract.model_validate_json(
        training_contract_path.read_text(encoding="utf-8")
    )
    contract_sha = training_contract_digest(contract)
    required = {
        "schema_version": "0.3",
        "system_id": "gax-paper-candidate",
        "architecture_id": DAL_PAPER_ARCHITECTURE,
        "training_seed": 0,
        "training_contract_sha256": contract_sha,
        "base_model_id": BACKBONE_MODEL_ID,
        "base_model_revision": BACKBONE_REVISION,
        "tokenizer_revision": BACKBONE_REVISION,
        "final_test_access": "sealed",
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise RuntimeError(
                f"canonical frozen checkpoint metadata drift for {key}: "
                f"expected {expected!r}, got {payload.get(key)!r}"
            )

    state = payload.get("state")
    if not isinstance(state, dict) or set(state) != _EXPECTED_STATE_KEYS:
        raise RuntimeError("canonical frozen checkpoint state keys drifted")

    import torch

    def tensor(name: str) -> Any:
        return torch.tensor(state[name], dtype=torch.float32)

    control = {
        "action_weight": tensor("action_weight"),
        "action_bias": tensor("action_bias"),
    }
    assurance = {
        "critic_scale": tensor("critic_scale"),
        "critic_bias": tensor("critic_bias"),
        "suff_scale": tensor("suff_scale"),
        "suff_bias": tensor("suff_bias"),
    }
    if tuple(control["action_weight"].shape) != (3, 768):
        raise RuntimeError("canonical action-weight shape drifted")
    if tuple(control["action_bias"].shape) != (3,):
        raise RuntimeError("canonical action-bias shape drifted")
    if tuple(assurance["critic_bias"].shape) != (3,):
        raise RuntimeError("canonical critic-bias shape drifted")
    if tuple(assurance["critic_scale"].shape) != (1,):
        raise RuntimeError("canonical critic-scale shape drifted")
    if tuple(assurance["suff_bias"].shape) != (1,) or tuple(
        assurance["suff_scale"].shape
    ) != (1,):
        raise RuntimeError("canonical sufficiency-state shape drifted")

    execution = _load_script(
        "dal_p08_sg000020_execution",
        Path(__file__).with_name("run_p08_sg000020_execution.py"),
    )
    d03 = execution._load_script(  # noqa: SLF001
        "dal_p08_d03_sg20_frozen",
        Path(__file__).with_name("run_p08_d03_assurance.py"),
    )
    return control, assurance, contract, d03.S, d03


def _canonical_calibration_rows() -> list[dict[str, object]]:
    if not CANONICAL_CALIBRATION_RAW_PATH.is_file():
        raise FileNotFoundError(
            "canonical SG-000020 calibration logits are missing: "
            f"{CANONICAL_CALIBRATION_RAW_PATH}"
        )
    actual_sha = sha256_file(CANONICAL_CALIBRATION_RAW_PATH)
    if actual_sha != CANONICAL_CALIBRATION_RAW_SHA256:
        raise RuntimeError(
            "canonical SG-000020 calibration-logit SHA-256 mismatch: "
            f"expected {CANONICAL_CALIBRATION_RAW_SHA256}, got {actual_sha}"
        )
    payload = json.loads(CANONICAL_CALIBRATION_RAW_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != 100:
        raise RuntimeError("canonical calibration evidence must contain exactly 100 rows")
    if any(not isinstance(row, dict) for row in payload):
        raise RuntimeError("canonical calibration evidence row type drifted")
    return payload


def _require_close(observed: float, canonical: float, *, label: str) -> float:
    if not math.isfinite(observed) or not math.isfinite(canonical):
        raise RuntimeError(f"non-finite calibration value for {label}")
    drift = abs(observed - canonical)
    if drift > MAX_ABS_CALIBRATION_DRIFT:
        raise RuntimeError(
            f"live calibration drift exceeded tolerance for {label}: "
            f"{drift} > {MAX_ABS_CALIBRATION_DRIFT}"
        )
    return drift


def _canonicalize_calibration_result(
    live: tuple[
        list[list[float]],
        list[int],
        list[float],
        list[int],
        list[dict[str, object]],
    ],
) -> tuple[
    list[list[float]],
    list[int],
    list[float],
    list[int],
    list[dict[str, object]],
]:
    action_logits, action_labels, suff_logits, suff_labels, live_rows = live
    canonical_rows = _canonical_calibration_rows()
    if len(live_rows) != 100:
        raise RuntimeError("live calibration evidence must contain exactly 100 rows")

    canonical_action_logits: list[list[float]] = []
    canonical_action_labels: list[int] = []
    canonical_suff_logits: list[float] = []
    max_drift = 0.0

    for index, (observed, canonical) in enumerate(
        zip(live_rows, canonical_rows, strict=True)
    ):
        observed_id = observed.get("item_id")
        canonical_id = canonical.get("item_id")
        if observed_id != canonical_id:
            raise RuntimeError(
                "calibration item-order drift at row "
                f"{index}: {observed_id!r} != {canonical_id!r}"
            )

        observed_raw = observed.get("present_sufficiency_raw_logit")
        canonical_raw = canonical.get("present_sufficiency_raw_logit")
        if not isinstance(observed_raw, (int, float)) or not isinstance(
            canonical_raw, (int, float)
        ):
            raise RuntimeError("calibration sufficiency-logit type drifted")
        max_drift = max(
            max_drift,
            _require_close(
                float(observed_raw),
                float(canonical_raw),
                label=f"row-{index}-sufficiency",
            ),
        )
        canonical_suff_logits.append(float(canonical_raw))

        canonical_logits = canonical.get("action_logits")
        canonical_label = canonical.get("gold_action_index")
        observed_logits = observed.get("action_logits")
        observed_label = observed.get("gold_action_index")
        if index < 50:
            if not isinstance(canonical_logits, list) or len(canonical_logits) != 3:
                raise RuntimeError("canonical action-logit shape drifted")
            if not isinstance(observed_logits, list) or len(observed_logits) != 3:
                raise RuntimeError("live action-logit shape drifted")
            if not isinstance(canonical_label, int) or not isinstance(
                observed_label, int
            ):
                raise RuntimeError("calibration action-label type drifted")
            if observed_label != canonical_label:
                raise RuntimeError("calibration action-label drifted")
            canonical_row: list[float] = []
            for choice, (observed_value, canonical_value) in enumerate(
                zip(observed_logits, canonical_logits, strict=True)
            ):
                if not isinstance(observed_value, (int, float)) or not isinstance(
                    canonical_value, (int, float)
                ):
                    raise RuntimeError("calibration action-logit type drifted")
                max_drift = max(
                    max_drift,
                    _require_close(
                        float(observed_value),
                        float(canonical_value),
                        label=f"row-{index}-action-{choice}",
                    ),
                )
                canonical_row.append(float(canonical_value))
            canonical_action_logits.append(canonical_row)
            canonical_action_labels.append(canonical_label)
        elif canonical_logits is not None or canonical_label is not None:
            raise RuntimeError("canonical withheld calibration row leaked action gold")

    if action_labels != canonical_action_labels:
        raise RuntimeError("live action-label sequence drifted")
    expected_suff_labels = [1] * 50 + [0] * 50
    if suff_labels != expected_suff_labels:
        raise RuntimeError("live sufficiency-label sequence drifted")
    if len(action_logits) != 50 or len(suff_logits) != 100:
        raise RuntimeError("live calibration role count drifted")

    print(
        "SG-000020 canonical calibration replay verified; "
        f"max_abs_live_drift={max_drift:.12g}"
    )
    return (
        canonical_action_logits,
        canonical_action_labels,
        canonical_suff_logits,
        expected_suff_labels,
        canonical_rows,
    )


def main() -> int:
    execution = _load_script(
        "dal_p08_sg000020_execution_main",
        Path(__file__).with_name("run_p08_sg000020_execution.py"),
    )
    execution._reconstruct_paper_checkpoint = _load_frozen_checkpoint  # noqa: SLF001
    live_calibration = execution._calibration_logits  # noqa: SLF001

    def canonical_calibration(*args: Any, **kwargs: Any) -> Any:
        return _canonicalize_calibration_result(live_calibration(*args, **kwargs))

    execution._calibration_logits = canonical_calibration  # noqa: SLF001
    return int(execution.main())


if __name__ == "__main__":
    raise SystemExit(main())
