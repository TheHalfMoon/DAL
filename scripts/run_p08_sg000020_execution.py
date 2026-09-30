from __future__ import annotations

import argparse
import ast
import csv
import gc
import gzip
import hashlib
import importlib.util
import json
import os
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from gaxbench.fhir import FHIR_REPRESENTATION_REVISION, render_fhir_resource, validate_fhir_resource
from gaxbench import fhir_agentbench_qualification as fq
from gaxbench.p08_calibration_execution import (
    AuthorizationCandidate,
    CalibrationEvidence,
    FhirRepresentationEvidence,
    artifact_digest,
    fit_platt,
    fit_temperature,
    frozen_ecal_ledger,
    select_fhir_representation,
)
from gaxbench.p08_paper_models import PaperTrainingContract, training_contract_digest
from gaxbench.p08_protocol_selection import PAPER_CHECKPOINT_SHA256, SG000020_CONTRACT_SHA256
from gaxbench.p08_real_systems import DevelopmentTrainingManifest
from gaxbench.provenance import canonical_json_sha256, sha256_file
from gaxbench.pubmedqa import PubMedQASplitManifest, convert_record, load_frozen_pqal

_ACTION_ORDER = ("maybe", "no", "yes")
_REQUIRED_SYSTEM_DIGESTS = {
    "gax-paper-candidate": "0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b",
    "clinical-encoder": "b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388",
    "laya": "b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534",
}


def _load_script(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pubmedqa-source", required=True)
    parser.add_argument("--pubmedqa-split-manifest", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--training-contract", required=True)
    parser.add_argument("--fhir-agentbench-csv", required=True)
    parser.add_argument("--physionet-root", required=True)
    parser.add_argument("--physionet-sha256s", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return sha256_file(path)


def _model_json(path: Path, model: Any) -> str:
    return _write_json(path, model.model_dump(mode="json"))


def _require_source_revision(value: str) -> None:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("source revision must be an exact lowercase git SHA")


def _reconstruct_paper_checkpoint(
    *,
    source: Path,
    development_manifest_path: Path,
    training_contract_path: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], PaperTrainingContract, Any, Any]:
    d03 = _load_script("dal_p08_d03_sg20", Path(__file__).with_name("run_p08_d03_assurance.py"))
    shared = d03.S
    manifest = shared._load_json_model(development_manifest_path, DevelopmentTrainingManifest)
    contract = shared._load_json_model(training_contract_path, PaperTrainingContract)
    contract_sha = training_contract_digest(contract)
    train, selection = shared._selected_records(source, manifest)

    import torch
    import transformers

    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))
    torch.use_deterministic_algorithms(True)
    embeddings = shared._prepare_embeddings(
        train,
        selection,
        contract,
        torch=torch,
        transformers=transformers,
    )
    seed = 0
    control, _control_history, _control_selected = shared._train_control(
        embeddings, contract, seed, torch=torch
    )
    assurance, _paper_history, paper_selected = d03._train_assurance(
        embeddings, contract, control, torch
    )
    paper_action = shared._control_logits(embeddings["selection_full"], control)
    control_action = shared._control_logits(embeddings["selection_full"], control)
    if not bool(torch.equal(paper_action, control_action)):
        raise RuntimeError("D03 reconstructed action path drifted from matched control")

    paper_state = shared._clone_parameters(control)
    paper_state.update(shared._clone_parameters(assurance))
    checkpoint_payload = {
        "schema_version": "0.3",
        "system_id": "gax-paper-candidate",
        "architecture_id": "dal-shadow-assurance-critic-v0.3",
        "training_seed": seed,
        "selected_epoch": paper_selected["epoch"],
        "selection_metric": paper_selected["selection_metric"],
        "action_nll": paper_selected["action_nll"],
        "accuracy": paper_selected["accuracy"],
        "critic_nll": paper_selected["critic_nll"],
        "critic_accuracy": paper_selected["critic_accuracy"],
        "sufficiency_brier": paper_selected["sufficiency_brier"],
        "training_contract_sha256": contract_sha,
        "development_manifest_sha256": (
            "9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c"
        ),
        "base_model_id": "thomas-sounack/BioClinical-ModernBERT-base",
        "base_model_revision": "5e17e2f25260b6993e0fb60485f94678ff29779a",
        "tokenizer_revision": "5e17e2f25260b6993e0fb60485f94678ff29779a",
        "state": shared._state_payload(paper_state),
        "final_test_access": "sealed",
    }
    checkpoint_sha = _write_json(
        output_dir / "reconstructed-gax-paper-candidate.seed-0.checkpoint.json",
        checkpoint_payload,
    )
    if checkpoint_sha != PAPER_CHECKPOINT_SHA256:
        raise RuntimeError(
            "frozen paper checkpoint reconstruction mismatch: "
            f"expected {PAPER_CHECKPOINT_SHA256}, got {checkpoint_sha}"
        )
    return control, assurance, contract, shared, d03


