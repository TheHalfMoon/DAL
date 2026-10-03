from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKER = ROOT / "registry" / "study1_sg000027_cpu_smoke_blocker.json"
FRONTIER = ROOT / "registry" / "study1_sg000027_frontier_status.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cpu_smoke_blocker_binds_exact_canonical_artifact() -> None:
    blocker = _load(BLOCKER)
    assert blocker["source_canonical_main"] == "5fbf4f30788688014cf29ef9d238a93af2d706fc"
    assert blocker["workflow_run"] == 37140291946
    assert blocker["artifact"]["id"] == 11280346690
    assert blocker["artifact"]["digest"] == (
        "sha256:40ffcbcb2366fa0a6381ab48abafe7b9a7c957021a3b4be523af2b5fe29054f9"
    )
    for entry in blocker["persisted_files"].values():
        assert _sha(ROOT / entry["path"]) == entry["sha256"]


def test_qwen_smoke_is_retained_as_blocker_not_reinterpreted_as_pass() -> None:
    blocker = _load(BLOCKER)
    result = blocker["qwen_smoke_result"]
    assert result["status"] == "blocked-behavior-changing"
    assert result["error"] is None
    assert result["tool_call_count"] == 0
    assert result["tool_name"] is None
    assert result["query_string"] is None
    assert result["cost"] == 0.0


def test_diagnosis_remains_causally_bounded() -> None:
    diagnosis = _load(BLOCKER)["diagnosis"]
    assert diagnosis["causal_status"] == "undetermined"
    assert len(diagnosis["not_yet_distinguishable"]) == 3
    assert "plausible mechanism" in diagnosis["static_source_risk"]


def test_blocker_prevents_model_freeze_query_trace_gate_and_d4() -> None:
    blocker = _load(BLOCKER)
    effects = blocker["governance_effects"]
    frontier = _load(FRONTIER)
    assert effects["base_model_frozen"] is False
    assert effects["tokenizer_frozen"] is False
    assert effects["trace_producing_system_frozen"] is False
    assert effects["query_trace_gate_ready"] is False
    assert effects["d4_allowed"] is False
    assert effects["training_allowed"] is False
    assert effects["final_role_accessed"] is False
    assert frontier["state"] == "cpu-smoke-blocked-diagnostic-pending"
    assert frontier["trace_producing_system_frozen"] is False
    assert frontier["d4_activation_allowed"] is False
