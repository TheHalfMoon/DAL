"""Deterministic native HTTP fixtures only; no benchmark, model or final content."""

from __future__ import annotations

import importlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admission(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.setenv("GH_TOKEN", "synthetic-qualification-token")
    return importlib.import_module("study1_sg000031_r2_admission")


@pytest.fixture
def native_fixture(admission, monkeypatch):
    observed = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            observed.append((self.path, self.headers.get("Authorization")))
            status = 404 if self.path == "/repos/TheHalfMoon/DAL/" else 200
            payload = json.dumps(
                {
                    "full_name": "TheHalfMoon/DAL",
                    "url": "https://api.github.com/repos/TheHalfMoon/DAL",
                    "private": False,
                    "default_branch": "main",
                }
            ).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class FixtureOpener:
        def open(self, request, timeout):
            parsed = urlsplit(request.full_url)
            assert parsed.scheme == "https" and parsed.netloc == "api.github.com"
            assert request.get_method() == "GET" and request.data is None
            fixture = f"http://127.0.0.1:{server.server_port}{parsed.path}"
            if parsed.query:
                fixture += "?" + parsed.query
            # Preserve the native path, headers and method; only route transport to the fixture.
            return urlopen(Request(fixture, headers=dict(request.header_items())), timeout=timeout)

    monkeypatch.setattr(admission, "build_opener", lambda *_args: FixtureOpener())
    try:
        yield observed
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_retained_trailing_slash_failure_and_corrected_native_lookup(admission, native_fixture):
    legacy = admission.REPOSITORY_API + "/"
    with pytest.raises(HTTPError) as caught:
        admission.native_http(admission.authenticated_request(legacy))
    retained = json.loads(
        (ROOT / "registry/study1_sg000031_attempt1_admission_failure.json").read_bytes()
    )
    assert caught.value.code == 404
    assert admission.digest(str(caught.value)) == retained["error_sha256"]
    with admission.native_read_only_preflight() as audit:
        assert admission.api("")["full_name"] == admission.REPOSITORY
    assert [path for path, _ in native_fixture] == [
        "/repos/TheHalfMoon/DAL/",
        "/repos/TheHalfMoon/DAL",
    ]
    assert all(auth == "Bearer synthetic-qualification-token" for _, auth in native_fixture)
    assert audit[0]["status"] == 200 and audit[0]["url"] == admission.REPOSITORY_API
    assert "synthetic-qualification-token" not in json.dumps(audit)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "https://api.github.com/repos/TheHalfMoon/DAL",
        "https://api.github.com/repos/TheHalfMoon/DAL/",
    ],
)
def test_repository_root_has_one_canonical_identity(admission, native_fixture, path):
    assert admission.repository_url(path) == admission.REPOSITORY_API
    assert admission.api(path)["url"] == admission.REPOSITORY_API
    assert native_fixture[0][0] == "/repos/TheHalfMoon/DAL"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "//api.github.com/repos/TheHalfMoon/DAL",
        " ../DAL",
        "git/../refs",
        "git/./refs",
        "git//refs",
        "git/refs/",
        "git\\refs",
        "git/%2e%2e/refs",
        "git/refs#fragment",
        "git/refs?",
        "git/refs?ref=main",
        "git/refs?per_page=101",
        "git/refs?per_page=100&per_page=1",
        "git/refs?per_page=01",
        "?per_page=100",
        "https://api.github.com/repos/TheHalfMoon/DAL-other",
        "https://api.github.com/repos/Elsewhere/DAL",
        "https://api.github.com.evil.example/repos/TheHalfMoon/DAL",
        "https://token@api.github.com/repos/TheHalfMoon/DAL",
        "https://api.github.com:443/repos/TheHalfMoon/DAL",
        "http://api.github.com/repos/TheHalfMoon/DAL",
        "HTTPS://api.github.com/repos/TheHalfMoon/DAL",
        "https://api.github.com/repos/TheHalfMoon/DAL//",
        "https://api.github.com/repos/TheHalfMoon/DAL/?per_page=100",
        "https://api.github.com/repos/TheHalfMoon/DAL#fragment",
        "git/refs\n",
        "git/refs\t",
        "gít/refs",
        None,
    ],
)
def test_ambiguous_urls_fail_before_transport_or_credentials(
    admission, native_fixture, monkeypatch, path
):
    monkeypatch.delenv("GH_TOKEN")
    with pytest.raises(ValueError):
        admission.api(path)
    assert native_fixture == []