def _calibration_items(source: Path, split_manifest_path: Path) -> list[Any]:
    records = dict(load_frozen_pqal(source))
    split = PubMedQASplitManifest.model_validate(
        json.loads(split_manifest_path.read_text(encoding="utf-8"))
    )
    items = [
        convert_record(pmid, records[pmid], split="calibration", include_gold=True)
        for pmid in split.calibration_ids
    ]
    if len(items) != 50:
        raise RuntimeError("PubMedQA action calibration role must contain exactly 50 rows")
    return items


def _calibration_logits(
    items: list[Any],
    contract: PaperTrainingContract,
    control: dict[str, Any],
    assurance: dict[str, Any],
    shared: Any,
    d03: Any,
) -> tuple[list[list[float]], list[int], list[float], list[int], list[dict[str, object]]]:
    import torch
    import transformers

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        contract.backbone.model_id,
        revision=contract.backbone.model_revision,
    )
    model = transformers.AutoModel.from_pretrained(
        contract.backbone.model_id,
        revision=contract.backbone.model_revision,
        torch_dtype=torch.float32,
        attn_implementation="eager",
    )
    model.requires_grad_(False)
    questions = [str(item.state["question"]) for item in items]
    evidences = [
        contract.encoder_input.evidence_joiner.join(evidence.text for evidence in item.evidence)
        for item in items
    ]
    full = shared._encode_pairs(
        tokenizer,
        model,
        questions,
        evidences,
        batch_size=contract.recipe.encoder_batch_size,
        torch=torch,
    )
    question_only = shared._encode_single(
        tokenizer,
        model,
        questions,
        batch_size=contract.recipe.encoder_batch_size,
        torch=torch,
    )
    action_logits_tensor = shared._control_logits(full, control)
    delta = full - question_only
    present, withheld = d03._suff(delta, assurance, torch)
    labels: list[int] = []
    for item in items:
        if item.gold is None or item.gold.action is None:
            raise RuntimeError("calibration item unexpectedly lacks action supervision")
        labels.append(_ACTION_ORDER.index(item.gold.action))
    action_logits = action_logits_tensor.detach().cpu().tolist()
    present_values = present.detach().cpu().tolist()
    withheld_values = withheld.detach().cpu().tolist()
    raw_sufficiency = [float(value) for value in present_values + withheld_values]
    sufficiency_labels = [1] * 50 + [0] * 50
    rows = []
    for item, logits, raw in zip(items, action_logits, present_values, strict=True):
        rows.append(
            {
                "item_id": item.id,
                "action_logits": [float(value) for value in logits],
                "gold_action_index": labels[len(rows)],
                "present_sufficiency_raw_logit": float(raw),
            }
        )
    for item, raw in zip(items, withheld_values, strict=True):
        rows.append(
            {
                "item_id": f"{item.id}::evidence-withheld",
                "action_logits": None,
                "gold_action_index": None,
                "present_sufficiency_raw_logit": float(raw),
            }
        )
    del model
    gc.collect()
    return action_logits, labels, raw_sufficiency, sufficiency_labels, rows


def _checksum_manifest(root: Path, path: Path) -> tuple[str, int, int]:
    manifest_sha = sha256_file(path)
    entries = 0
    verified = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"invalid SHA256SUMS line {line_number}")
        digest, relative = parts
        relative = relative.lstrip("*").strip()
        if relative.startswith("./"):
            relative = relative[2:]
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid SHA-256 digest on line {line_number}")
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents and candidate != root.resolve():
            raise ValueError("checksum manifest contains path traversal")
        entries += 1
        if not candidate.is_file():
            raise FileNotFoundError(f"PhysioNet release file missing: {relative}")
        if sha256_file(candidate) != digest:
            raise ValueError(f"PhysioNet SHA-256 mismatch: {relative}")
        verified += 1
    if entries == 0 or verified != entries:
        raise RuntimeError("PhysioNet checksum verification incomplete")
    return manifest_sha, entries, verified


