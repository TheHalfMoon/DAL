"""Versioned receipt and single-dispatch regressions; synthetic HTTP only."""

from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def grain(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.setenv("GH_TOKEN", "synthetic-attempt2-token")
    return importlib.import_module("study1_sg000031_attempt2_admission")


@pytest.fixture
def receipt(grain):
    contract = grain.load_contract(ROOT)
    runs = {
        key: index
        for index, key in enumerate(
            [
                "ci",
                "manuscript",
                "alibaba",
                "jev",
                "sdk",
                "repair_native",
                "pre_native",
                "post_ci",
                "post_manuscript",
                "post_sdk",
                "post_repair_native",
                "post_native",
            ],
            100,
        )
    }
    reviews = {
        key: {}
        for key in [
            "jev",
            "alibaba",
            "sdk",
            "repair_native",
            "pre_native",
            "post_sdk",
            "post_repair_native",
            "post_native",
        ]
    }
    return {
        **grain.binding_fields(ROOT, contract),
        "phase": "canonical",
        "base_sha": grain.REPAIR_MAIN,
        "head_sha": "a" * 40,
        "main_sha": "b" * 40,
        "tree": "c" * 40,
        "pull_request": 162,
        "runs": runs,
        "reviews": reviews,
    }


def comment(grain, receipt, *, marker=None):
    return {
        "issue_url": grain.legacy.REPOSITORY_API + "/issues/158",
        "user": {"login": "TheHalfMoon"},
        "body": (marker or grain.MARKERS["canonical"])
        + "\n```json\n"
        + json.dumps(receipt, indent=2)
        + "\n```",
    }


@pytest.mark.parametrize(
    "field",
    [
        "contract_sha256",
        "execution_authorization_sha256",
        "engineering_authorization_sha256",
        "repair_main",
        "repair_tree",
        "r1_manifest_sha256",
        "producer_identity_sha256",
        "population_sha256",
        "attempt1_lineage_sha256",
        "base_sha",
    ],
)
def test_wrong_binding_is_rejected_before_external_io(grain, receipt, monkeypatch, field):
    receipt[field] = "0" * len(receipt[field])
    monkeypatch.setattr(grain.legacy, "api", lambda *_args: pytest.fail("unexpected external I/O"))
    with pytest.raises(ValueError):
        grain.verify_qualification(ROOT, receipt)


@pytest.mark.parametrize("field", ["attempt_ordinal", "predecessor_attempt_ordinal"])
@pytest.mark.parametrize("value", [None, True, False, 1.0, 2.0, "2", 0, 3])
def test_ambiguous_attempt_identity_is_rejected(grain, receipt, field, value):
    receipt[field] = value
    with pytest.raises(ValueError):
        grain.validate_receipt_identity(ROOT, receipt)


@pytest.mark.parametrize("field", ["attempt_ordinal", "execution_authorization_sha256", "runs"])
def test_incomplete_receipt_is_rejected(grain, receipt, field):
    del receipt[field]
    with pytest.raises(ValueError):
        grain.validate_receipt_identity(ROOT, receipt)


def test_historical_receipt_cannot_be_reused_for_attempt2(grain):
    historical = json.loads((ROOT / "registry/study1_sg000031_attempt1_closeout.json").read_bytes())
    old = historical["canonical_runner_qualification"]
    with pytest.raises(ValueError, match="format"):
        grain.parse_receipt(comment(grain, old, marker="DAL_R2_CANONICAL_QUALIFICATION_V1"))
    with pytest.raises(ValueError, match="structure"):
        grain.validate_receipt_identity(ROOT, old)


@pytest.mark.parametrize("phase", ["candidate", "post-merge"])
def test_engineering_receipts_cannot_admit_execution(grain, receipt, phase):
    receipt["phase"] = phase
    with pytest.raises(ValueError):
        grain.validate_receipt_identity(ROOT, receipt)
    with pytest.raises(ValueError):
        grain.parse_receipt(comment(grain, receipt, marker=grain.MARKERS[phase]))


@pytest.mark.parametrize(
    "invalid",
    [
        "missing-close",
        "extra-fence",
        "old-marker",
        "duplicate-key",
        "nonfinite",
        "lone-cr",
        "invalid-json",
        "foreign-author",
        "foreign-issue",
    ],
)
def test_malformed_receipts_fail_closed(grain, receipt, invalid):
    value = comment(grain, receipt)
    if invalid == "missing-close":
        value["body"] = value["body"][:-3]
    elif invalid == "extra-fence":
        value["body"] += "\n```json\n{}\n```"
    elif invalid == "old-marker":
        value["body"] = value["body"].replace(
            grain.MARKERS["canonical"], "DAL_R2_CANONICAL_QUALIFICATION_V1"
        )
    elif invalid in {"duplicate-key", "nonfinite", "invalid-json"}:
        raw = {
            "duplicate-key": '{"attempt_ordinal":2,"attempt_ordinal":1}',
            "nonfinite": '{"attempt_ordinal":NaN}',
            "invalid-json": "{",
        }[invalid]
        value["body"] = grain.MARKERS["canonical"] + "\n```json\n" + raw + "\n```"
    elif invalid == "lone-cr":
        value["body"] = value["body"].replace("V1\n", "V1\r")
    elif invalid == "foreign-author":
        value["user"]["login"] = "SomeoneElse"
    else:
        value["issue_url"] += "0"
    with pytest.raises(ValueError):
        grain.parse_receipt(value)


@pytest.fixture
def native_evidence(grain, receipt, monkeypatch):
    """Keep production URL/auth/parser/admission code; fixture only external evidence."""
    native = grain.legacy
    routes = {
        "/repos/TheHalfMoon/DAL": {
            "full_name": native.REPOSITORY,
            "url": native.REPOSITORY_API,
            "private": False,
            "default_branch": "main",
        },
        "/repos/TheHalfMoon/DAL/issues/comments/200": comment(grain, receipt),
        "/repos/TheHalfMoon/DAL/git/ref/heads/main": {"object": {"sha": receipt["main_sha"]}},
        "/repos/TheHalfMoon/DAL/pulls/162": {
            "head": {"sha": receipt["head_sha"]},
            "merged": True,
            "merge_commit_sha": receipt["main_sha"],
        },
        "/graphql": {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {"pageInfo": {"hasNextPage": False}, "nodes": []}
                    }
                }
            }
        },
    }
    observed = []

    class Handler(BaseHTTPRequestHandler):
        def respond(self):
            if self.command == "POST":
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                assert request == {
                    "query": native.REVIEW_THREADS_QUERY,
                    "variables": {"number": 162},
                }
            observed.append((self.command, self.path, self.headers.get("Authorization")))
            payload = json.dumps(routes[self.path]).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = respond
        do_POST = respond

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class Opener:
        def open(self, request, timeout):
            parsed = urlsplit(request.full_url)
            assert parsed.scheme == "https" and parsed.netloc == "api.github.com"
            local = f"http://127.0.0.1:{server.server_port}{parsed.path}"
            return urlopen(
                Request(
                    local,
                    data=request.data,
                    headers=dict(request.header_items()),
                    method=request.get_method(),
                ),
                timeout=timeout,
            )

    monkeypatch.setattr(native, "build_opener", lambda *_args: Opener())
    monkeypatch.setattr(
        native,
        "git",
        lambda *args: (
            grain.REPAIR_MAIN
            if args[0] == "merge-base"
            else grain.REPAIR_MAIN + " " + receipt["head_sha"]
            if args[0] == "show"
            else receipt["tree"]
        ),
    )
    # Already-qualified external predecessor/review/ZIP objects are separate test seams.
    monkeypatch.setattr(grain, "verify_predecessors", lambda *_args: None)
    monkeypatch.setattr(native, "verify_run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(native, "verify_reports", lambda *_args: 7)
    monkeypatch.setattr(grain, "verify_inspection", lambda *_args: None)
    monkeypatch.setattr(grain, "verify_native", lambda *_args, **_kwargs: None)
    sdk = json.loads((ROOT / "registry/study1_sg000031_sdk_qualification.json").read_bytes())
    monkeypatch.setattr(
        native, "artifact_documents", lambda *_args: {"sdk-qualification.json": sdk}
    )
    try:
        yield routes, observed
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_correct_receipt_uses_native_auth_http_and_read_only_guard(grain, receipt, native_evidence):
    routes, observed = native_evidence
    native = grain.legacy
    with native.native_read_only_preflight() as audit:
        result = grain.qualify_canonical_receipt(ROOT, 200, receipt["main_sha"])
    routes["/repos/TheHalfMoon/DAL/issues/comments/200"]["body"] = routes[
        "/repos/TheHalfMoon/DAL/issues/comments/200"
    ]["body"].replace("\n", "\r\n")
    with native.native_read_only_preflight():
        assert grain.qualify_canonical_receipt(ROOT, 200, receipt["main_sha"]) == result
        with pytest.raises(ValueError, match="forbids mutation"):
            native.api("git/refs", {"synthetic": True})
    assert result == (receipt, 7)
    assert all(auth == "Bearer synthetic-attempt2-token" for _, _, auth in observed)
    assert [row["method"] for row in audit] == ["GET", "GET", "GET", "GET", "POST"]
    assert audit[-1]["read_only_review_query"] is True
    assert "synthetic-attempt2-token" not in json.dumps(audit)
    assert all(method == "GET" or path == "/graphql" for method, path, _ in observed)


@pytest.mark.parametrize(
    "invalid",
    [
        "stale-main",
        "wrong-tree",
        "wrong-parent",
        "changed-head",
        "missing-workflow",
        "missing-review",
        "active-thread",
    ],
)
def test_external_evidence_drift_is_rejected(grain, receipt, native_evidence, monkeypatch, invalid):
    routes, _observed = native_evidence
    if invalid == "stale-main":
        routes["/repos/TheHalfMoon/DAL/git/ref/heads/main"]["object"]["sha"] = "d" * 40
    elif invalid == "wrong-tree":
        receipt["tree"] = "d" * 40
        monkeypatch.setattr(grain.legacy, "git", lambda *_args: "c" * 40)
    elif invalid == "wrong-parent":
        monkeypatch.setattr(
            grain.legacy,
            "git",
            lambda *args: (
                receipt["tree"]
                if args[0] == "rev-parse"
                else grain.REPAIR_MAIN
                if args[0] == "merge-base"
                else "d" * 40
            ),
        )
    elif invalid == "changed-head":
        routes["/repos/TheHalfMoon/DAL/pulls/162"]["head"]["sha"] = "d" * 40
    elif invalid == "missing-workflow":
        del receipt["runs"]["post_native"]
    elif invalid == "missing-review":
        del receipt["reviews"]["post_native"]
    else:
        routes["/graphql"]["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"] = [
            {"isResolved": False, "isOutdated": False}
        ]
    with pytest.raises(ValueError):
        grain.verify_qualification(ROOT, receipt)


@pytest.mark.parametrize("history", [[], [1, 2], [2], [1]])
def test_no_claim_absence_can_renew_a_failed_dispatch(grain, monkeypatch, tmp_path, history):
    monkeypatch.setattr(grain.legacy, "environment_guard", lambda: None)
    monkeypatch.setattr(grain.legacy, "WORKFLOW", grain.WORKFLOW)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_RUN_ID", "2")
    runs = [{"id": value, "path": grain.WORKFLOW, "run_attempt": 1} for value in history]
    if history == [2]:
        runs[0]["run_attempt"] = 2
    monkeypatch.setattr(grain, "execution_history", lambda: runs)
    monkeypatch.setattr(grain.legacy, "api", lambda *_args: pytest.fail("claim mutation reached"))
    with pytest.raises(ValueError, match="consumed or wrong"):
        grain.admit(ROOT, 200, tmp_path)
    assert not list(tmp_path.iterdir())


def test_only_first_dispatch_reaches_canonical_receipt_validation(grain, monkeypatch, tmp_path):
    monkeypatch.setattr(grain.legacy, "environment_guard", lambda: None)
    monkeypatch.setattr(grain.legacy, "WORKFLOW", grain.WORKFLOW)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_RUN_ID", "2")
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    monkeypatch.setattr(
        grain, "execution_history", lambda: [{"id": 2, "path": grain.WORKFLOW, "run_attempt": 1}]
    )
    calls = []

    def stop(root, comment_id, main):
        calls.append((root, comment_id, main))
        raise ValueError("canonical-validation-stop")

    monkeypatch.setattr(grain, "qualify_canonical_receipt", stop)
    with pytest.raises(ValueError, match="canonical-validation-stop"):
        grain.admit(ROOT, 200, tmp_path)
    assert calls == [(ROOT, 200, "b" * 40)]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("ordinal", [None, "1", "2", "02", "", "3", "true"])
def test_namespace_selection_is_explicit_and_default_preserves_attempt1(ordinal):
    import os

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "scripts")
    environment.pop("DAL_R2_ATTEMPT_ORDINAL", None)
    if ordinal is not None:
        environment["DAL_R2_ATTEMPT_ORDINAL"] = ordinal
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import study1_sg000031_r2_admission as a; "
            "print(a.ATTEMPT_REF, a.LEDGER_BRANCH, a.WORKFLOW)",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if ordinal in {None, "1", "2"}:
        assert result.returncode == 0
        expected = "2" if ordinal == "2" else "1"
        assert f"tags/dal-r2-issue158-attempt{expected}" in result.stdout
        assert f"codex/sg000031-r2-attempt{expected}-journal" in result.stdout
    else:
        assert result.returncode != 0 and "ambiguous R2 attempt ordinal" in result.stderr


