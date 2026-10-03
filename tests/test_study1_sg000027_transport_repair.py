import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "registry/study1_sg000027_transport_diagnosis_observation.json"
CONTRACT = ROOT / "registry/study1_sg000027_transport_repair_contract.json"
PATCH = ROOT / "patches/study1_fhir_agentbench_qwen_structured_tool_calls.patch"
WORKFLOW = ROOT / ".github/workflows/study1-sg000027-cpu-smoke.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_diagnostic_proves_parser_transport_mismatch_without_data_access() -> None:
    obs = _load(OBS)
    assert obs["canonical_main_sha"] == "08fec6e8a990adaff5163e8ed93226aab7371e3b"
    assert obs["workflow_run_id"] == 37142304592
    assert obs["artifact"]["id"] == 11281350383
    assert obs["diagnosis"] == "parser-transport-mismatch"
    assert obs["raw_transport"]["structured_tool_call_count"] == 1
    assert obs["raw_transport"]["tool_name"] == "fhir_request_get"
    assert obs["frozen_qwen_parser"]["tool_call_count"] == 0
    assert obs["development_or_final_data_accessed"] is False
    assert obs["model_or_tokenizer_frozen"] is False


def test_transport_patch_is_exactly_bounded_and_digest_bound() -> None:
    contract = _load(CONTRACT)
    repair = contract["repair"]
    assert hashlib.sha256(PATCH.read_bytes()).hexdigest() == repair["patch_sha256"]
    text = PATCH.read_text(encoding="utf-8")
    deleted = [
        line[1:]
        for line in text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    added = [
        line[1:]
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    assert deleted == [
        (
            "                response = litellm.Message(**qwen_parse_tool_calls("
            "output.choices[0].message.content))"
        )
    ]
    assert added == [
        "                native_message = output.choices[0].message",
        "                if getattr(native_message, \"tool_calls\", None):",
        "                    response = native_message",
        "                else:",
        (
            "                    response = litellm.Message(**qwen_parse_tool_calls("
            "native_message.content))"
        ),
    ]
    assert repair["fallback_parser_preserved"] is True
    assert repair["changes_prompt"] is False
    assert repair["changes_tool_schema"] is False
    assert repair["changes_model_or_tokenizer"] is False
    assert repair["changes_agent_strategy"] is False


def test_repair_grain_cannot_freeze_or_activate_d4() -> None:
    contract = _load(CONTRACT)
    governance = contract["governance"]
    assert governance["this_grain_may_freeze_model_or_tokenizer"] is False
    assert governance["training_allowed"] is False
    assert governance["d4_allowed"] is False
    assert governance["final_role_access_allowed"] is False
    assert governance["separate_freeze_grain_required_after_canonical_repair_pass"] is True


def test_workflow_applies_patch_before_repaired_smoke_and_requires_pass() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    apply_pos = text.index("Apply governed Qwen structured-tool transport patch")
    smoke_pos = text.index("Execute synthetic tool-call smoke through frozen safe_llm_call")
    assert apply_pos < smoke_pos
    assert "transport_patch_receipt.json" in text
    assert 'if smoke["status"] != "pass"' in text
    assert 'required_transport_diagnosis_after_repair' in text