def _load_fhir_resources(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]], int]:
    exact: dict[str, dict[str, Any]] = {}
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failures = 0
    files = sorted(root.rglob("*.ndjson.gz")) + sorted(root.rglob("*.ndjson"))
    if not files:
        raise RuntimeError("no PhysioNet FHIR NDJSON files found")
    for path in files:
        opener: Any = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                    if not isinstance(value, dict):
                        raise ValueError("FHIR NDJSON row is not an object")
                    validate_fhir_resource(value)
                    resource_type = value.get("resourceType")
                    resource_id = value.get("id")
                    if not isinstance(resource_type, str) or not isinstance(resource_id, str):
                        raise ValueError("FHIR resource requires resourceType and id")
                    key = f"{resource_type}/{resource_id}"
                    if key in exact and exact[key] != value:
                        raise ValueError(f"duplicate conflicting FHIR resource: {key}")
                    exact[key] = value
                    by_id[resource_id].append(value)
                except (json.JSONDecodeError, ValueError):
                    failures += 1
    return exact, by_id, failures


def _normalize_ref(value: str) -> str | None:
    text = value.strip().strip("'\"")
    if not text or text.lower() in {"nan", "none", "null", "[]"}:
        return None
    text = text.split("?")[0].rstrip("/")
    if "/" in text:
        parts = [part for part in text.split("/") if part]
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", text):
        return text
    return None


def _refs_from_object(value: object) -> list[str]:
    if isinstance(value, str):
        normalized = _normalize_ref(value)
        return [normalized] if normalized else []
    if isinstance(value, dict):
        rows: list[str] = []
        for child in value.values():
            rows.extend(_refs_from_object(child))
        return rows
    if isinstance(value, (list, tuple, set)):
        if (
            len(value) == 2
            and all(isinstance(child, str) for child in value)
            and re.fullmatch(r"[A-Za-z][A-Za-z0-9]+", str(list(value)[0]))
        ):
            combined = _normalize_ref(f"{list(value)[0]}/{list(value)[1]}")
            if combined:
                return [combined]
        rows = []
        for child in value:
            rows.extend(_refs_from_object(child))
        return rows
    return []


def _parse_fhir_refs(text: str) -> list[str]:
    if not text.strip() or text.strip().lower() in {"nan", "none", "null", "[]"}:
        return []
    direct = re.findall(r"[A-Za-z][A-Za-z0-9]+/[A-Za-z0-9][A-Za-z0-9._-]*", text)
    if direct:
        return list(dict.fromkeys(ref for raw in direct if (ref := _normalize_ref(raw))))
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue
        rows = _refs_from_object(parsed)
        if rows:
            return list(dict.fromkeys(rows))
    normalized = _normalize_ref(text)
    return [normalized] if normalized else []


def _fhir_calibration_refs(csv_path: Path) -> tuple[list[str], int]:
    probe, manifest, _audit, report = fq.qualify_frozen_source(csv_path)
    if report.status != "qualified" or manifest.calibration_row_count != 341:
        raise RuntimeError("FHIR-AgentBench frozen source/role qualification failed")
    if probe.source_sha256 != fq.FHIR_AGENTBENCH_SOURCE_SHA256:
        raise RuntimeError("FHIR-AgentBench source SHA-256 drift")
    _, _, source_rows, _ = fq._read_source(csv_path)
    roles = fq._assign_patient_roles(source_rows)
    included, _excluded = fq._included_rows_with_roles(source_rows, roles)
    calibration_ids = {row.question_id for row, role in included if role == "calibration"}
    if len(calibration_ids) != 341:
        raise RuntimeError("FHIR-AgentBench calibration membership drift")
    refs: list[str] = []
    seen_rows = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "true_fhir_ids" not in reader.fieldnames:
            raise RuntimeError("FHIR-AgentBench source lacks true_fhir_ids")
        for row in reader:
            if (row.get("question_id") or "").strip() not in calibration_ids:
                continue
            seen_rows += 1
            refs.extend(_parse_fhir_refs(row.get("true_fhir_ids") or ""))
    if seen_rows != 341:
        raise RuntimeError("did not recover all 341 FHIR-AgentBench calibration rows")
    return refs, seen_rows