def test_science_and_first_attempt_files_remain_immutable(grain):
    contract = grain.load_contract(ROOT)
    assert len(contract["immutable_file_lf_sha256"]) == 43
    assert contract["attempt1"]["lineage_sha256"] == grain.LINEAGE_SHA
    old = (ROOT / ".github/workflows/study1-sg000031-r2-worker.yml").read_text(encoding="utf-8")
    new = (ROOT / ".github/workflows/study1-sg000031-r2-attempt2-worker.yml").read_text(
        encoding="utf-8"
    )
    new = new.replace('  DAL_R2_ATTEMPT_ORDINAL: "2"\n', "").replace(
        "R2 Attempt 2 frozen worker", "R2 frozen worker"
    )
    new = new.replace("sg000031-r2-attempt2-", "sg000031-r2-")
    assert new == old
    controller = (ROOT / grain.WORKFLOW).read_text(encoding="utf-8")
    assert (
        "  workflow_dispatch:" in controller
        and "  push:" not in controller
        and "  pull_request:" not in controller
    )
    preflight = (ROOT / grain.PREFLIGHT).read_text(encoding="utf-8")
    assert "scripts/study1_sg000031_r2_admission.py admit" not in preflight
    assert "study1_sg000031_r2_runner.py" not in preflight


def test_alibaba_workflow_cannot_fabricate_inspection(grain, receipt, monkeypatch):
    receipt["reviews"]["alibaba"] = {"inspection_comment_id": 300, "report_sha256": "e" * 64}
    identity = {**grain.inspection_identity(receipt), "rules_sha256": "f" * 64}
    value = comment(grain, identity, marker=grain.INSPECTION_MARKER)
    monkeypatch.setattr(grain.legacy, "api", lambda *_args: value)
    monkeypatch.setattr(
        grain.legacy,
        "artifact_documents",
        lambda *_args: {"ocr-evidence.json": {"rules_sha256": "f" * 64}},
    )
    grain.verify_inspection(receipt)
    identity["head_sha"] = "d" * 40
    value["body"] = comment(grain, identity, marker=grain.INSPECTION_MARKER)["body"]
    with pytest.raises(ValueError, match="actual exact-head"):
        grain.verify_inspection(receipt)


def test_native_report_cannot_omit_source_or_hide_model_calls(grain, monkeypatch):
    base = {
        "checkout_sha": "a" * 40,
        "engineering_preflight_state": "PASS",
        "R2_scientific_state": "BLOCKED",
        "physical_model_POSTs": 0,
        "first_turn_generations": 0,
        "final_rows_materialized": 0,
        "final_content_access": False,
        "new_execution_authorized": False,
        "founder_cost_usd": 0,
        "REST_mutations_permitted": False,
        "attempt_ordinal": 2,
        "phase": "candidate",
        "execution_authorization_unconsumed": True,
        "source_lf_sha256": {},
    }
    for changed in [
        {},
        {"physical_model_POSTs": 1},
        {"physical_model_POSTs": False},
        {"final_content_access": True},
    ]:
        report = {**copy.deepcopy(base), **changed}
        monkeypatch.setattr(grain, "artifact_report", lambda *_args, report=report: report)
        with pytest.raises(ValueError):
            grain.verify_native({}, 100, "a" * 40, phase="candidate")
