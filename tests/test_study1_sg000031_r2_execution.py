"""Synthetic structural qualification only: no model, benchmark source, or final content."""

from __future__ import annotations

import importlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from gaxbench.study1_query_trace_gate import DevelopmentTraceInput, normalize_relative_fhir_get
from gaxbench.study1_recovery_execution import (
    BASE_URL,
    MODEL,
    R1_MANIFEST_SHA256,
    R2Call,
    R2Row,
    call_audit,
    classify_rows,
    digest,
    json_bytes,
    planned_rows,
    read_journal,
    run_rows,
    verify_frozen_controls,
    verify_sdk_qualification,
)
from gaxbench.study1_recovery_runtime import R1RecoveryRuntime

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("study1_sg000031_r2_runner")


@pytest.fixture
def runtime():
    patient = "DAL-R2-SYNTHETIC-PATIENT"
    return R1RecoveryRuntime.from_resources(
        [{"resourceType": "Patient", "id": patient}],
        role="calibration",
        development_patient_digests=frozenset({digest(patient)}),
    )


class Response:
    def __init__(self, calls):
        self.tool_calls = calls

    def model_dump(self, **_kwargs):
        return {
            "content": "synthetic private output",
            "tool_calls": [
                {"name": call.function.name, "arguments": call.function.arguments}
                for call in self.tool_calls
            ],
        }


def tool(arguments, name="fhir_request_get"):
    return SimpleNamespace(function=SimpleNamespace(name=name, arguments=arguments))


def fixture_inputs(count=3):
    return [
        DevelopmentTraceInput(
            "calibration", digest(f"synthetic-{i}"), f"Synthetic question with private input {i}"
        )
        for i in range(count)
    ]


def run_fixture(
    tmp_path, runtime, *, responses=None, raise_at=None, durable_fail_at=None, usage_override=None
):
    inputs = fixture_inputs()
    admitted = []
    requests = []
    guards = []
    checkpoints = []

    def first_turn(**kwargs):
        requests.append(kwargs)
        guards[-1](digest(json_bytes(kwargs)))
        admitted.append(len(requests))
        if raise_at == len(requests):
            raise RuntimeError("private model or infrastructure exception payload")
        response = responses[len(requests) - 1] if responses else Response([])
        return (
            response,
            None,
            {
                "cost": None,
                "prompt_tokens": 10,
                "completion_tokens": 2,
                "_wire_http_status": 200,
                "_wire_response_sha256": digest("synthetic wire"),
                **((usage_override or {}) if len(requests) == 1 else {}),
            },
        )

    def checkpoint(row):
        checkpoints.append(row.model_dump())
        if durable_fail_at == len(checkpoints):
            raise RuntimeError("durable checkpoint unavailable")

    journal = tmp_path / "fixture-journal.jsonl"
    result = run_rows(
        inputs,
        runtimes={"calibration": runtime},
        first_turn=first_turn,
        system_messages=[{"role": "system", "content": "synthetic frozen prompt"}],
        tools=[],
        journal_path=journal,
        before_call=lambda: None,
        install_post_guard=guards.append,
        zero_cost_infrastructure_verified=True,
        durable_checkpoint=checkpoint,
    )
    latest = read_journal(journal, planned_rows(inputs))
    return result, list(latest.values()), requests, admitted, journal


def test_exact_controls_and_historical_identities():
    contract = verify_frozen_controls(ROOT)
    assert contract["canonical_r1"]["manifest_sha256"] == R1_MANIFEST_SHA256
    assert contract["producer"]["base_model"] == MODEL
    assert contract["original_sg000028"]["blockers"] == 1239
    assert contract["execution"]["D4"] is False


