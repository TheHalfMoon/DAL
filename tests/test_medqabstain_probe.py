from __future__ import annotations

import pytest

from gaxbench.medqabstain_probe import parse_hub_metadata


def payload() -> dict[str, object]:
    return {
        "sha": "a" * 40,
        "lastModified": "2026-06-24T00:00:00.000Z",
        "private": False,
        "gated": False,
        "disabled": False,
        "tags": ["format:parquet", "license:mit", "modality:text"],
        "cardData": {"license": "mit"},
        "siblings": [
            {"rfilename": "README.md", "size": 100},
            {
                "rfilename": "bench/train-00000-of-00001.parquet",
                "lfs": {"oid": "sha256:" + "b" * 64, "size": 1234},
            },
            {
                "rfilename": "images.zip",
                "lfs": {"oid": "sha256:" + "c" * 64, "size": 5678},
            },
        ],
    }


def test_probe_freezes_revision_and_sibling_manifest() -> None:
    probe = parse_hub_metadata(payload())
    assert probe.dataset_revision == "a" * 40
    assert probe.card_license == "mit"
    assert probe.parquet_file_count == 1
    assert probe.image_archive_count == 1
    assert probe.sibling_count == 3
    assert len(probe.sibling_manifest_sha256) == 64
    assert [item.path for item in probe.siblings] == [
        "README.md",
        "bench/train-00000-of-00001.parquet",
        "images.zip",
    ]


def test_probe_rejects_moving_main_without_immutable_sha() -> None:
    data = payload()
    data["sha"] = "main"
    with pytest.raises(ValueError, match="40-character"):
        parse_hub_metadata(data)


def test_probe_rejects_private_dataset() -> None:
    data = payload()
    data["private"] = True
    with pytest.raises(ValueError, match="publicly accessible"):
        parse_hub_metadata(data)


def test_probe_rejects_missing_siblings() -> None:
    data = payload()
    data["siblings"] = []
    with pytest.raises(ValueError, match="non-empty siblings"):
        parse_hub_metadata(data)


def test_probe_rejects_invalid_lfs_digest() -> None:
    data = payload()
    siblings = data["siblings"]
    assert isinstance(siblings, list)
    lfs_entry = siblings[1]
    assert isinstance(lfs_entry, dict)
    lfs_entry["lfs"] = {"oid": "sha256:not-a-digest", "size": 1}
    with pytest.raises(ValueError, match="SHA-256"):
        parse_hub_metadata(data)
