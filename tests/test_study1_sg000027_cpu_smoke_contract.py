from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry" / "study1_sg000027_cpu_smoke_contract.json"
WORKFLOW = ROOT / ".github" / "workflows" / "study1-sg000027-cpu-smoke.yml"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_cpu_smoke_is_synthetic_only_and_cannot_freeze() -> None:
    contract = _contract()
    assert contract["stage"] == "D3"
    assert contract["freeze_rule"]["automatic_freeze_allowed_by_this_grain"] is False
    forbidden = contract["inputs_forbidden"]
    assert (
        "FHIR-AgentBench final-role question text, labels, traces, gold IDs, or outputs"
        in forbidden
    )
    assert contract["governance"]["d4_allowed"] is False
    assert contract["governance"]["training_allowed"] is False
    assert contract["governance"]["final_role_access_allowed"] is False


def test_provider_preflight_is_preregistered_before_weight_download() -> None:
    preflight = _contract()["provider_routing_preflight"]
    assert preflight["expected"] == {
        "phi4-mini-instruct": "blocked-unrecognized-provider",
        "qwen3-4b-instruct-2507": "eligible-qwen-provider",
        "smollm3-3b": "blocked-unrecognized-provider",
    }
    assert preflight["blocked_candidates_are_negative_evidence"] is True


def test_qwen_execution_identity_is_exact_and_zero_cost() -> None:
    identity = _contract()["qwen_cpu_execution_identity"]
    assert identity["base_model_revision"] == "cdbee75f17c01a7cc42f958dc650907174af0554"
    assert identity["tokenizer_revision"] == identity["base_model_revision"]
    assert identity["quantized_repo_revision"] == "e6f794d44f9395d0184a966c27b5ae99ea356fcb"
    assert identity["quantized_file_sha256"] == (
        "ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1"
    )
    assert identity["runtime_commit"] == "d2e54583c7452353eb35d40431281f6ee984332f"
    assert identity["zero_founder_cost"] is True


def test_workflow_is_main_only_digest_bound_and_never_reads_benchmark_rows() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" not in workflow
    assert "branches:\n      - main" in workflow
    assert "bbb42909a5a7eb907d1cd91f72a560729e7037ea" in workflow
    assert "d2e54583c7452353eb35d40431281f6ee984332f" in workflow
    assert "ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1" in workflow
    assert "DAL-SMOKE-0001" in workflow
    assert "final_dataset/questions_answers_sql_fhir.csv" not in workflow
    assert "development_projection.jsonl" not in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow


def test_smoke_pass_contract_requires_exact_fhir_tool_call() -> None:
    smoke = _contract()["synthetic_tool_call_contract"]
    assert smoke["tool_name"] == "fhir_request_get"
    assert smoke["required_argument"] == "query_string"
    assert smoke["required_synthetic_marker"] == "DAL-SMOKE-0001"
    assert smoke["must_execute_through_frozen_safe_llm_call"] is True
    assert smoke["must_not_execute_real_fhir_request"] is True