def test_one_first_turn_per_row_and_no_raw_artifact(tmp_path, runtime):
    result, rows, requests, admissions, journal = run_fixture(tmp_path, runtime)
    assert not result["interrupted"] and len(requests) == len(rows) == 3
    assert admissions == [1, 2, 3]
    assert all(row.generation_attempts == row.http_post_admissions == 1 for row in rows)
    assert all(row.status == "behavior-changing-blocker" for row in rows)
    assert all(row.cost == 0.0 and row.sdk_reported_cost is None for row in rows)
    for request in requests:
        assert request["max_retries"] == 1 and request["temperature"] == 0.0
        assert request["base_url"] == BASE_URL and request["model"] == MODEL
        assert len(request["messages"]) == 2
    payload = journal.read_text()
    assert "private" not in payload and "synthetic frozen prompt" not in payload
    assert all(
        row.final_rows_materialized == 0 and not row.answer_correctness_scored for row in rows
    )


def test_inference_exception_stops_without_retry_and_retains_denominator(tmp_path, runtime):
    result, rows, requests, _, journal = run_fixture(tmp_path, runtime, raise_at=1)
    assert result["interrupted"] and len(requests) == 1
    assert [row.generation_attempts for row in rows] == [1, 0, 0]
    assert rows[0].error_sha256 and rows[0].blocker_codes == ["experiment-exception-stop"]
    assert "private model" not in journal.read_text()
    assert (
        classify_rows(rows, engineering_qualified=True, interrupted=True)["scientific_state"]
        == "BLOCKED"
    )


def test_durable_wire_checkpoint_failure_prevents_transmission_and_later_rows(tmp_path, runtime):
    result, rows, requests, admissions, _ = run_fixture(tmp_path, runtime, durable_fail_at=1)
    assert result["interrupted"] and len(requests) == 1 and admissions == []
    assert [row.generation_attempts for row in rows] == [1, 0, 0]


def test_completion_checkpoint_failure_stops_next_row(tmp_path, runtime):
    result, rows, requests, _, _ = run_fixture(tmp_path, runtime, durable_fail_at=2)
    assert result["interrupted"] and len(requests) == 1
    assert result["fatal_code"] == "durable-checkpoint-failed-stop"
    assert rows[0].status == "behavior-changing-blocker"


def test_accounting_failure_retains_wire_and_parsed_response_identity(
    tmp_path, runtime, monkeypatch
):
    module = importlib.import_module("gaxbench.study1_recovery_execution")

    def fail(*args):
        raise RuntimeError("synthetic accounting failure")

    monkeypatch.setattr(module, "call_audit", fail)
    response = Response([tool("{}")])
    result, rows, requests, _, _ = run_fixture(
        tmp_path, runtime, responses=[response, Response([]), Response([])]
    )
    assert result["interrupted"] and len(requests) == 1
    assert rows[0].wire_response_sha256 == digest("synthetic wire")
    assert rows[0].response_sha256 == digest(json_bytes(response.model_dump()))


def test_failed_output_row_is_retained_without_retry_and_continues(tmp_path, runtime):
    result, rows, requests, _, _ = run_fixture(
        tmp_path, runtime, responses=[None, Response([]), Response([])]
    )
    assert not result["interrupted"] and len(requests) == 3
    assert "inference-failed-row" in rows[0].blocker_codes
    assert len(rows) == 3


@pytest.mark.parametrize(
    ("arguments", "name", "code"),
    [
        ("{private broken JSON", "fhir_request_get", "malformed-tool-arguments"),
        ("[]", "fhir_request_get", "malformed-tool-arguments"),
        ("{}", "fhir_request_get", "missing-query-string"),
        ("{}", "proc_query", "unexpected-tool-name"),
    ],
)
def test_malformed_calls_preserved_without_raw_values(arguments, name, code, runtime):
    audit = call_audit(tool(arguments, name), 0, runtime)
    assert audit.arguments_sha256 == digest(arguments)
    assert audit.blocker_codes == [code] and audit.disposition == "hard-blocked"
    assert "private" not in audit.model_dump_json()


def test_every_call_retained_even_malformed(tmp_path, runtime):
    response = Response([tool("{"), tool("{}", "proc_query")])
    result, rows, requests, _, _ = run_fixture(tmp_path, runtime, responses=[response] * 3)
    assert not result["interrupted"] and len(requests) == 3
    assert all(row.tool_call_count == len(row.calls) == 2 for row in rows)


