"""Regression tests for claim ancestry availability; synthetic Git repositories only."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / ".github/workflows/study1-sg000031-r2-attempt2-worker.yml"


def _git(directory: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _synthetic_merge(tmp_path: Path) -> tuple[Path, list[str]]:
    source = tmp_path / "synthetic-source"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Synthetic Tester")
    _git(source, "config", "user.email", "synthetic@example.invalid")
    (source / "base.txt").write_text("base\n", encoding="utf-8")
    _git(source, "add", "base.txt")
    _git(source, "commit", "-m", "synthetic base")
    _git(source, "switch", "-c", "feature")
    (source / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(source, "add", "feature.txt")
    _git(source, "commit", "-m", "synthetic feature")
    _git(source, "switch", "main")
    (source / "main.txt").write_text("main\n", encoding="utf-8")
    _git(source, "add", "main.txt")
    _git(source, "commit", "-m", "synthetic main")
    _git(source, "merge", "--no-ff", "feature", "-m", "synthetic merge")
    expected_parents = _git(source, "show", "-s", "--format=%P", "HEAD").split()
    assert len(expected_parents) == 2
    return source, expected_parents


def test_shallow_checkout_hides_exact_merge_parents(tmp_path: Path) -> None:
    source, expected_parents = _synthetic_merge(tmp_path)
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "--quiet", "--depth=1", source.as_uri(), str(shallow))
    assert _git(shallow, "rev-parse", "HEAD") == _git(source, "rev-parse", "HEAD")
    assert _git(shallow, "show", "-s", "--format=%P", "HEAD").split() != expected_parents
    assert _git(shallow, "rev-parse", "--is-shallow-repository") == "true"


def test_complete_history_restores_exact_parents_and_rejects_wrong_parent(
    tmp_path: Path,
) -> None:
    source, expected_parents = _synthetic_merge(tmp_path)
    full = tmp_path / "full"
    _git(tmp_path, "clone", "--quiet", source.as_uri(), str(full))
    actual_parents = _git(full, "show", "-s", "--format=%P", "HEAD").split()
    assert _git(full, "rev-parse", "--is-shallow-repository") == "false"
    assert actual_parents == expected_parents
    assert actual_parents != list(reversed(expected_parents))
    assert actual_parents != ["0" * 40, expected_parents[1]]


def test_worker_fetches_history_before_claim_check() -> None:
    workflow = WORKER.read_text(encoding="utf-8")
    checkout = workflow.split("      - name: Checkout exact canonical execution main\n", 1)[1]
    checkout, remainder = checkout.split("      - name: Set up Python\n", 1)
    assert "uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in checkout
    assert "ref: ${{ github.sha }}" in checkout
    assert "fetch-depth: 0" in checkout
    assert (
        "      - name: Verify permanent exact-run R2 claim before infrastructure setup"
        in remainder
    )
    assert "      - name: Execute exactly one frozen first turn" in remainder


@pytest.mark.parametrize("depth", ["1", "2"])
def test_incomplete_checkout_still_fails_ancestry_verification(
    tmp_path: Path, depth: str
) -> None:
    source, expected_parents = _synthetic_merge(tmp_path)
    shallow = tmp_path / ("shallow-" + depth)
    _git(tmp_path, "clone", "--quiet", "--depth", depth, source.as_uri(), str(shallow))
    if depth == "1":
        assert _git(shallow, "show", "-s", "--format=%P", "HEAD").split() != expected_parents
    else:
        # A two-deep clone may know the immediate parents. This is not proof of
        # complete ancestry: it must remain classified as shallow.
        assert _git(shallow, "rev-parse", "--is-shallow-repository") == "true"
