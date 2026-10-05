"""R2 accounting around the immutable R1 runtime; never scores benchmark answers."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import os
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gaxbench.study1_fhir_compat import parse_relative_fhir_get
from gaxbench.study1_query_trace_evidence import is_safe_reason, safe_reason
from gaxbench.study1_query_trace_gate import DevelopmentTraceInput, normalize_relative_fhir_get
from gaxbench.study1_recovery_runtime import (
    R1_RUNTIME_VERSION,
    SOURCE_EVIDENCE_SHA256,
    R1RecoveryRuntime,
)

R1_MAIN = "ef9102ea3afda800e3fc25d38072b9e18fd3f9af"
R1_TREE = "fd6e40177425f64bb633f1aadddf0812a16f6c7d"
R1_MANIFEST_SHA256 = "220c676df241d8dc1ac8ccd83e81d54554e7618fc5acf016eaa32ec6302ca2b0"
POPULATION_SHA256 = "0755fcb62129037e05557d73863574b399503458b48b2c5a906546575aa1679f"
MODEL = "Qwen/Qwen3-4B-Instruct-2507"
BASE_URL = "http://127.0.0.1:8080/v1"
ROLE_COUNTS = {"calibration": 341, "validation": 1122}
ATTEMPT_REF = "tags/dal-r2-issue158-attempt1"
MANIFEST_PATH = "registry/study1_sg000030_r1_manifest.json"
CONTRACT_PATH = "registry/study1_sg000031_r2_contract.json"
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
AuditCode = Annotated[
    str, Field(pattern=r"^(?:[a-z][a-z0-9-]{0,95}|opaque-reason-sha256:[0-9a-f]{64})$")
]
Rule = Literal["empty-parameter-handling", "comparison-modifier-to-value-prefix"]
PROTOCOL_SHA = "d2301bbd204febe57c036274564a651b8391c5736e6d92f95799a8ee6ed4de23"
FREEZE_SHA = "2dc7159d84772aeb775e605e6bbaf79187ce3293331764a6f9f2fc9e66feeec5"
CORRECTION_SHA = "9db5001c1aa6662aae8bff98c644da69bafba12bf73ed5f7c2458ec98a157879"
PATCH_SHA = "ef9c657ca666a1a6a9e7f21c79afe1da9e30ed4a30b879ecc6fb2af00db5d757"
RUNTIME_MANIFEST_SHA = "744cc639e0d9f703869846636263d5e1d77c73c1c68d68aebd6d7d4a5485d57e"
FIXED_CONTROLS = {
    "registry/study1_sg000029_recovery_protocol.json": PROTOCOL_SHA,
    "registry/study1_sg000027_trace_producer_freeze.json": FREEZE_SHA,
    "registry/study1_sg000028_trace_producer_provenance_correction.json": CORRECTION_SHA,
    "patches/study1_fhir_agentbench_qwen_structured_tool_calls.patch": PATCH_SHA,
    "registry/study1_sg000026_fhir_runtime_manifest.json": RUNTIME_MANIFEST_SHA,
}


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def lf_digest(path: Path) -> str:
    return digest(path.read_bytes().replace(b"\r\n", b"\n"))


def population_digest(rows: Sequence[R2Row]) -> str:
    identities = sorted((row.question_id_sha256, row.role) for row in rows)
    return digest(json.dumps(identities, separators=(",", ":")))


def verify_sdk_qualification(root: Path) -> dict[str, Any]:
    report: dict[str, Any] = json.loads(
        (root / "registry/study1_sg000031_sdk_qualification.json").read_bytes()
    )
    if (
        report["state"] != "PASS"
        or report["model_inference_performed"] is not False
        or report["synthetic_HTTP_server_only"] is not True
        or report["founder_cost"] != 0.0
        or len(report["resolved_dependencies_verified"]) != 63
    ):
        raise ValueError("synthetic SDK qualification incomplete")
    sources = {
        **report["source_hashes"],
        "tools/qualify_sg000031_sdk.py": report["qualification_source_sha256"],
    }
    if set(sources) != {
        "scripts/study1_sg000031_r2_runner.py",
        "src/gaxbench/study1_recovery_execution.py",
        "tools/qualify_sg000031_sdk.py",
    }:
        raise ValueError("SDK source qualification inventory incomplete")
    for path, sha in sources.items():
        if lf_digest(root / path) != sha:
            raise ValueError("synthetic SDK qualification source binding drift")
    if [case["HTTP_status"] for case in report["cases"]] != [200, 500, 400]:
        raise ValueError("SDK synthetic error coverage incomplete")
    if any(
        case["HTTP_posts_received"] != 1 or case["wire_admissions"] != 1 for case in report["cases"]
    ):
        raise ValueError("SDK synthetic single-generation qualification failed")
    return report


def verify_frozen_controls(root: Path) -> dict[str, Any]:
    """Verify R1 and the historical producer, including the corrected provenance overlay."""
    if lf_digest(root / MANIFEST_PATH) != R1_MANIFEST_SHA256:
        raise ValueError("R1 manifest drift")
    manifest = json.loads((root / MANIFEST_PATH).read_bytes())
    expected = {
        **manifest["bound_files"],
        **FIXED_CONTROLS,
        manifest["source_evidence"]["path"]: SOURCE_EVIDENCE_SHA256,
    }
    contract: dict[str, Any] = json.loads((root / CONTRACT_PATH).read_bytes())
    if contract["canonical_r1"] != {
        "main": R1_MAIN,
        "tree": R1_TREE,
        "manifest_sha256": R1_MANIFEST_SHA256,
    }:
        raise ValueError("R1 authorization binding drift")
    if any(contract["immutable_files"].get(path) != sha for path, sha in expected.items()):
        raise ValueError("immutable control inventory drift")
    for path, sha in contract["immutable_files"].items():
        if lf_digest(root / path) != sha:
            raise ValueError("immutable control digest mismatch")
    old = json.loads((root / "registry/study1_sg000028_contract.json").read_bytes())
    if contract["producer"] != old["trace_producer"]:
        raise ValueError("producer identity drift")
    constraints = contract["producer_constraints"]
    if (
        constraints["source_run"] != 37156028113
        or constraints["source_job"] != 111299460161
        or constraints["resolved_dependencies"] != 63
        or lf_digest(root / constraints["path"]) != constraints["sha256"]
    ):
        raise ValueError("original resolved producer dependency identity drift")
    auth = root / "registry/study1_sg000031_founder_authorization.json"
    if lf_digest(auth) != contract["authorization_record_sha256"]:
        raise ValueError("authorization record digest mismatch")
    authorization = json.loads(auth.read_bytes())
    if authorization["source_kind"] != "direct-human-founder-message-in-Codex":
        raise ValueError("authorization source drift")
    if digest(authorization["statement"]) != authorization["statement_sha256"]:
        raise ValueError("authorization statement digest mismatch")
    if contract["execution"] != {
        "main_only": True,
        "workflow_dispatch_only": True,
        "attempts": 1,
        "first_turn_generations_per_row": 1,
        "safe_llm_call_max_retries": 1,
        "sdk_retries": 0,
        "shards": 8,
        "sequential_shards": True,
        "second_turn_reasoning": False,
        "answer_correctness_scored": False,
        "final_role_access": False,
        "D4": False,
        "training": False,
        "zero_founder_cost": True,
    }:
        raise ValueError("R2 execution boundary drift")
    verify_sdk_qualification(root)
    return contract


class AuditModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    @field_validator("blocker_codes", check_fields=False)
    @classmethod
    def finite_codes(cls, values: list[str]) -> list[str]:
        own = {
            "out-of-manifest-pattern",
            "inference-failed-stop",
            "experiment-exception-stop",
            "generation-transport-accounting-failed-stop",
            "sdk-cost-accounting-failed-stop",
            "invalid-query-encoding",
            "invalid-arguments-encoding",
            "inference-failed-row",
        }
        if any(value not in own and not is_safe_reason(value) for value in values):
            raise ValueError("blocker codes must use the finite vocabulary or opaque identities")
        return values


class R2Call(AuditModel):
    ordinal: int = Field(ge=0)
    audit_origin: Literal["frozen-helper", "wire-only"] = "frozen-helper"
    tool_structure_sha256: SHA256 | None = None
    arguments_sha256: SHA256 | None = None
    original_request_sha256: SHA256 | None = None
    observed_pattern_sha256: SHA256 | None = None
    source_pattern_sha256: SHA256 | None = None
    disposition: Literal["qualified-pass-through", "recovery-transformed", "hard-blocked"]
    recovery_transformed: bool = False
    runtime_support_changed: bool = False
    runtime_support_rule_sha256s: list[SHA256] = Field(default_factory=list)
    label: Literal["recovery-transformed"] | None = None
    transformation_rule_ids: list[Rule] = Field(default_factory=list)
    blocker_codes: list[AuditCode] = Field(default_factory=list)
    returned_resource_count: int = Field(default=0, ge=0)
    synthetic_qualification: bool = False

    @model_validator(mode="after")
    def complete_call(self) -> R2Call:
        if self.recovery_transformed != bool(self.transformation_rule_ids):
            raise ValueError("transformation accounting mismatch")
        if self.runtime_support_changed != bool(self.runtime_support_rule_sha256s):
            raise ValueError("manifest runtime support accounting mismatch")
        if self.runtime_support_changed and self.disposition == "hard-blocked":
            raise ValueError("unexecuted blocked requests cannot claim recovered runtime support")
        if (self.label == "recovery-transformed") != (
            self.recovery_transformed or self.runtime_support_changed
        ):
            raise ValueError("transformed request requires explicit label")
        if (self.disposition == "hard-blocked") != bool(self.blocker_codes):
            raise ValueError("call blocker disposition mismatch")
        if self.disposition != "hard-blocked":
            if self.original_request_sha256 is None or self.source_pattern_sha256 is None:
                raise ValueError("passing call requires original and source lineage")
            if self.observed_pattern_sha256 != self.source_pattern_sha256:
                raise ValueError("passing call requires exact source identity")
            if (self.disposition == "recovery-transformed") != self.recovery_transformed:
                raise ValueError("passing transformation disposition mismatch")
        return self


class R2Row(AuditModel):
    schema_version: Literal["study1-r2-row-v1"] = "study1-r2-row-v1"
    role: Literal["calibration", "validation"]
    question_id_sha256: SHA256
    input_sha256: SHA256
    original_evidence_sha256: SHA256 = SOURCE_EVIDENCE_SHA256
    r1_manifest_sha256: SHA256 = R1_MANIFEST_SHA256
    runtime_version: Literal["sg000030-r1-g2-v1"] = "sg000030-r1-g2-v1"
    status: Literal["not-attempted", "in-flight", "pass", "behavior-changing-blocker"] = (
        "not-attempted"
    )
    generation_attempts: Literal[0, 1] = 0
    http_post_admissions: Literal[0, 1] = 0
    producer_request_sha256: SHA256 | None = None
    wire_request_sha256: SHA256 | None = None
    wire_response_sha256: SHA256 | None = None
    wire_http_status: int | None = Field(default=None, ge=100, le=599)
    wire_tool_calls_available: bool = False
    wire_tool_call_sha256s: list[SHA256] = Field(default_factory=list)
    response_sha256: SHA256 | None = None
    error_sha256: SHA256 | None = None
    tool_schema_sha256: SHA256 | None = None
    system_prompt_sha256: SHA256 | None = None
    tool_call_count: int = Field(default=0, ge=0)
    calls: list[R2Call] = Field(default_factory=list)
    blocker_codes: list[AuditCode] = Field(default_factory=list)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost: float | None = None
    sdk_reported_cost: float | None = None
    cost_basis: Literal["public-hosted-CPU-local-llama-no-paid-provider"] = (
        "public-hosted-CPU-local-llama-no-paid-provider"
    )
    final_rows_materialized: Literal[0] = 0
    final_question_content_accessed: Literal[False] = False
    second_turn_reasoning_executed: Literal[False] = False
    answer_correctness_scored: Literal[False] = False

    @model_validator(mode="after")
    def complete_row(self) -> R2Row:
        if (
            self.original_evidence_sha256 != SOURCE_EVIDENCE_SHA256
            or self.r1_manifest_sha256 != R1_MANIFEST_SHA256
        ):
            raise ValueError("immutable lineage drift")
        if self.http_post_admissions > self.generation_attempts:
            raise ValueError("HTTP generation without row admission")
        if self.http_post_admissions and self.wire_request_sha256 is None:
            raise ValueError("HTTP generation requires immutable wire request identity")
        if self.cost is not None and (not math.isfinite(self.cost) or self.cost < 0):
            raise ValueError("invalid cost accounting")
        if self.cost not in {None, 0.0}:
            raise ValueError("only zero founder cost is authorized")
        if len(self.calls) != self.tool_call_count:
            raise ValueError("every observed tool call requires disposition")
        if [call.ordinal for call in self.calls] != list(range(self.tool_call_count)):
            raise ValueError("call ordinals must close")
        if self.status == "not-attempted" and self.generation_attempts != 0:
            raise ValueError("unattempted row cannot have a generation")
        if self.status != "not-attempted" and self.generation_attempts != 1:
            raise ValueError("attempted row requires exactly one generation admission")
        if self.generation_attempts and any(
            value is None
            for value in (
                self.producer_request_sha256,
                self.tool_schema_sha256,
                self.system_prompt_sha256,
            )
        ):
            raise ValueError("attempted row requires frozen producer request identity")
        if self.status == "pass":
            if (
                self.blocker_codes
                or not self.calls
                or self.cost != 0.0
                or not self.response_sha256
                or self.http_post_admissions != 1
                or not self.wire_response_sha256
                or self.wire_http_status != 200
            ):
                raise ValueError("passing row must have complete zero-cost response accounting")
            if any(call.blocker_codes or call.synthetic_qualification for call in self.calls):
                raise ValueError("passing row cannot omit blocked or synthetic calls")
        if self.status == "behavior-changing-blocker" and not self.blocker_codes:
            raise ValueError("blocked row requires blockers")
        return self


def planned_rows(inputs: Sequence[DevelopmentTraceInput]) -> list[R2Row]:
    return [
        R2Row(
            role=item.role,
            question_id_sha256=item.question_id_sha256,
            input_sha256=digest(item.input_text),
        )
        for item in inputs
    ]


def write_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(json_bytes(value))
        handle.flush()
        os.fsync(handle.fileno())


class RowJournal:
    """An exclusive, fsync'd event log. There is deliberately no resume/replay path."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open("xb")

    def append(self, row: R2Row) -> None:
        self.handle.write(json_bytes(row.model_dump(mode="json")))
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self) -> None:
        self.handle.close()


