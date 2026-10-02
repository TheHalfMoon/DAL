from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from gaxbench.provenance import sha256_file
from gaxbench.schema import StrictModel

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class D2FHIRRuntimeFile(StrictModel):
    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("runtime manifest paths must be safe relative paths")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("runtime file sha256 must be lowercase hexadecimal")
        return value


class D2FHIRRuntimeManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    study: Literal["DAL Study 1"]
    specgrain: Literal["SG-000026"]
    stage: Literal["D2"]
    purpose: str = Field(min_length=1)
    source: dict[str, JsonValue]
    cost_boundary: dict[str, JsonValue]
    scope_boundary: dict[str, JsonValue]
    files: list[D2FHIRRuntimeFile] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_paths(self) -> D2FHIRRuntimeManifest:
        paths = [entry.path for entry in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("runtime manifest file paths must be unique")
        return self


class D2FHIRRuntimeVerification(StrictModel):
    status: Literal["complete", "incomplete"]
    checked_files: int = Field(ge=0)
    missing_paths: list[str]
    mismatched_paths: list[str]


def load_fhir_runtime_manifest(path: str | Path) -> D2FHIRRuntimeManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return D2FHIRRuntimeManifest.model_validate(payload)


def verify_fhir_runtime_root(
    root: str | Path,
    manifest: D2FHIRRuntimeManifest,
) -> D2FHIRRuntimeVerification:
    root_path = Path(root)
    missing: list[str] = []
    mismatched: list[str] = []
    checked = 0
    for entry in manifest.files:
        candidate = root_path / entry.path
        if not candidate.is_file():
            missing.append(entry.path)
            continue
        checked += 1
        if sha256_file(candidate) != entry.sha256:
            mismatched.append(entry.path)
    return D2FHIRRuntimeVerification(
        status="complete" if not missing and not mismatched else "incomplete",
        checked_files=checked,
        missing_paths=sorted(missing),
        mismatched_paths=sorted(mismatched),
    )
