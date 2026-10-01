from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
MAIN = PAPER / "main.tex"
GENERATED = PAPER / "generated"
LEDGER = ROOT / "registry" / "p08_sg000023_paper_evidence" / "claim_ledger.json"

# Decimal literals allowed in hand-written manuscript prose: frozen protocol constants and
# software versions, never results.
ALLOWED_DECIMALS = {"0.5", "0.8", "0.9", "0.50", "0.80", "0.90", "3.11", "3.12", "1.17"}

PROHIBITED_PROSE = (
    "state of the art",
    "sota",
    "outperform",
    "significantly better",
    "superior to",
    "we are the first",
    "is the first",
    "novel method",
    "clinically safe system",
)


def _source() -> str:
    text = MAIN.read_text(encoding="utf-8")
    return "\n".join(
        line.split("%", 1)[0] if not line.lstrip().startswith("\\%") else line
        for line in text.splitlines()
    )


def _prose() -> str:
    text = _source()
    text = re.sub(
        r"\\(dalclaim|dallimitation|dalnum|texttt|input|label|ref|citep|citet|bibliography)\{[^}]*\}",
        " ",
        text,
    )
    return text


def _defined(file: str, family: str) -> set[str]:
    text = (GENERATED / file).read_text(encoding="utf-8")
    return set(re.findall(rf"\\csname {family}@([^\\]+)\\endcsname", text))


def test_every_number_macro_is_generated() -> None:
    used = set(re.findall(r"\\dalnum\{([^}]+)\}", _source()))
    assert used
    assert used <= _defined("dal_numbers.tex", "dalnum")


def test_claim_macros_respect_public_use() -> None:
    source = _source()
    used_claims = set(re.findall(r"\\dalclaim\{([^}]+)\}", source))
    used_limitations = set(re.findall(r"\\dallimitation\{([^}]+)\}", source))
    assert used_claims <= _defined("dal_claims.tex", "dalclaim")
    assert used_limitations <= _defined("dal_claims.tex", "dallimitation")


def test_negative_results_and_all_limitations_are_visible() -> None:
    source = _source()
    used = set(re.findall(r"\\dal(?:claim|limitation)\{([^}]+)\}", source))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    limitations = {
        c["claim_id"] for c in ledger["claims"] if c["public_use"] == "limitation-statement"
    }
    negative = {
        c["claim_id"]
        for c in ledger["claims"]
        if c["status"] in {"supported-negative-result", "supported-blocked-result"}
    }
    assert limitations <= used
    assert negative <= used
    assert {"SG23-C002", "SG23-C003", "SG23-C005", "SG23-C014"} <= used


def test_citations_resolve_to_generated_bibliography() -> None:
    keys = set(
        re.findall(r"@\w+\{([^,]+),", (GENERATED / "references.bib").read_text(encoding="utf-8"))
    )
    cited: set[str] = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", _source()):
        cited.update(key.strip() for key in group.split(","))
    assert cited
    assert cited <= keys


def test_no_hand_typed_result_decimals() -> None:
    # License identifiers (e.g. CC-BY-4.0) and layout widths (0.49\linewidth) are not results.
    decimals = set(re.findall(r"(?<![\w.-])\d+\.\d+(?![\w.]|\\linewidth)", _prose()))
    assert decimals <= ALLOWED_DECIMALS, sorted(decimals - ALLOWED_DECIMALS)


def test_no_prohibited_promotional_phrasing() -> None:
    prose = _prose().lower()
    for phrase in PROHIBITED_PROSE:
        assert phrase not in prose, phrase


def test_generated_inputs_are_all_used() -> None:
    inputs = set(re.findall(r"\\input\{generated/([^}]+)\}", _source()))
    tex_outputs = {path.name for path in GENERATED.glob("*.tex")}
    assert inputs == tex_outputs
