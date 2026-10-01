from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "registry" / "p08_sg000023_related_work_refresh.json"
EVIDENCE = ROOT / "registry" / "p08_sg000023_paper_evidence"
BUILDER_PATH = ROOT / "tools" / "build_sg000023_paper_evidence.py"

ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}$")
DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_sg000023_paper_evidence", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _record() -> dict[str, Any]:
    payload = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load(name: str) -> dict[str, Any]:
    payload = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_record_is_dated_zero_cost_and_changes_no_protocol() -> None:
    record = _record()
    assert record["grain_id"] == "SG-000023"
    assert record["search_date"] == "2026-10-01"
    assert record["cost"].startswith("zero")
    assert "Scite" not in json.dumps(record["sources"])
    assert record["model_or_protocol_change"].startswith("none")
    assert record["limitations"]


def test_search_manifest_is_internally_consistent() -> None:
    record = _record()
    ids: set[str] = set()
    for query in record["queries"]:
        assert query["query"]
        assert query["result_count"] == len(query["result_ids"])
        ids.update(query["result_ids"])
    assert record["screened_unique_records"] == len(ids)


def test_included_and_excluded_entries_are_verifiable() -> None:
    record = _record()
    assert record["included"]
    for entry in record["included"]:
        identifiers = entry["identifiers"]
        assert identifiers, entry["title"]
        if "arxiv" in identifiers:
            assert ARXIV_ID.match(identifiers["arxiv"]), identifiers
        if "doi" in identifiers:
            assert DOI.match(identifiers["doi"]), identifiers
        assert entry["urls"] and all(url.startswith("https://") for url in entry["urls"])
        assert entry["verified_via"]
        assert entry["relationship_to_dal"] and entry["novelty_implication"]
    for entry in record["excluded_notable"]:
        assert ARXIV_ID.match(entry["arxiv"])
        assert entry["reason"]


def test_novelty_dispositions_never_retain_a_first_claim() -> None:
    record = _record()
    allowed = {"removed", "narrowed-to-descriptive", "retained-as-scoped-description"}
    for row in record["novelty_disposition"]:
        assert row["disposition"] in allowed
        if row["disposition"] == "removed":
            assert row["blocking_work"], row["candidate_claim"]
        if row["disposition"] == "retained-as-scoped-description":
            wording = row["permitted_wording"].lower()
            assert "first" not in wording
            assert "state of the art" not in wording
            assert "we do not claim methodological novelty" in wording
    removed = {
        row["candidate_claim"]
        for row in record["novelty_disposition"]
        if row["disposition"] == "removed"
    }
    narrowed = [
        row
        for row in record["novelty_disposition"]
        if row["disposition"] == "narrowed-to-descriptive"
    ]
    assert all("outperforms" not in row["candidate_claim"] for row in narrowed)
    assert "first medical abstention system or benchmark" in removed


def test_literature_packet_and_claim_binding() -> None:
    packets = {row["packet_id"]: row for row in _load("evidence_packets.json")["packets"]}
    packet = packets["EP-SG23-LIT-001"]
    assert packet["status"] == "supported-literature-disposition"
    assert packet["canonical_sources"] == ["registry/p08_sg000023_related_work_refresh.json"]
    claims = {row["claim_id"]: row for row in _load("claim_ledger.json")["claims"]}
    claim = claims["SG23-C011"]
    assert claim["evidence_packet_id"] == "EP-SG23-LIT-001"
    assert claim["exportable"] is False
    assert "first medical abstention system or benchmark" in claim["text"]
    assert "no directional superiority claim" in claim["text"]
    scoped = claims["SG23-C012"]
    assert scoped["status"] == "candidate-scoped-description"
    assert scoped["exportable"] is False
    assert scoped["evidence_packet_id"] == "EP-SG23-LIT-001"
    assert "We do not claim methodological novelty" in scoped["text"]


def test_literature_packet_cannot_support_exportable_claim() -> None:
    builder = _builder()
    package = {name: _load(name) for name in builder.ARTIFACT_NAMES}
    matrix = json.loads(builder.MATRIX_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(package)
    for claim in tampered["claim_ledger.json"]["claims"]:
        if claim["claim_id"] == "SG23-C011":
            claim["exportable"] = True
            claim["status"] = "supported"
    errors = builder.validate_package(tampered, matrix)
    assert any("exports an affirmative claim from literature packet" in error for error in errors)