def test_existing_job_artifact_ref_and_checkpoint_routes_are_preserved(admission):
    for path in [
        "actions/runs/37320473498/jobs?per_page=100",
        "actions/artifacts/123/zip",
        "git/ref/tags/dal-r2-issue158-attempt1",
        "git/tags/abc123",
        "contents/evidence/study1-r2-attempt1/rows/" + "a" * 64 + ".json",
    ]:
        assert admission.repository_url(path) == admission.REPOSITORY_API + "/" + path


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "GET"])
def test_preflight_forbids_mutations_even_with_get_body(admission, native_fixture, method):
    with admission.native_read_only_preflight():
        with pytest.raises(ValueError, match="forbids mutation"):
            admission.api("git/refs", {"synthetic": True}, method=method)
    assert native_fixture == []


def test_only_fixed_read_only_graphql_query_is_permitted(admission, native_fixture):
    request = admission.authenticated_request(
        "https://api.github.com/graphql",
        {"query": "mutation { synthetic }", "variables": {"number": 159}},
    )
    with admission.native_read_only_preflight():
        with pytest.raises(ValueError, match="fixed read-only"):
            admission.native_http(request, review_query=True)
    assert native_fixture == []


def test_cross_host_artifact_redirect_strips_bearer_and_unsafe_targets_fail(admission):
    request = admission.authenticated_request(
        admission.REPOSITORY_API + "/actions/artifacts/123/zip"
    )
    handler = admission.StripCrossHostAuthorization()
    redirected = handler.redirect_request(
        request, None, 302, "Found", {}, "https://fixture.blob.core.windows.net/archive.zip"
    )
    assert not redirected.has_header("Authorization")
    for target in [
        "http://api.github.com/repos/TheHalfMoon/DAL",
        "https://token@api.github.com/repos/TheHalfMoon/DAL",
        "https://@api.github.com/repos/TheHalfMoon/DAL",
        "https://api.github.com:443/repos/TheHalfMoon/DAL",
        "https://api.github.com/repos/TheHalfMoon/DAL-other",
    ]:
        with pytest.raises(ValueError):
            handler.redirect_request(request, None, 302, "Found", {}, target)


def test_real_admission_uses_shared_validator_and_stops_before_claim(
    admission, monkeypatch, tmp_path
):
    events = []
    monkeypatch.setattr(admission, "environment_guard", lambda: None)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_RUN_ID", "37320473498")
    monkeypatch.setenv("GITHUB_SHA", "synthetic-main")
    monkeypatch.setattr(admission, "api", lambda path: {"path": admission.WORKFLOW})

    def shared(root, comment_id, main, *, live_main=True):
        events.append((root, comment_id, main, live_main))
        raise ValueError("shared-validation-stop")

    monkeypatch.setattr(admission, "qualify_canonical_receipt", shared)
    with pytest.raises(ValueError, match="shared-validation-stop"):
        admission.admit(ROOT, 5995901646, tmp_path)
    assert events == [(ROOT, 5995901646, "synthetic-main", True)]
    assert list(tmp_path.iterdir()) == []


def test_live_main_guard_remains_required_for_real_admission(admission, monkeypatch):
    historical = json.loads((ROOT / "registry/study1_sg000031_attempt1_closeout.json").read_bytes())
    receipt = historical["canonical_runner_qualification"]
    responses = {
        "": {
            "full_name": admission.REPOSITORY,
            "url": admission.REPOSITORY_API,
            "private": False,
            "default_branch": "main",
        },
        "issues/comments/5995901646": {
            "issue_url": admission.REPOSITORY_API + "/issues/158",
            "user": {"login": "TheHalfMoon"},
            "body": "DAL_R2_CANONICAL_QUALIFICATION_V1\n```json\n" + json.dumps(receipt) + "\n```",
        },
        "git/ref/heads/main": {"object": {"sha": "different-live-main"}},
    }
    monkeypatch.setattr(admission, "api", lambda path: responses[path])
    with pytest.raises(ValueError, match="live canonical main changed"):
        admission.qualify_canonical_receipt(ROOT, 5995901646, receipt["main_sha"])