def test_out_of_manifest_request_is_blocked_and_hash_linked(runtime):
    query = "ImaginaryResource?invented=private-value"
    audit = call_audit(tool(json.dumps({"query_string": query})), 0, runtime)
    assert audit.original_request_sha256 == digest(query)
    assert audit.observed_pattern_sha256 and audit.source_pattern_sha256 is None
    assert audit.blocker_codes == ["out-of-manifest-pattern"]
    assert "private-value" not in audit.model_dump_json()


def test_journal_cannot_be_resumed_or_replayed(tmp_path, runtime):
    _, rows, _, _, journal = run_fixture(tmp_path, runtime)
    with pytest.raises(FileExistsError):
        run_fixture(tmp_path, runtime)
    with journal.open("ab") as handle:
        handle.write(json_bytes(rows[0].model_dump()))
    with pytest.raises(ValueError, match="replay"):
        read_journal(journal, planned_rows(fixture_inputs()))


def test_partial_journal_write_cannot_qualify(tmp_path, runtime):
    _, _, _, _, journal = run_fixture(tmp_path, runtime)
    journal.write_bytes(journal.read_bytes()[:-1])
    with pytest.raises(ValueError, match="interrupted journal"):
        read_journal(journal, planned_rows(fixture_inputs()))


@pytest.mark.parametrize(
    "extra",
    [
        {"raw_query": "private"},
        {"role": "final"},
        {"final_rows_materialized": 1},
        {"cost": 1.0},
        {"r1_manifest_sha256": "0" * 64},
        {"blocker_codes": ["private-patient-fragment"]},
    ],
)
def test_unsafe_or_drifted_row_rejected(extra):
    data = planned_rows(fixture_inputs(1))[0].model_dump()
    with pytest.raises(ValidationError):
        R2Row.model_validate({**data, **extra})


def test_transformation_requires_rules_and_label():
    with pytest.raises(ValidationError):
        R2Call(ordinal=0, disposition="recovery-transformed", recovery_transformed=True)
    call = R2Call(
        ordinal=0,
        disposition="hard-blocked",
        recovery_transformed=True,
        label="recovery-transformed",
        transformation_rule_ids=["empty-parameter-handling"],
        blocker_codes=["out-of-manifest-pattern"],
    )
    assert call.label == "recovery-transformed"


def test_unknown_or_incomplete_population_never_passes():
    rows = planned_rows(fixture_inputs())
    for interrupted in (False, True):
        report = classify_rows(rows, engineering_qualified=True, interrupted=interrupted)
        assert report["scientific_state"] == "BLOCKED" and not report["population_complete"]
        assert report["unfinished_rows"] == 3 and report["original_sg000028"]["blockers"] == 1239
        assert report["D4"] is False


def test_actual_http_guard_rejects_second_post_and_producer_drift(runner):
    guard = runner.HttpGenerationGuard()
    guard.expected_messages, guard.expected_tools = [{"role": "user", "content": "synthetic"}], []
    guard.active = True
    count = []

    def once(sha):
        if count:
            raise RuntimeError("second POST forbidden")
        count.append(sha)

    guard.install(once)
    payload = {"model": MODEL, "temperature": 0.0, "messages": guard.expected_messages, "tools": []}
    request = SimpleNamespace(
        method="POST", url=BASE_URL + "/chat/completions", content=json_bytes(payload)
    )
    guard.hook(request)
    with pytest.raises(RuntimeError, match="second POST"):
        guard.hook(request)
    assert len(count) == 1
    for key, value in (
        ("model", "changed-model"),
        ("temperature", 0.1),
        ("temperature", False),
        ("messages", []),
        ("tools", [{"changed": True}]),
        ("stream", True),
    ):
        request.content = json_bytes({**payload, key: value})
        with pytest.raises(RuntimeError, match="wire semantics"):
            guard.hook(request)
    request.url = "https://api.openai.com/v1/chat/completions"
    with pytest.raises(RuntimeError, match="loopback"):
        guard.hook(request)


