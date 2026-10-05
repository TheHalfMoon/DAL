"""Frozen first-turn generation and immutable R1 exercise; all other stages are forbidden."""

from __future__ import annotations

import argparse
import contextlib
import functools
import importlib.metadata
import io
import json
import os
import sys
import time
from pathlib import Path

from study1_sg000031_r2_admission import ledger_write, verify_claim

from gaxbench.study1_query_trace_gate import (
    build_development_trace_inputs,
    load_verified_gate_runtime,
)
from gaxbench.study1_recovery_execution import (
    BASE_URL,
    MODEL,
    R2Row,
    digest,
    json_bytes,
    planned_rows,
    run_rows,
    verify_frozen_controls,
    verify_sdk_qualification,
    write_exclusive,
)
from gaxbench.study1_recovery_runtime import R1RecoveryRuntime


class HttpGenerationGuard:
    """Observe the unchanged HTTP payload and reject SDK retries before transmission."""

    def __init__(self):
        self.admit = None
        self.expected_messages = None
        self.expected_tools = None
        self.active = False
        self.wire_response_sha256 = None
        self.wire_http_status = None
        self.guard_failed = False
        self.wire_error_type = None
        self.wire_tool_calls_available = False
        self.wire_tool_call_sha256s = []
        self.wire_tool_calls = []

    def install(self, admit):
        self.admit = admit
        self.wire_response_sha256 = None
        self.wire_http_status = None
        self.guard_failed = False
        self.wire_error_type = None
        self.wire_tool_calls_available = False
        self.wire_tool_call_sha256s = []
        self.wire_tool_calls = []

    def response_hook(self, response):
        if not self.active or str(response.request.url) != BASE_URL + "/chat/completions":
            self.guard_failed = True
            raise RuntimeError("unadmitted response transport")
        response.read()
        self.wire_response_sha256 = digest(response.content)
        self.wire_http_status = response.status_code
        try:
            payload = response.json()
            if response.status_code == 400:
                if payload.get("error", {}).get("type") == "exceed_context_size_error":
                    self.wire_error_type = "exceed_context_size_error"
            if response.status_code == 200:
                calls = payload["choices"][0]["message"].get("tool_calls", [])
                if isinstance(calls, list):
                    self.wire_tool_calls_available = True
                    self.wire_tool_calls = calls
                    self.wire_tool_call_sha256s = [digest(json_bytes(call)) for call in calls]
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            pass

    def hook(self, request):
        try:
            self._checked_hook(request)
        except Exception:
            self.guard_failed = True
            raise

    def _checked_hook(self, request):
        if (
            not self.active
            or request.method != "POST"
            or str(request.url) != BASE_URL + "/chat/completions"
        ):
            raise RuntimeError("generation transport outside the admitted loopback request")
        payload = json.loads(request.content)
        if (
            payload.get("model") != MODEL
            or type(payload.get("temperature")) not in {int, float}
            or payload.get("temperature") != 0.0
            or payload.get("messages") != self.expected_messages
            or payload.get("tools") != self.expected_tools
            or payload.get("stream", False) is not False
        ):
            raise RuntimeError("frozen producer wire semantics drift")
        if self.admit is None:
            raise RuntimeError("HTTP request has no row admission")
        self.admit(digest(request.content))


def configure_sdk(litellm, guard, httpx):
    # Supported SDK options only; upstream source, payload and structured-call patch stay frozen.
    litellm.num_retries = 0
    litellm.telemetry = False
    litellm.callbacks = []
    litellm.success_callback = []
    litellm.failure_callback = []
    litellm.model_fallbacks = None
    litellm.completion = functools.partial(litellm.completion, max_retries=0, num_retries=0)
    client = httpx.Client(
        transport=httpx.HTTPTransport(retries=0),
        trust_env=False,
        follow_redirects=False,
        limits=httpx.Limits(max_connections=1000, max_keepalive_connections=100),
        event_hooks={"request": [guard.hook], "response": [guard.response_hook]},
    )
    litellm.client_session = client
    return client


