from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"expected patch site not found: {label}")
    return text.replace(old, new, 1)


builder = Path("tools/build_sg000023_paper_evidence.py")
text = builder.read_text(encoding="utf-8")

text = replace_once(
    text,
    "def _evidence_packets() -> dict[str, Any]:\n",
    "def _evidence_packets(matrix: dict[str, Any]) -> dict[str, Any]:\n",
    "evidence packet signature",
)

text = replace_once(
    text,
    '''            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(CALIBRATION_PATH),
            ],''',
    '''            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(CALIBRATION_PATH),
                _rel(CONTRACT_PATH),
            ],''',
    "calibration packet sources",
)

text = replace_once(
    text,
    '''            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
                _rel(CONTRACT_PATH),
            ],''',
    '''            "canonical_sources": [
                _rel(FINAL_ROOT / "raw-pubmedqa-predictions.json"),
                _rel(FINAL_ROOT / "raw-native-abstention-predictions.json"),
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(CALIBRATION_PATH),
                _rel(CONTRACT_PATH),
            ],''',
    "figure packet sources",
)

text = replace_once(
    text,
    '''    ]
    return {"schema_version": "0.1", "grain_id": "SG-000023", "packets": packets}


def _claim_ledger''',
    '''    ]

    packets.extend(
        [
            {
                "packet_id": "EP-SG23-PACKETS-INDEX",
                "status": "supported",
                "canonical_sources": [_rel(MATRIX_PATH), _rel(CONTRACT_PATH)],
                "derived_artifacts": [],
                "scope": "index packet binding the declared SG-000023 evidence-packet namespace",
            },
            {
                "packet_id": "EP-SG23-CLAIMS-INDEX",
                "status": "supported",
                "canonical_sources": [
                    _rel(MATRIX_PATH),
                    _rel(FINAL_ROOT / "manifest.json"),
                    _rel(FINAL_ROOT / "metrics.json"),
                ],
                "derived_artifacts": ["claim_ledger.json"],
                "scope": "claim-ledger index with supported and non-exportable dispositions",
            },
        ]
    )

    declared: dict[str, str] = {}
    for row in matrix["rows"]:
        for packet_id in row.get("evidence_packet_ids", []):
            declared[packet_id] = row["id"]
    present = {packet["packet_id"] for packet in packets}
    for packet_id in sorted(set(declared) - present):
        packets.append(
            {
                "packet_id": packet_id,
                "status": "declared-future-stage",
                "canonical_sources": [_rel(MATRIX_PATH)],
                "derived_artifacts": [],
                "scope": (
                    f"declared by availability-matrix row {declared[packet_id]}; "
                    "materialization belongs to a later SG-000023 stage"
                ),
            }
        )

    return {"schema_version": "0.1", "grain_id": "SG-000023", "packets": packets}


def _claim_ledger''',
    "evidence packet registry completion",
)

text = replace_once(
    text,
    '''            "evidence_packet_id": "EP-SG23-ACTION-001",
            "canonical_source_paths": [
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(CALIBRATION_PATH),
            ],''',
    '''            "evidence_packet_id": "EP-SG23-CAL-001",
            "canonical_source_paths": [
                _rel(FINAL_ROOT / "metrics.json"),
                _rel(CALIBRATION_PATH),
            ],''',
    "C003 calibration packet binding",
)

text = replace_once(
    text,
    '        "evidence_packets.json": _evidence_packets(),',
    '        "evidence_packets.json": _evidence_packets(matrix),',
    "evidence packet builder call",
)

text = replace_once(
    text,
    '''    comparison = next(
        row
        for row in metrics["primary_comparisons"]
        if row["benchmark"] == "gax-native-abstention-pqal" and row["metric"] == "risk_at_80"
    )
    return {''',
    '''    canonical_comparison = next(
        row
        for row in metrics["primary_comparisons"]
        if row["benchmark"] == "gax-native-abstention-pqal" and row["metric"] == "risk_at_80"
    )
    comparison = json.loads(json.dumps(canonical_comparison))
    for key in ("estimate", "ci_low", "ci_high"):
        comparison["paired_bootstrap"][key] = round(
            float(comparison["paired_bootstrap"][key]), 4
        )
    return {''',
    "selective display comparison",
)

