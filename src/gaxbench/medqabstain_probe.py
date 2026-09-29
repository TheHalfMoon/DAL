from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

MEDQABSTAIN_DATASET_ID = "disi-unibo-nlp/MedQAbstain"
MEDQABSTAIN_RESEARCH_REPOSITORY = "disi-unibo-nlp/llm-medical-abstention"
MEDQABSTAIN_RESEARCH_REVISION = "3c296b55686f1bcf3e0eccbdd12bfc57c4bfdd1d"
HF_API_URL = f"https://huggingface.co/api/datasets/{MEDQABSTAIN_DATASET_ID}?blobs=true"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class MedQAbstainSibling(StrictModel):
    path: str = Field(min_length=1)
    size: int | None = Field(default=None, ge=0)
    lfs_sha256: str | None = None

    @model_validator(mode="after")
    def validate_lfs(self) -> MedQAbstainSibling:
        if self.lfs_sha256 is not None:
            _require_sha256(self.lfs_sha256, "lfs_sha256")
        return self


class MedQAbstainHubProbe(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["disi-unibo-nlp/MedQAbstain"] = "disi-unibo-nlp/MedQAbstain"
    dataset_revision: str
    dataset_last_modified: str | None = None
    private: bool
    gated: bool | str | None = None
    disabled: bool | None = None
    card_license: str | list[str] | None = None
    tags: list[str]
    sibling_count: int = Field(ge=1)
    siblings: list[MedQAbstainSibling] = Field(min_length=1)
    sibling_manifest_sha256: str
    parquet_file_count: int = Field(ge=0)
    image_archive_count: int = Field(ge=0)
    immutable_revision_verified: Literal[True] = True
    raw_dataset_rows_serialized: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_probe(self) -> MedQAbstainHubProbe:
        _require_git_sha(self.dataset_revision, "dataset_revision")
        _require_sha256(self.sibling_manifest_sha256, "sibling_manifest_sha256")
        if self.sibling_count != len(self.siblings):
            raise ValueError("sibling_count must equal siblings length")
        if self.private:
            raise ValueError(
                "MedQAbstain dataset must be publicly accessible for zero-cost qualification"
            )
        if self.disabled is True:
            raise ValueError("MedQAbstain dataset is disabled")
        return self


def parse_hub_metadata(payload: dict[str, Any]) -> MedQAbstainHubProbe:
    revision = str(payload.get("sha", ""))
    _require_git_sha(revision, "dataset sha")

    siblings_payload = payload.get("siblings")
    if not isinstance(siblings_payload, list) or not siblings_payload:
        raise ValueError("Hugging Face metadata must contain non-empty siblings")

    siblings: list[MedQAbstainSibling] = []
    for raw in siblings_payload:
        if not isinstance(raw, dict):
            raise ValueError("every sibling must be an object")
        path = raw.get("rfilename")
        if not isinstance(path, str) or not path:
            raise ValueError("every sibling requires rfilename")
        lfs = raw.get("lfs")
        lfs_sha: str | None = None
        size: int | None = None
        if isinstance(lfs, dict):
            oid = lfs.get("oid")
            if isinstance(oid, str):
                lfs_sha = oid.removeprefix("sha256:")
            lfs_size = lfs.get("size")
            if isinstance(lfs_size, int):
                size = lfs_size
        if size is None and isinstance(raw.get("size"), int):
            size = raw["size"]
        siblings.append(MedQAbstainSibling(path=path, size=size, lfs_sha256=lfs_sha))

    siblings.sort(key=lambda item: item.path)
    sibling_manifest = [item.model_dump(mode="json") for item in siblings]
    card_data = payload.get("cardData")
    card_license: str | list[str] | None = None
    if isinstance(card_data, dict):
        raw_license = card_data.get("license")
        if isinstance(raw_license, str):
            card_license = raw_license
        elif isinstance(raw_license, list) and all(
            isinstance(value, str) for value in raw_license
        ):
            card_license = list(raw_license)

    tags = payload.get("tags")
    clean_tags = (
        sorted(value for value in tags if isinstance(value, str))
        if isinstance(tags, list)
        else []
    )
    parquet_count = sum(item.path.endswith(".parquet") for item in siblings)
    image_archive_count = sum(
        item.path.lower().endswith((".zip", ".tar", ".tar.gz"))
        and "image" in item.path.lower()
        for item in siblings
    )

    return MedQAbstainHubProbe(
        dataset_revision=revision,
        dataset_last_modified=(
            str(payload["lastModified"]) if payload.get("lastModified") is not None else None
        ),
        private=bool(payload.get("private", False)),
        gated=payload.get("gated"),
        disabled=payload.get("disabled") if isinstance(payload.get("disabled"), bool) else None,
        card_license=card_license,
        tags=clean_tags,
        sibling_count=len(siblings),
        siblings=siblings,
        sibling_manifest_sha256=canonical_json_sha256(sibling_manifest),
        parquet_file_count=parquet_count,
        image_archive_count=image_archive_count,
    )


def metadata_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m gaxbench.medqabstain_probe")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw = Path(args.metadata).read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise SystemExit("Hugging Face API payload must be a JSON object")
    probe = parse_hub_metadata(payload)
    output = {
        **probe.model_dump(mode="json"),
        "metadata_response_sha256": metadata_sha256(raw),
        "research_repository": MEDQABSTAIN_RESEARCH_REPOSITORY,
        "research_revision": MEDQABSTAIN_RESEARCH_REVISION,
    }
    Path(args.output).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "dataset_revision": probe.dataset_revision,
                "sibling_count": probe.sibling_count,
                "parquet_file_count": probe.parquet_file_count,
                "image_archive_count": probe.image_archive_count,
                "card_license": probe.card_license,
                "sibling_manifest_sha256": probe.sibling_manifest_sha256,
            },
            sort_keys=True,
        )
    )


def _require_git_sha(value: str, field: str) -> None:
    if _SHA40.fullmatch(value) is None:
        raise ValueError(f"{field} must be a 40-character lowercase hexadecimal git SHA")


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


if __name__ == "__main__":
    main()
