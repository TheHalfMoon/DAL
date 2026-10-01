from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "paper" / "generated"
BUILDER_PATH = ROOT / "tools" / "build_sg000024_manuscript_inputs.py"


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_sg000024_manuscript_inputs", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _builder()


def test_manuscript_inputs_are_deterministically_rebuildable() -> None:
    result = subprocess.run(
        [sys.executable, "tools/build_sg000024_manuscript_inputs.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_frozen_claim_binding_matches_sg000024_spec() -> None:
    spec = json.loads(
        (ROOT / ".specgrain" / "specs" / "SG-000024.json").read_text(encoding="utf-8")
    )
    assert BUILDER.FROZEN_CLAIM_SET_SHA256 == spec["metadata"]["frozen_claim_set_sha256"]


def test_claim_macros_reproduce_frozen_wording_by_public_use() -> None:
    claims_tex = (GENERATED / "dal_claims.tex").read_text(encoding="utf-8")
    ledger = json.loads((BUILDER.PACKAGE / "claim_ledger.json").read_text(encoding="utf-8"))
    for claim in ledger["claims"]:
        family = "dalclaim" if claim["public_use"] == "affirmative-claim" else "dallimitation"
        other = "dallimitation" if family == "dalclaim" else "dalclaim"
        macro = (
            f"\csname {family}@{claim['claim_id']}\endcsname{{{BUILDER.tex_escape(claim['text'])}}}"
        )
        assert macro in claims_tex
        assert f"{other}@{claim['claim_id']}\endcsname" not in claims_tex


def test_numbers_are_copied_from_the_frozen_package() -> None:
    numbers = BUILDER._numbers()
    main = json.loads((BUILDER.PACKAGE / "main_results.json").read_text(encoding="utf-8"))
    paper = next(row for row in main["rows"] if row["system_id"] == "paper")
    assert numbers["pubmedqa.paper.accuracy"] == f"{paper['metrics']['accuracy']:.4f}"
    assert numbers["native.diff.estimate"] == "-0.0125"
    assert numbers["native.paper.target08.unsafecommitrate"] == "1.0000"
    assert numbers["fhir.requested"] == "173"
    assert numbers["fhir.goldrows"] == "0"
    assert numbers["pubmedqa.identity.probabilities"] == numbers["pubmedqa.identity.rows"] == "500"


def test_tampered_package_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    copy = tmp_path / "package"
    shutil.copytree(BUILDER.PACKAGE, copy)
    target = copy / "main_results.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace("0.552", "0.600", 1), encoding="utf-8"
    )
    monkeypatch.setattr(BUILDER, "PACKAGE", copy)
    with pytest.raises(ValueError, match="differs from provenance index"):
        BUILDER.verify_package()


def test_bibliography_entries_are_verified_records() -> None:
    record = json.loads(BUILDER.BIBLIOGRAPHY_PATH.read_text(encoding="utf-8"))
    bib = (GENERATED / "references.bib").read_text(encoding="utf-8")
    keys = [entry["key"] for entry in record["entries"]]
    assert len(keys) == len(set(keys))
    for entry in record["entries"]:
        assert entry["verified_via"]
        assert entry["url"].startswith("https://")
        assert f"{{{entry['key']},\n" in bib
        if entry["kind"] == "doi":
            assert entry["doi"] == entry["identifier"]
        if entry["kind"] == "arxiv":
            assert entry["arxiv"] == entry["identifier"]
    assert bib.count("\n@") + bib.startswith("@") == len(keys)


def test_tex_escape_handles_specials() -> None:
    assert BUILDER.tex_escape("95% & a_b") == "95\% \& a\_b"


def test_generated_manifest_binds_outputs() -> None:
    manifest = json.loads((GENERATED / BUILDER.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["frozen_claim_set_sha256"] == BUILDER.FROZEN_CLAIM_SET_SHA256
    for name, digest in manifest["outputs_sha256"].items():
        text = (GENERATED / name).read_text(encoding="utf-8")
        assert BUILDER._sha256(text.encode("utf-8")) == digest
