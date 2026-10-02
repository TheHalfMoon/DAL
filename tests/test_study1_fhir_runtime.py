from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from gaxbench.study1_fhir_runtime import (
    D2FHIRRuntimeFile,
    D2FHIRRuntimeManifest,
    load_fhir_runtime_manifest,
    verify_fhir_runtime_root,
)

MANIFEST = Path("registry/study1_sg000026_fhir_runtime_manifest.json")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_canonical_runtime_manifest_freezes_open_zero_cost_source() -> None:
    manifest = load_fhir_runtime_manifest(MANIFEST)
    assert len(manifest.files) == 32
    assert manifest.source["version"] == "2.1.0"
    assert manifest.source["access_policy"] == "open-access"
    assert manifest.source["license"] == "ODbL-1.0"
    assert manifest.source["checksum_manifest_sha256"] == (
        "582688e274af7523f4db1cdebcd88395628a0256084bc0cc20b14884a418b69c"
    )
    assert manifest.cost_boundary["download_cost_usd"] == 0
    assert manifest.cost_boundary["paid_cloud_required"] is False
    assert manifest.scope_boundary["sealed_final_role_accessed"] is False


def test_canonical_manifest_pins_representative_fhir_files() -> None:
    manifest = load_fhir_runtime_manifest(MANIFEST)
    by_path = {entry.path: entry.sha256 for entry in manifest.files}
    assert by_path["fhir/MimicPatient.ndjson.gz"] == (
        "f64c61f64aaed317ddb013276515deaf9ca69815d5c0d70ca372f2a75284ce16"
    )
    assert by_path["fhir/MimicEncounter.ndjson.gz"] == (
        "01d3583e4c8b9fbfde87baa8a6cf1cc6bf53c1db45c0b64120fcb80c34e6b17b"
    )
    assert by_path["fhir/MimicMedicationRequest.ndjson.gz"] == (
        "3f446cd92a820dff3623c674f4d1f13ea6cc7f3c157f3584e9c17d8502f33456"
    )
    assert by_path["fhir/MimicSpecimen.ndjson.gz"] == (
        "3429ad1ced3672be4597636fd925130717192efc917be6ab405d76ab1867c24d"
    )


def _fixture_manifest(entries: list[D2FHIRRuntimeFile]) -> D2FHIRRuntimeManifest:
    return D2FHIRRuntimeManifest(
        study="DAL Study 1",
        specgrain="SG-000026",
        stage="D2",
        purpose="test",
        source={},
        cost_boundary={},
        scope_boundary={},
        files=entries,
    )


def test_offline_verifier_reports_complete_runtime(tmp_path: Path) -> None:
    one = b"one\n"
    two = b"two\n"
    (tmp_path / "fhir").mkdir()
    (tmp_path / "fhir" / "one.ndjson.gz").write_bytes(one)
    (tmp_path / "fhir" / "two.ndjson.gz").write_bytes(two)
    manifest = _fixture_manifest(
        [
            D2FHIRRuntimeFile(path="fhir/one.ndjson.gz", sha256=_sha256(one)),
            D2FHIRRuntimeFile(path="fhir/two.ndjson.gz", sha256=_sha256(two)),
        ]
    )
    result = verify_fhir_runtime_root(tmp_path, manifest)
    assert result.status == "complete"
    assert result.checked_files == 2
    assert result.missing_paths == []
    assert result.mismatched_paths == []


def test_offline_verifier_reports_missing_and_mismatch(tmp_path: Path) -> None:
    (tmp_path / "present.txt").write_bytes(b"actual")
    manifest = _fixture_manifest(
        [
            D2FHIRRuntimeFile(path="present.txt", sha256=_sha256(b"expected")),
            D2FHIRRuntimeFile(path="missing.txt", sha256=_sha256(b"missing")),
        ]
    )
    result = verify_fhir_runtime_root(tmp_path, manifest)
    assert result.status == "incomplete"
    assert result.checked_files == 1
    assert result.missing_paths == ["missing.txt"]
    assert result.mismatched_paths == ["present.txt"]


def test_runtime_manifest_rejects_unsafe_paths_and_bad_hashes() -> None:
    with pytest.raises(ValidationError, match="safe relative"):
        D2FHIRRuntimeFile(path="../secret", sha256="0" * 64)
    with pytest.raises(ValidationError, match="lowercase hexadecimal"):
        D2FHIRRuntimeFile(path="safe.txt", sha256="G" * 64)


def test_runtime_manifest_rejects_duplicate_paths() -> None:
    entry = D2FHIRRuntimeFile(path="same.txt", sha256="0" * 64)
    with pytest.raises(ValidationError, match="unique"):
        _fixture_manifest([entry, entry])
