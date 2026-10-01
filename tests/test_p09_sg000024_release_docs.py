from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_sg000024_release_docs.py"
LEDGER = ROOT / "registry" / "p08_sg000023_paper_evidence" / "claim_ledger.json"
RELEASE = ROOT / "docs" / "release"
GENERATED_DOCS = ("MODEL_CARD.md", "HUGGINGFACE_CARD_DRAFT.md", "RELEASE_NOTES_DRAFT.md")

PROHIBITED = (
    "state of the art",
    "sota)",
    "outperform",
    "know when not to act",
    "clinically safe system",
)


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_sg000024_release_docs", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _builder()


def _ledger() -> list[dict[str, str]]:
    claims = json.loads(LEDGER.read_text(encoding="utf-8"))["claims"]
    assert isinstance(claims, list)
    return claims


def test_release_documents_are_deterministically_rebuildable() -> None:
    result = subprocess.run(
        [sys.executable, "tools/build_sg000024_release_docs.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_frozen_claim_appears_verbatim_in_every_release_text() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    block = readme.split(BUILDER.BEGIN, 1)[1].split(BUILDER.END, 1)[0]
    texts = [block] + [(RELEASE / name).read_text(encoding="utf-8") for name in GENERATED_DOCS]
    for claim in _ledger():
        for text in texts:
            assert f"- {claim['text']} (`{claim['claim_id']}`)" in text


def test_limitations_are_listed_under_limitations() -> None:
    card = (RELEASE / "MODEL_CARD.md").read_text(encoding="utf-8")
    findings, limitations = card.split("### Limitations", 1)
    for claim in _ledger():
        line = f"(`{claim['claim_id']}`)"
        if claim["public_use"] == "limitation-statement":
            assert line in limitations and line not in findings
        else:
            assert line in findings.split("### Findings", 1)[1]


def test_disclaimer_and_boundaries_are_present() -> None:
    for name in GENERATED_DOCS:
        assert BUILDER.DISCLAIMER in (RELEASE / name).read_text(encoding="utf-8")
    hf = (RELEASE / "HUGGINGFACE_CARD_DRAFT.md").read_text(encoding="utf-8")
    assert "DRAFT: not published" in hf
    assert "license_name: to-be-confirmed-by-founder" in hf
    card = (RELEASE / "MODEL_CARD.md").read_text(encoding="utf-8")
    assert "Model weights are **not released**" in card
    steps = (RELEASE / "ARXIV_AND_RELEASE_STEPS.md").read_text(encoding="utf-8")
    assert "none has been performed" in steps


def test_hand_written_release_text_avoids_promotional_claims() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    outside_block = readme.split(BUILDER.BEGIN, 1)[0] + readme.split(BUILDER.END, 1)[1]
    hand_written = [
        outside_block,
        (RELEASE / "REPRODUCIBILITY_CHECKLIST.md").read_text(encoding="utf-8"),
        (RELEASE / "ARXIV_AND_RELEASE_STEPS.md").read_text(encoding="utf-8"),
        (ROOT / "CITATION.cff").read_text(encoding="utf-8"),
    ]
    for text in hand_written:
        lowered = text.lower()
        for phrase in PROHIBITED:
            assert phrase not in lowered, phrase
    assert "Research use only" in outside_block


def test_reproducibility_checklist_keeps_external_items_open() -> None:
    checklist = (RELEASE / "REPRODUCIBILITY_CHECKLIST.md").read_text(encoding="utf-8")
    for item in (
        "Independent third-party reproduction",
        "arXiv submission",
        "Model-weight release",
    ):
        assert f"- [ ] {item}" in checklist
