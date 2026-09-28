from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from gaxbench.provenance import canonical_json_sha256
from gaxbench.schema import StrictModel

MEDAGENTBENCH_REPOSITORY = "stanfordmlgroup/MedAgentBench"
MEDAGENTBENCH_SOURCE_COMMIT = "99260117137b09f04837a8c18d18a1107efa55ae"
MEDAGENTBENCH_TASK_PATH = "data/medagentbench/test_data_v2.json"
MEDAGENTBENCH_TASK_BLOB_SHA1 = "7f568f041f9d22e11b5bf31b80efd2219aaaf14f"
MEDAGENTBENCH_TASK_BYTES = 118276
MEDAGENTBENCH_FUNCTION_PATH = "data/medagentbench/funcs_v1.json"
MEDAGENTBENCH_FUNCTION_BLOB_SHA1 = "9b15acc0ccf402ede8964261c371d6a00889b436"
MEDAGENTBENCH_FUNCTION_BYTES = 12571
MEDAGENTBENCH_REPOSITORY_LICENSE = "MIT"
MEDAGENTBENCH_ROLE_REVISION = "gax-medagentbench-final-test-only-v0.1"
MEDAGENTBENCH_NEAR_DUPLICATE_SHINGLES = 5
MEDAGENTBENCH_NEAR_DUPLICATE_THRESHOLD = 0.80
MEDAGENTBENCH_DOCKER_REFERENCE = "jyxsu6/medagentbench:latest"
MEDAGENTBENCH_REFSOL_URL = (
    "https://stanfordmedicine.box.com/s/fizv0unyjgkb1r3a83rfn5p3dc673uho"
)

MEDAGENTBENCH_TASK_RAW_URL = (
    "https://raw.githubusercontent.com/"
    f"{MEDAGENTBENCH_REPOSITORY}/{MEDAGENTBENCH_SOURCE_COMMIT}/{MEDAGENTBENCH_TASK_PATH}"
)
MEDAGENTBENCH_FUNCTION_RAW_URL = (
    "https://raw.githubusercontent.com/"
    f"{MEDAGENTBENCH_REPOSITORY}/{MEDAGENTBENCH_SOURCE_COMMIT}/"
    f"{MEDAGENTBENCH_FUNCTION_PATH}"
)

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


@dataclass(frozen=True)
class _VisibleTask:
    task_id: str
    family: str
    normalized_text: str