def call_audit(
    call: Any, ordinal: int, runtime: R1RecoveryRuntime, *, execute: bool = True
) -> R2Call:
    function = getattr(call, "function", None)
    structure = (
        call.model_dump(mode="json")
        if hasattr(call, "model_dump")
        else {
            "function": {
                "name": getattr(function, "name", None),
                "arguments": getattr(function, "arguments", None),
            }
        }
    )
    audit = _call_audit(call, ordinal, runtime, execute=execute)
    return R2Call.model_validate(
        {**audit.model_dump(), "tool_structure_sha256": digest(json_bytes(structure))}
    )


def _call_audit(
    call: Any, ordinal: int, runtime: R1RecoveryRuntime, *, execute: bool = True
) -> R2Call:
    function = getattr(call, "function", None)
    raw = getattr(function, "arguments", None)
    try:
        args_sha = digest(raw) if isinstance(raw, str) else digest(json_bytes(raw))
    except UnicodeEncodeError:
        return R2Call(
            ordinal=ordinal,
            arguments_sha256=digest(json_bytes(raw)),
            disposition="hard-blocked",
            blocker_codes=["invalid-arguments-encoding"],
        )
    code: str | None = None
    if getattr(function, "name", None) != "fhir_request_get":
        code = "unexpected-tool-name"
    elif not isinstance(raw, str):
        code = "malformed-tool-arguments"
    else:
        try:
            arguments = json.loads(raw)
        except (ValueError, TypeError):
            arguments = None
        if not isinstance(arguments, dict):
            code = "malformed-tool-arguments"
        else:
            query = arguments.get("query_string")
            if not isinstance(query, str) or not query:
                code = "missing-query-string"
            else:
                try:
                    request_sha = digest(query)
                except UnicodeEncodeError:
                    return R2Call(
                        ordinal=ordinal,
                        arguments_sha256=args_sha,
                        disposition="hard-blocked",
                        blocker_codes=["invalid-query-encoding"],
                    )
                normalized = normalize_relative_fhir_get(query)
                observed_sha = digest(normalized.pattern)
                source = runtime.source_entries.get(observed_sha)
                if not execute:
                    return R2Call(
                        ordinal=ordinal,
                        arguments_sha256=args_sha,
                        original_request_sha256=request_sha,
                        observed_pattern_sha256=observed_sha,
                        source_pattern_sha256=source["source_pattern_sha256"] if source else None,
                        disposition="hard-blocked",
                        blocker_codes=["inference-failed-row"],
                    )
                if source is None:
                    return R2Call(
                        ordinal=ordinal,
                        arguments_sha256=args_sha,
                        original_request_sha256=request_sha,
                        observed_pattern_sha256=observed_sha,
                        disposition="hard-blocked",
                        blocker_codes=["out-of-manifest-pattern"],
                    )
                try:
                    exercise = runtime.exercise(query, source_entry=source)
                except (TypeError, ValueError):
                    return R2Call(
                        ordinal=ordinal,
                        arguments_sha256=args_sha,
                        original_request_sha256=request_sha,
                        observed_pattern_sha256=observed_sha,
                        source_pattern_sha256=source["source_pattern_sha256"],
                        disposition="hard-blocked",
                        blocker_codes=["query-exercise-exception"],
                    )
                support_rules = []
                if exercise.disposition != "hard-blocked":
                    request = parse_relative_fhir_get(query, role=runtime.role)
                    if any(p.name == "status" and p.value for p in request.parameters):
                        manifest = json.loads(
                            (Path(__file__).resolve().parents[2] / MANIFEST_PATH).read_bytes()
                        )
                        support_rules = [
                            digest(json_bytes(pair))
                            for pair in manifest["new_resource_parameter_pairs"]
                            if pair["resource"] == request.resource_type
                            and pair["parameter"] == "status"
                        ]
                        if len(support_rules) != 1:
                            raise ValueError("R1 manifest support identity mismatch")
                return R2Call.model_validate(
                    {
                        "ordinal": ordinal,
                        "arguments_sha256": args_sha,
                        "original_request_sha256": exercise.original_request_sha256,
                        "observed_pattern_sha256": observed_sha,
                        "source_pattern_sha256": source["source_pattern_sha256"],
                        "disposition": exercise.disposition,
                        "recovery_transformed": exercise.recovery_transformed,
                        "runtime_support_changed": bool(support_rules),
                        "runtime_support_rule_sha256s": support_rules,
                        "label": "recovery-transformed"
                        if exercise.recovery_transformed or support_rules
                        else None,
                        "transformation_rule_ids": list(exercise.transformation_rule_ids),
                        "blocker_codes": sorted(
                            {safe_reason(code) for code in exercise.blocker_codes}
                        ),
                        "returned_resource_count": exercise.returned_resource_count,
                        "synthetic_qualification": exercise.synthetic_qualification,
                    }
                )
    assert code is not None
    return R2Call(
        ordinal=ordinal, arguments_sha256=args_sha, disposition="hard-blocked", blocker_codes=[code]
    )


