from __future__ import annotations

import importlib.util
import json
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


def main() -> int:
    execution = _load_script(
        "dal_p08_sg000020_execution_main",
        Path(__file__).with_name("run_p08_sg000020_execution.py"),
    )
    execution._reconstruct_paper_checkpoint = _load_frozen_checkpoint  # noqa: SLF001
    return int(execution.main())


if __name__ == "__main__":
    raise SystemExit(main())
