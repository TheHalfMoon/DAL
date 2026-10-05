"""Synthetic localhost HTTP fixture; does not load or infer with any model."""

import argparse
import contextlib
import importlib.metadata
import io
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def main():
    REPO = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream_root.resolve()
    revision = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != "bbb42909a5a7eb907d1cd91f72a560729e7037ea":
        raise ValueError("frozen upstream revision mismatch")

    sys.path.insert(0, str(REPO / "scripts"))
    from study1_sg000031_r2_runner import HttpGenerationGuard, configure_sdk

    from gaxbench.study1_recovery_execution import BASE_URL, MODEL, digest, json_bytes

    os.environ["OPENAI_API_KEY"] = "dal-local-query-trace-gate"
    os.environ["GEMINI_API_KEY"] = "dal-unused-synthetic-provider"
    sys.path.insert(0, str(upstream))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import httpx
        import litellm
        from agent.single_turn_request_agent import SingleTurnRequestAgent
        from utils import safe_llm_call
        from utils.core_utils import count_tokens_in_messages

    state = {"status": 200, "posts": 0}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            state["posts"] += 1
            self.rfile.read(int(self.headers["Content-Length"]))
            if state["status"] == 200:
                value = {
                    "id": "synthetic-http-fixture",
                    "object": "chat.completion",
                    "created": 0,
                    "model": MODEL,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "synthetic",
                                        "type": "function",
                                        "function": {
                                            "name": "fhir_request_get",
                                            "arguments": json.dumps(
                                                {"query_string": "Patient/DAL-SYNTHETIC-ONLY"}
                                            ),
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
            else:
                value = {
                    "error": {
                        "message": "synthetic fixture error",
                        "type": "exceed_context_size_error"
                        if state["status"] == 400
                        else "server_error",
                        "code": state["status"],
                    }
                }
            payload = json_bytes(value)
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = HTTPServer(("127.0.0.1", 8080), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    agent = SingleTurnRequestAgent(model=MODEL, verbose=False, base_url=BASE_URL)
    messages = [
        *agent.system_msg,
        {"role": "user", "content": "Synthetic transport fixture. No benchmark content."},
    ]
    tools = agent.tools
    assert count_tokens_in_messages(messages) < 32000
    guard = HttpGenerationGuard()
    guard.expected_messages, guard.expected_tools = messages, tools
    client = configure_sdk(litellm, guard, httpx)
    cases = []
    try:
        for status in (200, 500, 400):
            state.update(status=status, posts=0)
            admitted = []

            def once(sha, admitted=admitted):
                if admitted:
                    raise RuntimeError("second synthetic HTTP POST forbidden")
                admitted.append(sha)

            guard.install(once)
            guard.active = True
            try:
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    output, error, usage = safe_llm_call(
                        model=MODEL,
                        messages=messages,
                        tools=tools,
                        temperature=0.0,
                        base_url=BASE_URL,
                        max_retries=1,
                    )
                if status == 200:
                    assert output is not None and error is None and len(output.tool_calls) == 1
                else:
                    assert output is None and error is not None
            finally:
                guard.active = False
            assert state["posts"] == len(admitted) == 1, (status, state["posts"], len(admitted))
            assert not guard.guard_failed
            assert guard.wire_http_status == status and guard.wire_response_sha256
            if status == 400:
                assert guard.wire_error_type == "exceed_context_size_error"
            cases.append(
                {
                    "HTTP_status": status,
                    "HTTP_posts_received": state["posts"],
                    "wire_admissions": len(admitted),
                    "error_returned": error is not None,
                    "wire_response_sha256": guard.wire_response_sha256,
                    "wire_request_sha256": admitted[0],
                }
            )
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join()

    constraints = (
        (REPO / "registry/study1_sg000031_producer_constraints.txt").read_text().splitlines()
    )
    versions = {
        name: importlib.metadata.version(name)
        for pin in constraints
        for name, expected in [pin.split("==")]
    }
    assert all(
        versions[name] == expected for pin in constraints for name, expected in [pin.split("==")]
    )
    report = {
        "schema_version": "study1-r2-synthetic-SDK-qualification-v1",
        "state": "PASS",
        "synthetic_HTTP_server_only": True,
        "model_inference_performed": False,
        "benchmark_source_or_final_content_accessed": False,
        "founder_cost": 0.0,
        "cases": cases,
        "resolved_dependencies_verified": versions,
        "original_dependency_source_job": 111299460161,
        "constraints_sha256": digest(
            (REPO / "registry/study1_sg000031_producer_constraints.txt").read_bytes()
        ),
        "qualification_source_sha256": digest(Path(__file__).read_bytes().replace(b"\r\n", b"\n")),
        "source_hashes": {
            path: digest((REPO / path).read_bytes().replace(b"\r\n", b"\n"))
            for path in [
                "scripts/study1_sg000031_r2_runner.py",
                "src/gaxbench/study1_recovery_execution.py",
            ]
        },
        "upstream_revision": revision,
        "patched_core_sha256": digest((upstream / "utils/core_utils.py").read_bytes()),
        "system_prompt_sha256": digest(json_bytes(agent.system_msg)),
        "tool_schema_sha256": digest(json_bytes(agent.tools)),
        "claim_limit": (
            "Transport/retry implementation qualification only; "
            "no study result or model-generation evidence."
        ),
    }
    assert (
        report["patched_core_sha256"]
        == "9dcbe56df002e8e30c28cc171dd47db687aa6760e5fc798aaa2dc5dc1d9803da"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, sort_keys=True, indent=2) + "\n").encode())
    print(
        json.dumps(
            {
                "synthetic_SDK_qualification": "PASS",
                "HTTP_fixture_cases": len(cases),
                "resolved_dependencies_verified": len(versions),
                "model_inference_performed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
