from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "registry" / "p08_sg000023_paper_evidence"
BUILDER_PATH = ROOT / "tools" / "build_sg000023_paper_evidence.py"


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_sg000023_paper_evidence", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _builder()


def _load(name: str) -> dict[str, Any]:
    payload = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _matrix() -> dict[str, Any]:
    payload = json.loads(BUILDER.MATRIX_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _committed_package() -> dict[str, Any]:
    return {name: _load(name) for name in BUILDER.ARTIFACT_NAMES}


def test_paper_evidence_is_deterministically_rebuildable() -> None:
    result = subprocess.run(
        [sys.executable, "tools/build_sg000023_paper_evidence.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{len(BUILDER.ARTIFACT_NAMES)} artifacts" in result.stdout


def test_paper_evidence_catalog_matches_shared_inventory() -> None:
    assert {path.name for path in EVIDENCE.glob("*.json")} == set(BUILDER.ARTIFACT_NAMES)


def test_frozen_sources_match_pins_and_final_manifest() -> None:
    assert BUILDER.verify_frozen_sources() == []
    manifest = json.loads(BUILDER.MANIFEST_PATH.read_text(encoding="utf-8"))
    for filename, record in manifest["artifacts"].items():
        assert BUILDER.FROZEN_SOURCE_SHA256[BUILDER.FINAL_ROOT / filename] == record["byte_sha256"]


def test_mutated_canonical_source_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    pins = dict(BUILDER.FROZEN_SOURCE_SHA256)
    pins[BUILDER.METRICS_PATH] = "0" * 64
    monkeypatch.setattr(BUILDER, "FROZEN_SOURCE_SHA256", pins)
    errors = BUILDER.verify_frozen_sources()
    assert any("metrics.json" in error and "digest mismatch" in error for error in errors)
    with pytest.raises(ValueError, match="digest mismatch"):
        BUILDER.build_artifacts()


def test_undeclared_source_read_is_rejected() -> None:
    view = BUILDER.SourceView({BUILDER.METRICS_PATH: {}}, (BUILDER.METRICS_PATH,))
    with pytest.raises(KeyError, match="undeclared canonical source"):
        view[BUILDER.CALIBRATION_PATH]


def test_package_validation_passes_on_committed_artifacts() -> None:
    assert BUILDER.validate_package(_committed_package(), _matrix()) == []


def test_packet_registry_matches_availability_matrix() -> None:
    declared = [pid for row in _matrix()["rows"] for pid in row["evidence_packet_ids"]]
    packets = _load("evidence_packets.json")["packets"]
    assert sorted(packet["packet_id"] for packet in packets) == sorted(declared)
    for packet in packets:
        if packet["status"] == BUILDER.PENDING_PACKET_STATUS:
            assert packet["derived_artifacts"] == []
            assert packet["canonical_sources"] == []
            assert packet["pending_reason"]


def test_packet_sources_cover_every_derived_artifact_input() -> None:
    package = _committed_package()
    for packet in package["evidence_packets.json"]["packets"]:
        for name in packet["derived_artifacts"]:
            assert set(package[name]["canonical_sources"]) <= set(packet["canonical_sources"])
            assert set(package[name]["canonical_sources"]) <= set(packet["derivation_inputs"])
    reliability_packets = [
        packet
        for packet in package["evidence_packets.json"]["packets"]
        if "reliability_source_data.json" in packet["derived_artifacts"]
    ]
    assert {packet["packet_id"] for packet in reliability_packets} == {
        "EP-SG23-CAL-001",
        "EP-SG23-FIGURES-001",
    }
    expected = set(package["reliability_source_data.json"]["canonical_sources"])
    for packet in reliability_packets:
        assert expected <= set(packet["derivation_inputs"])


def test_validation_rejects_missing_matrix_packet() -> None:
    package = copy.deepcopy(_committed_package())
    package["evidence_packets.json"]["packets"] = [
        packet
        for packet in package["evidence_packets.json"]["packets"]
        if packet["packet_id"] != "EP-SG23-CLAIMS-INDEX"
    ]
    errors = BUILDER.validate_package(package, _matrix())
    assert any("missing=['EP-SG23-CLAIMS-INDEX']" in error for error in errors)


def test_validation_rejects_packet_matrix_row_rebinding() -> None:
    package = copy.deepcopy(_committed_package())
    for packet in package["evidence_packets.json"]["packets"]:
        if packet["packet_id"] == "EP-SG23-CAL-001":
            packet["matrix_row_id"] = "main-action-selection-tables"
    errors = BUILDER.validate_package(package, _matrix())
    assert any(
        "EP-SG23-CAL-001 is not declared by matrix row main-action-selection-tables" in error
        for error in errors
    )


def test_validation_rejects_claim_sources_outside_packet() -> None:
    package = copy.deepcopy(_committed_package())
    for claim in package["claim_ledger.json"]["claims"]:
        if claim["claim_id"] == "SG23-C003":
            claim["evidence_packet_id"] = "EP-SG23-ACTION-001"
            claim["canonical_source_paths"].append(
                "registry/p08_calibration_evidence_sg000020.json"
            )
    errors = BUILDER.validate_package(package, _matrix())
    assert any("SG23-C003 cites sources outside packet" in error for error in errors)


def test_laya_calibration_claim_is_bound_to_calibration_packet() -> None:
    claims = {row["claim_id"]: row for row in _load("claim_ledger.json")["claims"]}
    packets = {row["packet_id"]: row for row in _load("evidence_packets.json")["packets"]}
    claim = claims["SG23-C003"]
    assert claim["evidence_packet_id"] == "EP-SG23-CAL-001"
    assert set(claim["canonical_source_paths"]) <= set(
        packets["EP-SG23-CAL-001"]["canonical_sources"]
    )


def test_reliability_and_risk_coverage_preserve_frozen_semantics() -> None:
    reliability = _load("reliability_source_data.json")
    assert [row["system_id"] for row in reliability["systems"]] == [
        "paper",
        "clinical_control",
    ]
    for system in reliability["systems"]:
        assert len(system["bins"]) == 15
        assert system["computed_ece_15_equal_width"] == system["canonical_ece_15_equal_width"]
    assert "uncalibrated" in reliability["laya_disposition"]
    assert reliability["laya_runtime_warning"]["observed"] is True

    risk = _load("risk_coverage_source_data.json")
    assert risk["no_smoothing"] is True
    assert risk["no_threshold_refit"] is True
    for system in risk["systems"]:
        assert system["n"] == 1000
        assert len(system["points"]) == 1000
        assert system["points"][0]["coverage"] == 0.001
        assert system["points"][-1]["coverage"] == 1.0
        assert system["computed_aurc"] == system["canonical_aurc"]


def test_display_values_do_not_replace_canonical_values() -> None:
    metrics = json.loads(BUILDER.METRICS_PATH.read_text(encoding="utf-8"))
    canonical = next(row for row in metrics["primary_comparisons"] if row["metric"] == "risk_at_80")
    selective = _load("selective_results.json")
    assert selective["primary_comparison"] == canonical
    assert selective["primary_comparison_display"]["estimate"] == "-0.0125"
    assert selective["primary_comparison_display"]["ci_low"] == "-0.0200"
    assert selective["primary_comparison_display"]["ci_high"] == "-0.0050"
    assert canonical["paired_bootstrap"]["estimate"] == -0.012499999999999956


def test_negative_and_blocked_results_remain_visible() -> None:
    selective = _load("selective_results.json")
    paper = next(row for row in selective["rows"] if row["system_id"] == "paper")
    assert paper["actual_policy"]["0.8"]["unsafe_commit_rate"] == 1.0
    assert paper["actual_policy"]["0.9"]["unsafe_commit_rate"] == 1.0
    laya = next(row for row in selective["rows"] if row["system_id"] == "laya")
    assert laya["status"] == "blocked"

    fhir = _load("fhir_block_table.json")
    assert fhir["new_adapter_forbidden"] is True
    assert all(row["status"] == "blocked" for row in fhir["rows"])
    assert all(row["gold_rows_loaded"] == 0 for row in fhir["rows"])


def test_qualitative_examples_are_content_blind_and_keep_zero_strata() -> None:
    examples = _load("qualitative_examples.json")
    assert examples["clinical_text_used_for_selection"] is False
    assert examples["raw_clinical_text_export"] is False
    for group in (examples["pubmedqa_strata"], examples["native_strata"]):
        for stratum in group:
            assert len(stratum["selected"]) <= 3
            selected_sources = [row["source_id"] for row in stratum["selected"]]
            assert selected_sources == sorted(selected_sources)
            for row in stratum["selected"]:
                assert "text" not in row
                assert "question" not in row
                assert "context" not in row

    zero = next(
        row for row in examples["native_strata"] if row["id"] == "both-abstain-on-sufficient"
    )
    assert zero["member_count"] == 0
    assert zero["selected"] == []


def test_claim_ledger_blocks_forbidden_affirmative_exports() -> None:
    ledger = _load("claim_ledger.json")
    by_id = {row["claim_id"]: row for row in ledger["claims"]}
    assert by_id["SG23-C004"]["status"] == "supported-negative-result"
    assert "unsafe-commit rate 1.0" in by_id["SG23-C004"]["text"]
    assert by_id["SG23-C006"]["status"] == "supported-blocked-result"
    for claim_id in ("SG23-C007", "SG23-C008", "SG23-C009", "SG23-C010"):
        assert by_id[claim_id]["exportable"] is False


def test_provenance_index_binds_sources_and_derived_artifacts() -> None:
    provenance = _load(BUILDER.PROVENANCE_INDEX_NAME)
    assert provenance["canonical_main_dependency"] == BUILDER.CANONICAL_MAIN_DEPENDENCY
    assert provenance["no_new_inference"] is True
    assert provenance["no_post_test_tuning"] is True
    assert provenance["frozen_source_digests_verified_before_derivation"] is True
    assert provenance["artifact_inventory"] == list(BUILDER.ARTIFACT_NAMES)
    # The provenance index hashes every other artifact; it cannot contain its own digest.
    assert set(provenance["artifact_sha256"]) == set(BUILDER.BASE_ARTIFACT_NAMES)
    assert BUILDER.PROVENANCE_INDEX_NAME not in provenance["artifact_sha256"]
    assert provenance["source_sha256"] == {
        path.relative_to(ROOT).as_posix(): digest
        for path, digest in BUILDER.FROZEN_SOURCE_SHA256.items()
    }
