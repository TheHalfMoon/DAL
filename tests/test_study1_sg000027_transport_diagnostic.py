import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "registry/study1_sg000027_cpu_smoke_observation.json"
CONTRACT = ROOT / "registry/study1_sg000027_transport_diagnostic_contract.json"
WORKFLOW = ROOT / ".github/workflows/study1-sg000027-cpu-smoke.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_canonical_cpu_smoke_block_is_retained_without_freeze() -> None:
    obs = _load(OBS)
    assert obs["canonical_main_sha"] == "5fbf4f30788688014cf29ef9d238a93af2d706fc"
    assert obs["workflow_run_id"] == 37140291946
    assert obs["artifact"]["id"] == 11280346690
    assert obs["qwen_cpu_smoke"]["status"] == "blocked-behavior-changing"
    assert obs["qwen_cpu_smoke"]["tool_call_count"] == 0
    assert obs["qwen_cpu_smoke"]["development_or_final_data_accessed"] is False
    assert obs["qwen_cpu_smoke"]["selection_performed"] is False
    assert obs["qwen_cpu_smoke"]["training_performed"] is False
    assert obs["conclusion"] == "no-base-model-or-tokenizer-freeze-permitted"


def test_transport_diagnostic_is_synthetic_and_non_mutating() -> None:
    contract = _load(CONTRACT)
    assert contract["stage"] == "D3"
    repair = contract["repair_boundary"]
    assert repair["this_grain_may_modify_frozen_upstream_parser"] is False
    assert repair["this_grain_may_freeze_model_or_tokenizer"] is False
    assert contract["governance"]["synthetic_inputs_only"] is True
    assert contract["governance"]["training_allowed"] is False
    assert contract["governance"]["d4_allowed"] is False
    assert contract["governance"]["final_role_access_allowed"] is False


def test_workflow_records_raw_and_frozen_transport_before_any_repair() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Diagnose raw OpenAI-compatible tool transport on synthetic input" in text
    assert "raw_transport_probe.json" in text
    assert "transport_diagnosis.json" in text
    assert "parser-transport-mismatch" in text
    assert "model-or-template-no-tool-call" in text
    assert "model_or_tokenizer_frozen" in text