def test_zero_cost_infrastructure_is_required_before_any_call(tmp_path, runtime):
    with pytest.raises(ValueError, match="zero-cost"):
        run_rows(
            fixture_inputs(),
            runtimes={"calibration": runtime},
            first_turn=lambda **_: None,
            system_messages=[],
            tools=[],
            journal_path=tmp_path / "not-created.jsonl",
            before_call=lambda: None,
            install_post_guard=lambda _: None,
            zero_cost_infrastructure_verified=False,
            durable_checkpoint=lambda _: None,
        )
    assert not (tmp_path / "not-created.jsonl").exists()


def test_workflow_is_dispatch_only_and_failure_stops_every_later_shard():
    text = (ROOT / ".github/workflows/study1-sg000031-r2-recovery.yml").read_text()
    assert "workflow_dispatch:" in text and "  push:" not in text and "  pull_request:" not in text
    assert "cancel-in-progress: false" in text
    for shard in range(1, 8):
        assert f"needs: [admission, shard-{shard - 1}]" in text
    worker = (ROOT / ".github/workflows/study1-sg000031-r2-worker.yml").read_text()
    assert "if: always()" in worker and "--retry 3" not in worker
    assert "scripts/study1_sg000028_query_trace_runner.py" not in worker


@pytest.mark.parametrize(
    ("status", "error_type", "guard_failed", "stop"),
    [
        (400, "exceed_context_size_error", False, False),
        (400, "invalid_request_error", False, True),
        (500, None, False, True),
        (200, None, True, True),
        (None, None, False, True),
    ],
)
def test_wire_failure_classification_stops_only_infrastructure_or_experiment(
    tmp_path, runtime, status, error_type, guard_failed, stop
):
    result, rows, requests, _, _ = run_fixture(
        tmp_path,
        runtime,
        responses=[None, Response([]), Response([])],
        usage_override={
            "_wire_http_status": status,
            "_wire_error_type": error_type,
            "_guard_failed": guard_failed,
        },
    )
    assert result["interrupted"] is stop
    assert len(requests) == (1 if stop else 3)
    assert len(rows) == 3 and rows[0].status == "behavior-changing-blocker"


def test_unparsed_wire_calls_are_hashed_and_disposed_without_runtime_execution(tmp_path, runtime):
    wire = {
        "function": {
            "name": "fhir_request_get",
            "arguments": '{"query_string":"ImaginaryResource?private=value"}',
        }
    }
    result, rows, requests, _, journal = run_fixture(
        tmp_path,
        runtime,
        responses=[None, Response([]), Response([])],
        usage_override={"_wire_tool_calls": [wire]},
    )
    assert not result["interrupted"] and len(requests) == 3
    call = rows[0].calls[0]
    assert call.audit_origin == "wire-only" and call.disposition == "hard-blocked"
    assert call.original_request_sha256 == digest("ImaginaryResource?private=value")
    assert call.tool_structure_sha256 == digest(json_bytes(wire))
    assert "private=value" not in journal.read_text()


def test_non_utf8_tool_arguments_are_retained_as_structural_hash(runtime):
    raw = "\ud800"
    audit = call_audit(tool(raw), 0, runtime)
    assert audit.arguments_sha256 == digest(json_bytes(raw))
    assert audit.blocker_codes == ["invalid-arguments-encoding"]


def test_synthetic_manifest_status_support_receives_transformed_label_and_rule_hash():
    patient = "synthetic-dev"
    runtime = R1RecoveryRuntime.from_resources(
        [
            {
                "resourceType": "Observation",
                "id": "synthetic",
                "status": "final",
                "subject": {"reference": "Patient/" + patient},
            }
        ],
        role="calibration",
        development_patient_digests=frozenset({digest(patient)}),
        synthetic_qualification=True,
    )
    query = "Observation?patient=" + patient + "&status=final"
    pattern = normalize_relative_fhir_get(query).pattern
    identity = digest(pattern)
    runtime = replace(
        runtime,
        source_entries={identity: {"safe_pattern": pattern, "source_pattern_sha256": identity}},
    )
    audit = call_audit(
        tool(json.dumps({"query_string": "Observation?patient=" + patient + "&status=final"})),
        0,
        runtime,
    )
    assert not audit.blocker_codes and audit.disposition == "qualified-pass-through"
    assert audit.runtime_support_changed and audit.label == "recovery-transformed"
    manifest = json.loads((ROOT / "registry/study1_sg000030_r1_manifest.json").read_bytes())
    pair = next(
        p for p in manifest["new_resource_parameter_pairs"] if p["resource"] == "Observation"
    )
    assert audit.runtime_support_rule_sha256s == [digest(json_bytes(pair))]
    assert not audit.recovery_transformed and audit.returned_resource_count == 1
    assert audit.synthetic_qualification is True