def run_rows(
    inputs: Sequence[DevelopmentTraceInput],
    *,
    runtimes: Mapping[str, R1RecoveryRuntime],
    first_turn: Callable[..., Any],
    system_messages: list[dict[str, Any]],
    tools: Any,
    journal_path: Path,
    before_call: Callable[[], None],
    install_post_guard: Callable[[Callable[[str], None]], None],
    zero_cost_infrastructure_verified: bool,
    durable_checkpoint: Callable[[R2Row], None],
) -> dict[str, Any]:
    """Run each selected row once, retaining a checkpoint before every admitted generation."""
    if not zero_cost_infrastructure_verified:
        raise ValueError("zero-cost infrastructure qualification is required before inference")
    rows = planned_rows(inputs)
    journal = RowJournal(journal_path)
    interrupted = False
    fatal_code: str | None = None
    try:
        for row in rows:
            journal.append(row)
        for item, row in zip(inputs, rows, strict=True):
            try:
                before_call()
            except Exception:
                interrupted, fatal_code = True, "execution-admission-lost"
                break
            messages = [*system_messages, {"role": "user", "content": item.input_text}]
            row = R2Row.model_validate(
                {
                    **row.model_dump(),
                    "status": "in-flight",
                    "generation_attempts": 1,
                    "producer_request_sha256": digest(
                        json_bytes(
                            {
                                "messages": messages,
                                "tools": tools,
                                "model": MODEL,
                                "temperature": 0.0,
                                "base_url": BASE_URL,
                            }
                        )
                    ),
                    "system_prompt_sha256": digest(json_bytes(system_messages)),
                    "tool_schema_sha256": digest(json_bytes(tools)),
                }
            )
            journal.append(row)

            def admit_http_post(wire_sha256: str) -> None:
                nonlocal row
                if row.http_post_admissions:
                    raise RuntimeError("a second HTTP generation is forbidden")
                before_call()
                row = R2Row.model_validate(
                    {
                        **row.model_dump(),
                        "http_post_admissions": 1,
                        "wire_request_sha256": wire_sha256,
                    }
                )
                journal.append(row)
                durable_checkpoint(row)

            install_post_guard(admit_http_post)
            # Exceptions/logs can contain query literals. Only fixed codes and hashes survive.
            try:
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    response, error, usage = first_turn(
                        model=MODEL,
                        messages=messages,
                        tools=tools,
                        temperature=0.0,
                        base_url=BASE_URL,
                        max_retries=1,
                    )
                usage = usage if isinstance(usage, dict) else {}
                row = R2Row.model_validate(
                    {
                        **row.model_dump(),
                        "wire_response_sha256": usage.get("_wire_response_sha256"),
                        "wire_http_status": usage.get("_wire_http_status"),
                        "wire_tool_calls_available": usage.get("_wire_tool_calls_available", False),
                        "wire_tool_call_sha256s": usage.get("_wire_tool_call_sha256s", []),
                    }
                )
                if response is not None:
                    row = R2Row.model_validate(
                        {
                            **row.model_dump(),
                            "response_sha256": digest(json_bytes(response.model_dump(mode="json"))),
                        }
                    )
                codes: list[str] = []
                guard_failed = bool(usage.get("_guard_failed"))
                failed = error is not None or response is None
                row_failure = (
                    failed
                    and not guard_failed
                    and (
                        (row.http_post_admissions == 1 and usage.get("_wire_http_status") == 200)
                        or (
                            row.http_post_admissions == 1
                            and usage.get("_wire_http_status") == 400
                            and usage.get("_wire_error_type") == "exceed_context_size_error"
                        )
                        or (
                            row.http_post_admissions == 0
                            and usage.get("_frozen_preflight_rejected") is True
                        )
                    )
                )
                if failed or guard_failed or usage.get("_wire_http_status") != 200:
                    code = "inference-failed-row" if row_failure else "inference-failed-stop"
                    codes.append(code)
                    if not row_failure:
                        interrupted, fatal_code = True, code
                calls = list(getattr(response, "tool_calls", None) or []) if response else []
                if row.http_post_admissions != 1 and not row_failure:
                    codes.append("generation-transport-accounting-failed-stop")
                    interrupted, fatal_code = True, "generation-transport-accounting-failed-stop"
                if not calls:
                    codes.append("no-tool-call")
                audits = [
                    call_audit(call, i, runtimes[item.role])
                    for i, call in enumerate(calls)
                    if not failed
                ]
                if failed:
                    audits = []
                    wire_calls = usage.get("_wire_tool_calls", [])
                    for i, wire_call in enumerate(wire_calls):
                        function = (
                            wire_call.get("function", {}) if isinstance(wire_call, dict) else {}
                        )
                        if not isinstance(function, dict):
                            function = {}
                        audit = call_audit(
                            SimpleNamespace(
                                function=SimpleNamespace(
                                    name=function.get("name"), arguments=function.get("arguments")
                                )
                            ),
                            i,
                            runtimes[item.role],
                            execute=False,
                        )
                        audits.append(
                            R2Call.model_validate(
                                {
                                    **audit.model_dump(),
                                    "audit_origin": "wire-only",
                                    "tool_structure_sha256": digest(json_bytes(wire_call)),
                                    "blocker_codes": sorted(
                                        set([*audit.blocker_codes, "inference-failed-row"])
                                    ),
                                }
                            )
                        )
                codes.extend(code for call in audits for code in call.blocker_codes)
                if "query-exercise-exception" in codes:
                    interrupted, fatal_code = True, "query-exercise-exception"
                sdk_cost = usage.get("cost")
                if sdk_cost is not None and (
                    isinstance(sdk_cost, bool)
                    or not isinstance(sdk_cost, (float, int))
                    or not math.isfinite(sdk_cost)
                    or sdk_cost < 0
                ):
                    codes.append("sdk-cost-accounting-failed-stop")
                    interrupted, fatal_code = True, "sdk-cost-accounting-failed-stop"
                    sdk_cost = None
                data = {
                    **row.model_dump(),
                    "status": "behavior-changing-blocker" if codes else "pass",
                    "calls": [call.model_dump() for call in audits],
                    "tool_call_count": len(audits),
                    "blocker_codes": sorted(set(codes)),
                    # SDK model-price estimates are not bills from the qualified local substrate.
                    "cost": 0.0,
                    "sdk_reported_cost": float(sdk_cost) if sdk_cost is not None else None,
                    "wire_response_sha256": usage.get("_wire_response_sha256"),
                    "wire_http_status": usage.get("_wire_http_status"),
                    "wire_tool_calls_available": usage.get("_wire_tool_calls_available", False),
                    "wire_tool_call_sha256s": usage.get("_wire_tool_call_sha256s", []),
                    "response_sha256": digest(json_bytes(response.model_dump(mode="json")))
                    if response is not None
                    else None,
                    "error_sha256": digest(str(error)) if error is not None else None,
                }
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    value = usage.get(key)
                    data[key] = value if type(value) is int and value >= 0 else 0
                row = R2Row.model_validate(data)
            except Exception as error:
                row = R2Row.model_validate(
                    {
                        **row.model_dump(),
                        "status": "behavior-changing-blocker",
                        "blocker_codes": ["experiment-exception-stop"],
                        "error_sha256": digest(str(error)),
                        "cost": 0.0,
                    }
                )
                interrupted, fatal_code = True, "experiment-exception-stop"
            journal.append(row)
            try:
                durable_checkpoint(row)
            except Exception:
                interrupted, fatal_code = True, "durable-checkpoint-failed-stop"
            if interrupted:
                break
    finally:
        journal.close()
    return {
        "interrupted": interrupted,
        "fatal_code": fatal_code,
        "journal_sha256": digest(journal_path.read_bytes()),
        "final_rows_materialized": 0,
        "final_question_content_accessed": False,
        "second_turn_reasoning_executed": False,
        "answer_correctness_scored": False,
    }