text = replace_once(
    text,
    '''        "primary_comparison": comparison,
        "mandatory_warning": (''',
    '''        "primary_comparison": comparison,
        "canonical_primary_comparison": canonical_comparison,
        "mandatory_warning": (''',
    "canonical selective comparison retention",
)

builder.write_text(text, encoding="utf-8", newline="\n")

tests = Path("tests/test_p08_sg000023_paper_evidence.py")
t = tests.read_text(encoding="utf-8")

t = replace_once(
    t,
    'EVIDENCE = ROOT / "registry" / "p08_sg000023_paper_evidence"\n',
    '''EVIDENCE = ROOT / "registry" / "p08_sg000023_paper_evidence"
ARTIFACT_NAMES = {
    "claim_ledger.json",
    "evidence_boundaries.json",
    "evidence_packets.json",
    "fhir_block_table.json",
    "main_results.json",
    "provenance_index.json",
    "qualitative_examples.json",
    "reliability_source_data.json",
    "risk_coverage_source_data.json",
    "selective_results.json",
}
''',
    "artifact catalog constant",
)

t = replace_once(
    t,
    '    assert "10 artifacts" in result.stdout\n',
    '    assert f"{len(ARTIFACT_NAMES)} artifacts" in result.stdout\n',
    "dynamic artifact stdout assertion",
)

t = replace_once(
    t,
    '''    assert {path.name for path in EVIDENCE.glob("*.json")} == {
        "claim_ledger.json",
        "evidence_boundaries.json",
        "evidence_packets.json",
        "fhir_block_table.json",
        "main_results.json",
        "provenance_index.json",
        "qualitative_examples.json",
        "reliability_source_data.json",
        "risk_coverage_source_data.json",
        "selective_results.json",
    }
''',
    '    assert {path.name for path in EVIDENCE.glob("*.json")} == ARTIFACT_NAMES\n',
    "single artifact catalog assertion",
)

t = replace_once(
    t,
    '    assert len(provenance["artifact_sha256"]) == 9\n',
    '''    # provenance_index.json cannot hash itself without a recursive digest.
    assert len(provenance["artifact_sha256"]) == len(ARTIFACT_NAMES) - 1
''',
    "self-exclusion provenance count",
)

t += '''

def test_packet_registry_covers_every_declared_matrix_packet() -> None:
    matrix = json.loads(
        (ROOT / "registry" / "p08_sg000023_evidence_availability_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    declared = {
        packet_id
        for row in matrix["rows"]
        for packet_id in row.get("evidence_packet_ids", [])
    }
    packets = _load("evidence_packets.json")["packets"]
    by_id = {row["packet_id"]: row for row in packets}
    assert declared <= set(by_id)
    assert by_id["EP-SG23-PACKETS-INDEX"]["status"] == "supported"
    assert by_id["EP-SG23-CLAIMS-INDEX"]["status"] == "supported"


def test_laya_calibration_claim_uses_calibration_packet() -> None:
    ledger = _load("claim_ledger.json")
    claim = next(row for row in ledger["claims"] if row["claim_id"] == "SG23-C003")
    assert claim["evidence_packet_id"] == "EP-SG23-CAL-001"
    packets = {
        row["packet_id"]: row for row in _load("evidence_packets.json")["packets"]
    }
    cal_sources = set(packets["EP-SG23-CAL-001"]["canonical_sources"])
    assert set(claim["canonical_source_paths"]) <= cal_sources
    assert "registry/p08_sg000022_final_evaluation/metrics.json" in cal_sources


def test_selective_table_keeps_raw_comparison_and_clean_display_values() -> None:
    table = _load("selective_results.json")
    display = table["primary_comparison"]["paired_bootstrap"]
    canonical = table["canonical_primary_comparison"]["paired_bootstrap"]
    assert display["estimate"] == -0.0125
    assert display["ci_low"] == -0.02
    assert display["ci_high"] == -0.005
    assert canonical["estimate"] != display["estimate"]
'''

tests.write_text(t, encoding="utf-8", newline="\n")