def test_sdk_qualification_cannot_be_reused_after_source_change(tmp_path):
    report_path = "registry/study1_sg000031_sdk_qualification.json"
    report = json.loads((ROOT / report_path).read_bytes())
    for path in [report_path, *report["source_hashes"], "tools/qualify_sg000031_sdk.py"]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    verify_sdk_qualification(tmp_path)
    with (tmp_path / "scripts/study1_sg000031_r2_runner.py").open("ab") as handle:
        handle.write(b"\n# synthetic source drift\n")
    with pytest.raises(ValueError, match="source binding drift"):
        verify_sdk_qualification(tmp_path)


@pytest.mark.parametrize(("ref", "attempt"), [("refs/heads/main", "2"), ("refs/heads/other", "1")])
def test_rerun_or_non_main_is_rejected_before_any_model_integration(
    runner, monkeypatch, ref, attempt
):
    admission = importlib.import_module("study1_sg000031_r2_admission")
    monkeypatch.setenv("GITHUB_REPOSITORY", "TheHalfMoon/DAL")
    monkeypatch.setenv("GITHUB_REF", ref)
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", attempt)
    with pytest.raises(ValueError, match="main-only first-run"):
        admission.environment_guard()


def test_aggregation_retains_available_partial_journal_without_shard_audit(
    tmp_path, runtime, runner, monkeypatch
):
    # Isolate journal recovery; custodian validation is covered by the unchanged custodian tests.
    _, rows, _, _, journal = run_fixture(tmp_path, runtime, raise_at=1)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    lines = journal.read_bytes().splitlines(keepends=True)
    for shard in range(8):
        selected = [
            line
            for line in lines
            if int(json.loads(line)["question_id_sha256"][:16], 16) % 8 == shard
        ]
        if selected:
            (evidence / f"shard-{shard}-journal.jsonl").write_bytes(b"".join(selected))
    module = importlib.import_module("study1_sg000031_r2_aggregate")
    plan = {
        "custodian_audit": {},
        "rows": [row.model_dump() for row in planned_rows(fixture_inputs())],
    }
    custody = SimpleNamespace(selected_rows=1463, model_dump=lambda **_: {})
    monkeypatch.setattr(
        module, "DevelopmentTraceAudit", SimpleNamespace(model_validate=lambda _: custody)
    )
    monkeypatch.setattr(module, "verify_claim", lambda _: {"engineering_qualified": True})
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_SHA", "f" * 40)

    def git_bytes(*args):
        if args[0] == "show":
            return json_bytes(plan)
        if args[0] == "ls-tree":
            return b""
        return ("f" * 40).encode()

    monkeypatch.setattr(module, "git_bytes", git_bytes)
    output = tmp_path / "output"
    module.aggregate(
        SimpleNamespace(claim_sha="synthetic-claim", input_dir=evidence, output_dir=output)
    )
    saved = R2Row.model_validate_json(
        (output / "rows" / f"{rows[0].question_id_sha256}.json").read_bytes()
    )
    assert saved.generation_attempts == 1 and saved.blocker_codes == ["experiment-exception-stop"]
    report = json.loads((output / "r2-report.json").read_bytes())
    assert report["scientific_state"] == "BLOCKED" and report["interrupted"]
    assert report["completed_rows"] == 1 and report["unfinished_rows"] == 2