def read_journal(path: Path, plan: Sequence[R2Row]) -> dict[str, R2Row]:
    """Reject duplicates, replay, role drift, incomplete writes and leaked extra fields."""
    expected = {row.question_id_sha256: row for row in plan}
    latest: dict[str, R2Row] = {}
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        raise ValueError("interrupted journal write")
    for line in payload.splitlines():
        row = R2Row.model_validate_json(line)
        key = row.question_id_sha256
        if key not in expected or row.role != expected[key].role:
            raise ValueError("journal identity outside plan")
        if row.input_sha256 != expected[key].input_sha256:
            raise ValueError("journal input identity drift")
        prior = latest.get(key)
        allowed = {"not-attempted": "in-flight", "in-flight": "completed"}
        current = "completed" if row.status in {"pass", "behavior-changing-blocker"} else row.status
        if prior is None:
            if row.status != "not-attempted":
                raise ValueError("journal must start with planned row")
        elif allowed.get(prior.status) != current:
            if not (
                prior.status == row.status == "in-flight"
                and prior.http_post_admissions == 0
                and row.http_post_admissions == 1
            ):
                raise ValueError("journal generation replay or invalid transition")
        if prior is not None and prior.generation_attempts:
            if (
                row.producer_request_sha256 != prior.producer_request_sha256
                or row.http_post_admissions < prior.http_post_admissions
            ):
                raise ValueError("journal producer identity or transport accounting drift")
            if prior.http_post_admissions and row.wire_request_sha256 != prior.wire_request_sha256:
                raise ValueError("journal wire identity drift")
        latest[key] = row
    return latest