class MedAgentBenchCorpusProbe(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["medagentbench"] = "medagentbench"
    source_repository: Literal["stanfordmlgroup/MedAgentBench"] = MEDAGENTBENCH_REPOSITORY
    source_commit: Literal["99260117137b09f04837a8c18d18a1107efa55ae"] = (
        MEDAGENTBENCH_SOURCE_COMMIT
    )
    repository_license: Literal["MIT"] = "MIT"
    task_path: Literal["data/medagentbench/test_data_v2.json"] = MEDAGENTBENCH_TASK_PATH
    task_blob_sha1: Literal["7f568f041f9d22e11b5bf31b80efd2219aaaf14f"] = (
        MEDAGENTBENCH_TASK_BLOB_SHA1
    )
    task_sha256: str
    task_bytes: Literal[118276] = MEDAGENTBENCH_TASK_BYTES
    task_count: int = Field(ge=1)
    unique_task_id_count: int = Field(ge=1)
    duplicate_task_id_count: int = Field(ge=0)
    task_field_names: list[str]
    task_family_counts: dict[str, int]
    exact_duplicate_visible_task_count: int = Field(ge=0)
    near_duplicate_visible_pair_count: int = Field(ge=0)
    cross_family_near_duplicate_pair_count: int = Field(ge=0)
    near_duplicate_pair_digest: str
    function_path: Literal["data/medagentbench/funcs_v1.json"] = MEDAGENTBENCH_FUNCTION_PATH
    function_blob_sha1: Literal["9b15acc0ccf402ede8964261c371d6a00889b436"] = (
        MEDAGENTBENCH_FUNCTION_BLOB_SHA1
    )
    function_sha256: str
    function_bytes: Literal[12571] = MEDAGENTBENCH_FUNCTION_BYTES
    function_count: int = Field(ge=1)
    unique_function_name_count: int = Field(ge=1)
    duplicate_function_name_count: int = Field(ge=0)
    function_field_names: list[str]
    raw_task_text_serialized: Literal[False] = False
    raw_gold_serialized: Literal[False] = False
    raw_patient_identifiers_serialized: Literal[False] = False
    public_benchmark_pretraining_contamination: Literal["unresolved-public-benchmark"] = (
        "unresolved-public-benchmark"
    )
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_probe(self) -> MedAgentBenchCorpusProbe:
        _require_sha256(self.task_sha256, "task_sha256")
        _require_sha256(self.function_sha256, "function_sha256")
        _require_sha256(self.near_duplicate_pair_digest, "near_duplicate_pair_digest")
        if self.task_count != self.unique_task_id_count + self.duplicate_task_id_count:
            raise ValueError("task counts do not reconcile")
        if sum(self.task_family_counts.values()) != self.task_count:
            raise ValueError("task_family_counts must sum to task_count")
        return self


class MedAgentBenchRoleManifest(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["medagentbench"] = "medagentbench"
    role_revision: Literal["gax-medagentbench-final-test-only-v0.1"] = (
        MEDAGENTBENCH_ROLE_REVISION
    )
    role: Literal["final-test"] = "final-test"
    item_count: int = Field(ge=1)
    membership_sha256: str
    membership_uses_task_ids_only: Literal[True] = True
    training_use_forbidden: Literal[True] = True
    calibration_use_forbidden: Literal[True] = True
    prompt_selection_use_forbidden: Literal[True] = True
    threshold_selection_use_forbidden: Literal[True] = True
    model_selection_use_forbidden: Literal[True] = True
    final_test_access: Literal["sealed"] = "sealed"
    test_gold_serialized: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> MedAgentBenchRoleManifest:
        _require_sha256(self.membership_sha256, "membership_sha256")
        return self


class MedAgentBenchRuntimeStatus(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["medagentbench"] = "medagentbench"
    official_runtime_status: Literal["blocked"] = "blocked"
    docker_reference: Literal["jyxsu6/medagentbench:latest"] = MEDAGENTBENCH_DOCKER_REFERENCE
    docker_reference_is_mutable_tag: Literal[True] = True
    docker_terms_verified: Literal[False] = False
    docker_patient_environment_rights_verified: Literal[False] = False
    refsol_url: Literal[
        "https://stanfordmedicine.box.com/s/fizv0unyjgkb1r3a83rfn5p3dc673uho"
    ] = MEDAGENTBENCH_REFSOL_URL
    refsol_immutable_revision_verified: Literal[False] = False
    refsol_license_verified: Literal[False] = False
    official_scoring_depends_on_refsol: Literal[True] = True
    official_runtime_required_for_corpus_identity: Literal[False] = False
    official_success_rate_claim_allowed: Literal[False] = False
    blocked_reason: str = Field(min_length=1)


class MedAgentBenchQualificationReport(StrictModel):
    schema_version: Literal["0.1"] = "0.1"
    dataset_id: Literal["medagentbench"] = "medagentbench"
    corpus_status: Literal["qualified", "blocked"]
    official_runtime_status: Literal["blocked"] = "blocked"
    task_sha256: str
    function_sha256: str
    role_manifest_sha256: str
    audit_sha256: str
    repository_license: Literal["MIT"] = "MIT"
    role_revision: Literal["gax-medagentbench-final-test-only-v0.1"] = (
        MEDAGENTBENCH_ROLE_REVISION
    )
    raw_upstream_files_committed_to_gax: Literal[False] = False
    official_success_rate_claim_allowed: Literal[False] = False
    final_test_access: Literal["sealed"] = "sealed"

    @model_validator(mode="after")
    def validate_hashes(self) -> MedAgentBenchQualificationReport:
        for field, value in (
            ("task_sha256", self.task_sha256),
            ("function_sha256", self.function_sha256),
            ("role_manifest_sha256", self.role_manifest_sha256),
            ("audit_sha256", self.audit_sha256),
        ):
            _require_sha256(value, field)
        return self


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_frozen_sources(task_bytes: bytes, function_bytes: bytes) -> None:
    if len(task_bytes) != MEDAGENTBENCH_TASK_BYTES:
        raise ValueError("task corpus byte count differs from frozen source")
    if git_blob_sha1(task_bytes) != MEDAGENTBENCH_TASK_BLOB_SHA1:
        raise ValueError("task corpus Git blob differs from frozen source")
    if len(function_bytes) != MEDAGENTBENCH_FUNCTION_BYTES:
        raise ValueError("function catalog byte count differs from frozen source")
    if git_blob_sha1(function_bytes) != MEDAGENTBENCH_FUNCTION_BLOB_SHA1:
        raise ValueError("function catalog Git blob differs from frozen source")


def qualify_medagentbench(
    task_bytes: bytes,
    function_bytes: bytes,
) -> tuple[
    MedAgentBenchCorpusProbe,
    MedAgentBenchRoleManifest,
    MedAgentBenchRuntimeStatus,
    MedAgentBenchQualificationReport,
]:
    verify_frozen_sources(task_bytes, function_bytes)
    tasks = _load_list_of_objects(task_bytes, "task corpus")
    functions = _load_list_of_objects(function_bytes, "function catalog")
    visible_tasks = _visible_tasks(tasks)

    task_ids = [task.task_id for task in visible_tasks]
    duplicate_task_ids = len(task_ids) - len(set(task_ids))
    if duplicate_task_ids:
        raise ValueError("duplicate task IDs block corpus qualification")

    family_counts = dict(sorted(Counter(task.family for task in visible_tasks).items()))
    exact_duplicates = len(visible_tasks) - len({task.normalized_text for task in visible_tasks})
    near_pairs, cross_family_pairs, pair_digest = _near_duplicate_summary(visible_tasks)

    function_names = [str(item.get("name", "")) for item in functions]
    if any(not name for name in function_names):
        raise ValueError("every function entry must have a non-empty name")
    duplicate_function_names = len(function_names) - len(set(function_names))

    task_sha256 = hashlib.sha256(task_bytes).hexdigest()
    function_sha256 = hashlib.sha256(function_bytes).hexdigest()
    membership_sha256 = canonical_json_sha256(sorted(task_ids))

    probe = MedAgentBenchCorpusProbe(
        task_sha256=task_sha256,
        task_count=len(tasks),
        unique_task_id_count=len(set(task_ids)),
        duplicate_task_id_count=duplicate_task_ids,
        task_field_names=sorted({key for item in tasks for key in item}),
        task_family_counts=family_counts,
        exact_duplicate_visible_task_count=exact_duplicates,
        near_duplicate_visible_pair_count=near_pairs,
        cross_family_near_duplicate_pair_count=cross_family_pairs,
        near_duplicate_pair_digest=pair_digest,
        function_sha256=function_sha256,
        function_count=len(functions),
        unique_function_name_count=len(set(function_names)),
        duplicate_function_name_count=duplicate_function_names,
        function_field_names=sorted({key for item in functions for key in item}),
    )
    manifest = MedAgentBenchRoleManifest(
        item_count=len(tasks),
        membership_sha256=membership_sha256,
    )
    runtime = MedAgentBenchRuntimeStatus(
        blocked_reason=(
            "Official scoring depends on external refsol.py and a Docker-hosted FHIR environment. "
            "The frozen repository does not provide immutable refsol identity/license evidence, "
            "and the referenced Docker image uses a mutable latest tag with patient-environment "
            "rights not established by the repository MIT license."
        )
    )
    audit_payload = {
        "duplicate_task_id_count": duplicate_task_ids,
        "exact_duplicate_visible_task_count": exact_duplicates,
        "near_duplicate_visible_pair_count": near_pairs,
        "cross_family_near_duplicate_pair_count": cross_family_pairs,
        "near_duplicate_pair_digest": pair_digest,
        "public_benchmark_pretraining_contamination": "unresolved-public-benchmark",
        "role_revision": MEDAGENTBENCH_ROLE_REVISION,
    }
    report = MedAgentBenchQualificationReport(
        corpus_status="qualified",
        task_sha256=task_sha256,
        function_sha256=function_sha256,
        role_manifest_sha256=canonical_json_sha256(manifest.model_dump(mode="json")),
        audit_sha256=canonical_json_sha256(audit_payload),
    )
    return probe, manifest, runtime, report


def write_medagentbench_evidence(
    task_path: str | Path,
    function_path: str | Path,
    output_dir: str | Path,
) -> None:
    task_bytes = Path(task_path).read_bytes()
    function_bytes = Path(function_path).read_bytes()
    probe, manifest, runtime, report = qualify_medagentbench(task_bytes, function_bytes)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, StrictModel] = {
        "source_probe.json": probe,
        "role_manifest.json": manifest,
        "runtime_status.json": runtime,
        "qualification.json": report,
    }
    for name, payload in payloads.items():
        (output / name).write_text(
            json.dumps(payload.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _load_list_of_objects(data: bytes, label: str) -> list[dict[str, Any]]:
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{label} must be a non-empty JSON list")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{label} entries must be JSON objects")
    return payload


def _visible_tasks(tasks: list[dict[str, Any]]) -> list[_VisibleTask]:
    result: list[_VisibleTask] = []
    for item in tasks:
        task_id = str(item.get("id", ""))
        instruction = item.get("instruction")
        context = item.get("context", "")
        if not task_id or not isinstance(instruction, str) or not isinstance(context, str):
            raise ValueError("tasks require id, string instruction, and string context")
        family = task_id.split("_", 1)[0]
        normalized_text = " ".join(_TOKEN_RE.findall(f"{instruction} {context}".lower()))
        result.append(_VisibleTask(task_id=task_id, family=family, normalized_text=normalized_text))
    return result


def _near_duplicate_summary(tasks: list[_VisibleTask]) -> tuple[int, int, str]:
    shingles = {
        task.task_id: _shingles(task.normalized_text, MEDAGENTBENCH_NEAR_DUPLICATE_SHINGLES)
        for task in tasks
    }
    pair_tokens: list[str] = []
    near_pairs = 0
    cross_family_pairs = 0
    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            score = _jaccard(shingles[left.task_id], shingles[right.task_id])
            if score < MEDAGENTBENCH_NEAR_DUPLICATE_THRESHOLD:
                continue
            near_pairs += 1
            if left.family != right.family:
                cross_family_pairs += 1
            family_pair = ":".join(sorted((left.family, right.family)))
            pair_tokens.append(f"{family_pair}:{score:.6f}")
    return near_pairs, cross_family_pairs, canonical_json_sha256(sorted(pair_tokens))


def _shingles(text: str, size: int) -> frozenset[tuple[str, ...]]:
    tokens = text.split()
    if len(tokens) < size:
        return frozenset({tuple(tokens)}) if tokens else frozenset()
    return frozenset(tuple(tokens[index : index + size]) for index in range(len(tokens) - size + 1))


def _jaccard(left: frozenset[tuple[str, ...]], right: frozenset[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