def run(args):
    claim = verify_claim(args.claim_sha)
    verify_frozen_controls(Path.cwd())
    qualification = verify_sdk_qualification(Path.cwd())
    for name, version in qualification["resolved_dependencies_verified"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError("frozen producer resolved dependency drift")
    if args.shard_index not in range(8):
        raise ValueError("fixed shard ownership required")
    plan = json.loads(args.plan.read_bytes())
    expected = [
        R2Row.model_validate(row)
        for row in plan["rows"]
        if int(row["question_id_sha256"][:16], 16) % 8 == args.shard_index
    ]
    inputs, audit, patient_digests = build_development_trace_inputs(
        args.source, shard_index=args.shard_index, shard_count=8
    )
    if [row.model_dump() for row in planned_rows(inputs)] != [row.model_dump() for row in expected]:
        raise ValueError("custodian input population or input identity drift")
    gate = load_verified_gate_runtime(
        args.runtime_root, args.runtime_manifest, development_patient_digests=patient_digests
    )
    runtimes = {
        role: R1RecoveryRuntime.from_resources(
            gate.identity_index.values(),
            role=role,
            development_patient_digests=patient_digests,
        )
        for role in ("calibration", "validation")
    }
    sys.path.insert(0, str(args.upstream_root))
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import httpx
            import litellm
            from agent.single_turn_request_agent import SingleTurnRequestAgent
            from utils import safe_llm_call
            from utils.core_utils import count_tokens_in_messages
    finally:
        sys.path.pop(0)
    agent = SingleTurnRequestAgent(model=MODEL, verbose=False, base_url=BASE_URL)
    if (
        digest(json_bytes(agent.system_msg)) != qualification["system_prompt_sha256"]
        or digest(json_bytes(agent.tools)) != qualification["tool_schema_sha256"]
    ):
        raise ValueError("frozen first-turn prompt or tool-schema identity drift")
    guard = HttpGenerationGuard()
    client = configure_sdk(litellm, guard, httpx)
    remote_shas = {}
    last_start = 0.0

    def before_call():
        if os.environ["GITHUB_RUN_ATTEMPT"] != "1" or os.environ["GITHUB_REF"] != "refs/heads/main":
            raise ValueError("R2 execution admission lost")

    def checkpoint(row):
        remote_shas[row.question_id_sha256] = ledger_write(
            f"rows/{row.question_id_sha256}.json",
            row.model_dump(mode="json"),
            remote_shas.get(row.question_id_sha256),
        )

    def first_turn(**kwargs):
        nonlocal last_start
        # At most 450 checkpoint writes/hour, below GitHub's content-write secondary limit.
        delay = 16.0 - (time.monotonic() - last_start)
        if delay > 0:
            time.sleep(delay)
        last_start = time.monotonic()
        guard.expected_messages = json.loads(json.dumps(kwargs["messages"]))
        guard.expected_tools = json.loads(json.dumps(kwargs["tools"]))
        guard.active = True
        try:
            response, error, usage = safe_llm_call(**kwargs)
            usage = dict(usage) if isinstance(usage, dict) else {}
            usage["_wire_response_sha256"] = guard.wire_response_sha256
            usage["_wire_http_status"] = guard.wire_http_status
            usage["_guard_failed"] = guard.guard_failed
            usage["_wire_error_type"] = guard.wire_error_type
            usage["_wire_tool_calls_available"] = guard.wire_tool_calls_available
            usage["_wire_tool_call_sha256s"] = guard.wire_tool_call_sha256s
            usage["_wire_tool_calls"] = guard.wire_tool_calls
            usage["_frozen_preflight_rejected"] = (
                response is None
                and guard.wire_http_status is None
                and count_tokens_in_messages(kwargs["messages"]) > 32000
            )
            return response, error, usage
        finally:
            guard.active = False

    try:
        result = run_rows(
            inputs,
            runtimes=runtimes,
            first_turn=first_turn,
            system_messages=agent.system_msg,
            tools=agent.tools,
            journal_path=args.output_dir / f"shard-{args.shard_index}-journal.jsonl",
            before_call=before_call,
            install_post_guard=guard.install,
            zero_cost_infrastructure_verified=claim["zero_cost_infrastructure_verified"],
            durable_checkpoint=checkpoint,
        )
    finally:
        client.close()
    write_exclusive(
        args.output_dir / f"shard-{args.shard_index}-audit.json",
        {
            "custodian_audit": audit.model_dump(mode="json"),
            **result,
            "claim_sha": args.claim_sha,
            "run_id": int(os.environ["GITHUB_RUN_ID"]),
            "main_sha": os.environ["GITHUB_SHA"],
            "durable_row_blobs": remote_shas,
        },
    )
    if result["interrupted"]:
        raise RuntimeError("R2 interrupted attempt retained; new founder decision required")
    print(f"R2_SHARD_{args.shard_index}_COMPLETED_ROWS={len(inputs)}")


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "source",
        "upstream-root",
        "runtime-root",
        "runtime-manifest",
        "output-dir",
        "plan",
    ):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--shard-index", required=True, type=int)
    parser.add_argument("--claim-sha", required=True)
    args = parser.parse_args()
    try:
        run(args)
    except Exception as error:
        write_exclusive(
            args.output_dir / f"shard-{args.shard_index}-failure.json",
            {
                "state": "BLOCKED",
                "code": "r2-experiment-or-infrastructure-failed-stop",
                "error_sha256": digest(str(error)),
                "run_id": os.environ.get("GITHUB_RUN_ID"),
                "new_founder_decision_before_new_model_attempt": True,
            },
        )
        raise SystemExit(
            "R2 failed attempt retained; no additional model-call attempt authorized"
        ) from None


if __name__ == "__main__":
    main()
