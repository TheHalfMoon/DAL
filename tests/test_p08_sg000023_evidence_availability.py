from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MATRIX = Path("registry/p08_sg000023_evidence_availability_matrix.json")
_EXPECTED_ROWS = {
    "main-action-selection-tables",
    "reliability-analysis",
    "risk-coverage-analysis",
    "ecal-reporting",
    "evidence-interventions",
    "counterfactual-robustness",
    "fhir-final-action-selection",
    "distribution-shift-slices",
    "failure-taxonomy-and-qualitative-errors",
    "efficiency-hardware",
    "paper-tables",
    "paper-figures",
    "evidence-packets",
    "claim-ledger",
    "related-work-refresh",
    "p08-final-result-freeze",
    "canonical-p08-closeout",
}
_FORBIDDEN_NEW_WORK = {
    "would-require-forbidden-new-inference",
    "would-require-forbidden-new-adapter-or-inference",
    "would-require-new-measurement",
}


def _payload() -> dict[str, Any]:
    value = json.loads(_MATRIX.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _rows_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload["rows"]
    assert isinstance(rows, list)
    return {str(row["id"]): row for row in rows}


def test_matrix_binds_canonical_post_final_frontier() -> None:
    payload = _payload()
    assert payload["schema_version"] == "0.1"
    assert payload["grain_id"] == "SG-000023"
    assert payload["research_issue"] == 91
    assert payload["canonical_activation_main"] == (
        "7da5e1e2efc17e5fdad42e1d80da25139de74317"
    )
    assert payload["activation_post_main_gaxbench_run"] == 36904770004
    assert payload["canonical_sg000022_closeout"] == (
        "421ad093e1b89df69e10c763ec2474853c09d0e3"
    )
    assert payload["sg000022_post_closeout_gaxbench_run"] == 36903592739
    assert payload["source_final_evaluation_run"] == 36886952302
    assert payload["source_artifact_id"] == 11176566473
    assert payload["source_artifact_zip_sha256"] == (
        "8dcd894be6ae184aaf5311417d268a5500b89d0d78d14ee7a79305fbb3071136"
    )
    assert set(payload["allowed_statuses"]) == {
        "available",
        "blocked",
        "unavailable",
        "not-applicable",
    }
    assert all(payload["permanent_post_final_lock"].values())


def test_matrix_covers_every_remaining_p08_analysis_family() -> None:
    payload = _payload()
    rows = _rows_by_id(payload)
    assert set(rows) == _EXPECTED_ROWS
    assert len(rows) == len(payload["rows"])

    contracts = set(payload["contract_catalog"])
    sources = set(payload["evidence_source_catalog"])
    statuses = set(payload["allowed_statuses"])
    for row in rows.values():
        assert row["status"] in statuses
        assert row["contract_ids"]
        assert set(row["contract_ids"]) <= contracts
        assert set(row["evidence_source_ids"]) <= sources
        assert row["allowed_artifacts"]
        assert row["prohibited_interpretation"]
        if row["computation_class"] in _FORBIDDEN_NEW_WORK:
            assert row["status"] == "blocked"
        if row["status"] in {"blocked", "unavailable", "not-applicable"}:
            assert row.get("no_packet_reason")


def test_matrix_preserves_known_negative_and_blocked_boundaries() -> None:
    rows = _rows_by_id(_payload())
    assert rows["evidence-interventions"]["status"] == "blocked"
    assert rows["counterfactual-robustness"]["status"] == "blocked"
    assert rows["fhir-final-action-selection"]["status"] == "blocked"
    assert rows["distribution-shift-slices"]["status"] == "unavailable"
    assert rows["efficiency-hardware"]["status"] == "blocked"
    assert rows["canonical-p08-closeout"]["status"] == "not-applicable"

    laya_prohibitions = rows["reliability-analysis"]["prohibited_interpretation"]
    assert "treat affected Laya confidence as calibrated" in laya_prohibitions

    risk_prohibitions = rows["risk-coverage-analysis"]["prohibited_interpretation"]
    assert (
        "hide DAL unsafe-commit rate 1.0 at target coverage 0.8 or 0.9"
        in risk_prohibitions
    )

    fhir = rows["fhir-final-action-selection"]
    assert fhir["evidence_packet_ids"] == ["EP-SG23-FHIR-BLOCK-001"]
    assert "new FHIR action adapter" in fhir["prohibited_interpretation"]


def test_source_bound_rows_reference_existing_repository_paths() -> None:
    payload = _payload()
    source_catalog = payload["evidence_source_catalog"]
    contract_catalog = payload["contract_catalog"]

    for path in source_catalog.values():
        assert Path(path).exists(), path
    for contract_id, path in contract_catalog.items():
        if contract_id in {"sg20", "sg23"}:
            assert path.startswith("https://github.com/TheHalfMoon/DAL/issues/")
        else:
            assert Path(path).exists(), path


def test_affirmative_available_rows_have_packet_bindings() -> None:
    rows = _rows_by_id(_payload())
    for row in rows.values():
        if row["status"] != "available":
            continue
        assert row["evidence_packet_ids"], row["id"]
        assert not row["computation_class"].startswith("would-require-forbidden")