def _resolve_reference(
    ref: str,
    exact: dict[str, dict[str, Any]],
    by_id: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    if ref in exact:
        return exact[ref]
    resource_id = ref.rsplit("/", 1)[-1]
    candidates = by_id.get(resource_id, [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def _reverse_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _reverse_keys(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [_reverse_keys(child) for child in value]
    return value


def _has_narrative(value: Any) -> bool:
    if isinstance(value, dict):
        if isinstance(value.get("resourceType"), str) and "text" in value:
            return True
        return any(_has_narrative(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_narrative(child) for child in value)
    return False


def _representation_evidence(
    representation: str,
    resources: list[dict[str, Any]],
    *,
    requested: int,
    resolved: int,
    missing: int,
    source_parse_failures: int,
) -> FhirRepresentationEvidence:
    rendered_lengths: list[int] = []
    repeated = True
    invariant = True
    parse_failures = source_parse_failures
    narrative_count = 0
    for resource in resources:
        try:
            first = render_fhir_resource(resource, representation=representation)  # type: ignore[arg-type]
            second = render_fhir_resource(resource, representation=representation)  # type: ignore[arg-type]
            perturbed = render_fhir_resource(
                _reverse_keys(resource), representation=representation  # type: ignore[arg-type]
            )
            repeated = repeated and first == second
            invariant = invariant and first == perturbed
            rendered_lengths.append(len(first.encode("utf-8")))
            if _has_narrative(resource) and representation in {
                "canonical-with-narrative",
                "source-order-json",
            }:
                narrative_count += 1
        except (TypeError, ValueError):
            parse_failures += 1
    median = float(statistics.median(rendered_lengths)) if rendered_lengths else 0.0
    required_invariance = representation != "source-order-json"
    eligible = (
        requested == resolved
        and missing == 0
        and parse_failures == 0
        and bool(resources)
        and repeated
        and (invariant or not required_invariance)
    )
    return FhirRepresentationEvidence(
        representation=representation,  # type: ignore[arg-type]
        requested_reference_count=requested,
        resolved_reference_count=resolved,
        unique_resource_count=len(resources),
        missing_resource_count=missing,
        parse_failure_count=parse_failures,
        deterministic_repeat=repeated,
        key_order_invariant=invariant,
        source_order_sensitivity_recorded=representation == "source-order-json",
        narrative_exposure_count=narrative_count,
        median_rendered_bytes=median,
        min_rendered_bytes=min(rendered_lengths, default=0),
        max_rendered_bytes=max(rendered_lengths, default=0),
        eligible=eligible,
    )


def _failure_category(error: BaseException) -> str:
    text = str(error).lower()
    if isinstance(error, TimeoutError) or "timeout" in text:
        return "timeout"
    if "out of memory" in text or "oom" in text:
        return "oom"
    if "http" in text or "download" in text or "transport" in text:
        return "transport"
    if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)) or "parse" in text:
        return "parse"
    if isinstance(error, FileNotFoundError) or "missing" in text or "resolve" in text:
        return "missing-resource"
    if isinstance(error, (TypeError, ValueError, RuntimeError)):
        return "interface"
    return "other"


def _run(args: argparse.Namespace) -> int:
    source_revision = str(args.source_revision)
    _require_source_revision(source_revision)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    control, assurance, contract, shared, d03 = _reconstruct_paper_checkpoint(
        source=Path(args.pubmedqa_source),
        development_manifest_path=Path(args.development_manifest),
        training_contract_path=Path(args.training_contract),
        output_dir=out,
    )
    items = _calibration_items(Path(args.pubmedqa_source), Path(args.pubmedqa_split_manifest))
    action_logits, action_labels, suff_logits, suff_labels, raw_rows = _calibration_logits(
        items, contract, control, assurance, shared, d03
    )
    temperature = fit_temperature(action_logits, action_labels)
    platt = fit_platt(suff_logits, suff_labels)
    calibration = CalibrationEvidence(action=temperature, sufficiency=platt)
    _model_json(out / "calibration-evidence.json", calibration)
    _write_json(out / "calibration-raw-logits.json", raw_rows)

    ecal = frozen_ecal_ledger()
    _model_json(out / "ecal-decision-ledger.json", ecal)

    physionet_root = Path(args.physionet_root)
    checksum_sha, checksum_entries, checksum_verified = _checksum_manifest(
        physionet_root, Path(args.physionet_sha256s)
    )
    exact, by_id, source_parse_failures = _load_fhir_resources(physionet_root / "fhir")
    refs, fhir_rows = _fhir_calibration_refs(Path(args.fhir_agentbench_csv))
    if fhir_rows != 341:
        raise RuntimeError("FHIR calibration row count drift")
    resolved_resources: dict[str, dict[str, Any]] = {}
    missing_digests: list[str] = []
    resolved_count = 0
    for ref in refs:
        resource = _resolve_reference(ref, exact, by_id)
        if resource is None:
            missing_digests.append(hashlib.sha256(ref.encode("utf-8")).hexdigest())
            continue
        resolved_count += 1
        key = f"{resource['resourceType']}/{resource['id']}"
        resolved_resources[key] = resource
    resources = [resolved_resources[key] for key in sorted(resolved_resources)]
    evidence_rows = [
        _representation_evidence(
            representation,
            resources,
            requested=len(refs),
            resolved=resolved_count,
            missing=len(missing_digests),
            source_parse_failures=source_parse_failures,
        )
        for representation in (
            "canonical-structured",
            "canonical-with-narrative",
            "flat-text",
            "source-order-json",
        )
    ]
    fhir = select_fhir_representation(
        evidence_rows,
        physionet_sha256s_sha256=checksum_sha,
        checksum_entry_count=checksum_entries,
        checksum_verified_file_count=checksum_verified,
    )
    fhir_payload = fhir.model_dump(mode="json")
    fhir_payload["missing_reference_sha256s"] = sorted(missing_digests)
    fhir_payload["fhir_representation_revision"] = FHIR_REPRESENTATION_REVISION
    _write_json(out / "fhir-selection-evidence.json", fhir_payload)

    calibration_sha = artifact_digest(calibration)
    ecal_sha = artifact_digest(ecal)
    fhir_sha = canonical_json_sha256(fhir.model_dump(mode="json"))
    selected_fhir_sha = canonical_json_sha256(
        {
            "representation": fhir.selected_representation,
            "fhir_representation_revision": FHIR_REPRESENTATION_REVISION,
            "selection_evidence_sha256": fhir_sha,
        }
    )
    authorization = AuthorizationCandidate(
        required_system_bundle_digests=dict(_REQUIRED_SYSTEM_DIGESTS),
        calibration_evidence_sha256=calibration_sha,
        selected_ecal_configuration_sha256=ecal_sha,
        selected_fhir_representation_sha256=selected_fhir_sha,
    )
    _model_json(out / "final-test-authorization-candidate.json", authorization)

    summary = {
        "schema_version": "0.1",
        "source_revision": source_revision,
        "contract_sha256": SG000020_CONTRACT_SHA256,
        "paper_checkpoint_sha256": PAPER_CHECKPOINT_SHA256,
        "paper_checkpoint_reconstruction_verified": True,
        "calibration_evidence_sha256": calibration_sha,
        "action_temperature": temperature.temperature,
        "action_nll_before": temperature.nll_before,
        "action_nll_after": temperature.nll_after,
        "sufficiency_platt_coefficient": platt.coefficient,
        "sufficiency_platt_intercept": platt.intercept,
        "sufficiency_bce_before": platt.bce_before,
        "sufficiency_bce_after": platt.bce_after,
        "ecal_ledger_sha256": ecal_sha,
        "ecal_keep": [row.component for row in ecal.decisions if row.decision == "keep"],
        "ecal_reject": [row.component for row in ecal.decisions if row.decision == "reject"],
        "fhir_selection_evidence_sha256": fhir_sha,
        "selected_fhir_representation": fhir.selected_representation,
        "fhir_requested_reference_count": len(refs),
        "fhir_resolved_reference_count": resolved_count,
        "fhir_missing_reference_count": len(missing_digests),
        "physionet_sha256s_sha256": checksum_sha,
        "authorization_candidate_sha256": artifact_digest(authorization),
        "authorization_can_authorize_inference": False,
        "calibration_rows_used": 150,
        "fhir_calibration_rows_used": 341,
        "final_test_rows_used": 0,
        "final_test_access": "sealed",
        "zero_founder_cost": True,
    }
    _write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    args = _args()
    out = Path(args.output_dir)
    try:
        return _run(args)
    except BaseException as error:
        out.mkdir(parents=True, exist_ok=True)
        _write_json(
            out / "failure.json",
            {
                "schema_version": "0.1",
                "status": "blocked",
                "failure_category": _failure_category(error),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "final_test_access": "sealed",
                "final_test_rows_used": 0,
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