def classify_rows(
    rows: Sequence[R2Row], *, engineering_qualified: bool, interrupted: bool
) -> dict[str, Any]:
    roles = Counter(row.role for row in rows)
    statuses = Counter(row.status for row in rows)
    population_complete = (
        len(rows) == 1463
        and len({row.question_id_sha256 for row in rows}) == 1463
        and dict(roles) == ROLE_COUNTS
        and population_digest(rows) == POPULATION_SHA256
    )
    completed = sum(row.status in {"pass", "behavior-changing-blocker"} for row in rows)
    blockers = Counter(code for row in rows for code in row.blocker_codes)
    calls = [call for row in rows for call in row.calls]
    passed = (
        population_complete
        and engineering_qualified
        and not interrupted
        and statuses["pass"] == 1463
        and all(row.generation_attempts == 1 for row in rows)
    )
    return {
        "schema_version": "study1-r2-accounting-v1",
        "scientific_state": "PASS" if passed else "BLOCKED",
        "expected_rows": 1463,
        "accounted_rows": len(rows),
        "population_complete": population_complete,
        "question_role_assignments_sha256": population_digest(rows),
        "role_counts": dict(sorted(roles.items())),
        "status_counts": dict(sorted(statuses.items())),
        "completed_rows": completed,
        "generation_admissions": sum(row.generation_attempts for row in rows),
        "http_post_admissions": sum(row.http_post_admissions for row in rows),
        "unresolved_behavior_changing_blocker_rows": statuses["behavior-changing-blocker"],
        "unfinished_rows": len(rows) - completed,
        "observed_tool_calls": len(calls),
        "blocker_counts": dict(sorted(blockers.items())),
        "call_dispositions": dict(sorted(Counter(call.disposition for call in calls).items())),
        "request_transformations_accounted": sum(call.recovery_transformed for call in calls),
        "executed_recovery_transformed_calls": sum(
            call.disposition == "recovery-transformed" for call in calls
        ),
        "recovered_runtime_support_calls": sum(call.runtime_support_changed for call in calls),
        "recovery_transformed_labels": sum(call.label == "recovery-transformed" for call in calls),
        "transformation_rule_counts": dict(
            sorted(Counter(rule for call in calls for rule in call.transformation_rule_ids).items())
        ),
        "original_sg000028": {
            "scientific_state": "BLOCKED",
            "rows": 1463,
            "pass": 224,
            "blockers": 1239,
            "calls": 1623,
            "source_patterns": 248,
            "evidence_sha256": SOURCE_EVIDENCE_SHA256,
        },
        "r1_manifest_sha256": R1_MANIFEST_SHA256,
        "runtime_version": R1_RUNTIME_VERSION,
        "interrupted": interrupted,
        "new_founder_decision_required_before_new_model_attempt": interrupted,
        "engineering_qualified": engineering_qualified,
        "final_rows_materialized": 0,
        "final_question_content_accessed": False,
        "sealed_final_patients": 40,
        "sealed_final_rows": 173,
        "second_turn_reasoning_executed": False,
        "answer_correctness_scored": False,
        "D4": False,
        "training": False,
        "founder_cost": 0.0,
        "cost_accounting_complete": all(row.cost == 0.0 for row in rows if row.generation_attempts),
        "interpretation": (
            "Exposed-development recovery; no independent confirmation or final evaluation."
        ),
    }
