from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CLINICAL_MODEL_ID = "thomas-sounack/BioClinical-ModernBERT-base"
CLINICAL_MODEL_REVISION = "5e17e2f25260b6993e0fb60485f94678ff29779a"
LAYA_MODEL_ID = "convaiinnovations/laya"
LAYA_SOURCE_REVISION = "3c68ca2ccf6a83640ab80c20379503fe72c772fd"
HF_API_ROOT = "https://huggingface.co/api/models"


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DAL-SG-000019-model-identity/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"unable to resolve Hugging Face model identity: {url}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected Hugging Face response type for {url}")
    return payload


def _model_url(model_id: str, revision: str | None = None) -> str:
    quoted_model = urllib.parse.quote(model_id, safe="/")
    url = f"{HF_API_ROOT}/{quoted_model}"
    if revision is not None:
        url = f"{url}/revision/{urllib.parse.quote(revision, safe='')}"
    return url


def _resolve(model_id: str, revision: str | None = None) -> dict[str, Any]:
    payload = _fetch_json(_model_url(model_id, revision))
    resolved_sha = payload.get("sha")
    if not isinstance(resolved_sha, str) or len(resolved_sha) != 40:
        raise RuntimeError(f"Hugging Face response for {model_id} lacks a 40-char commit SHA")
    if revision is not None and resolved_sha != revision:
        raise RuntimeError(
            f"Hugging Face resolved {model_id}@{revision} to unexpected SHA {resolved_sha}"
        )
    card_data = payload.get("cardData")
    license_name = card_data.get("license") if isinstance(card_data, dict) else None
    return {
        "model_id": model_id,
        "model_revision": resolved_sha,
        "license": license_name,
    }


def _bootstrap_registry() -> dict[str, Any]:
    laya = _resolve(LAYA_MODEL_ID)
    clinical = _resolve(CLINICAL_MODEL_ID, CLINICAL_MODEL_REVISION)
    return {
        "schema_version": "0.1",
        "identity_policy": "immutable-huggingface-commit-v0.1",
        "final_test_access": "sealed",
        "systems": [
            {
                "system_id": "laya",
                "role": "baseline",
                "source_revision": LAYA_SOURCE_REVISION,
                "model_id": LAYA_MODEL_ID,
                "model_revision": laya["model_revision"],
                "license": "Apache-2.0",
                "identity_status": "frozen-not-executed",
            },
            {
                "system_id": "clinical-encoder",
                "role": "control",
                "source_revision": CLINICAL_MODEL_REVISION,
                "model_id": CLINICAL_MODEL_ID,
                "model_revision": clinical["model_revision"],
                "tokenizer_revision": clinical["model_revision"],
                "license": "MIT",
                "identity_status": "frozen-not-executed",
            },
        ],
    }


def _verify_registry(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "0.1":
        raise RuntimeError("model revision registry schema_version must be 0.1")
    if payload.get("identity_policy") != "immutable-huggingface-commit-v0.1":
        raise RuntimeError("unexpected model identity policy")
    if payload.get("final_test_access") != "sealed":
        raise RuntimeError("model revision registry must keep final-test access sealed")

    raw_systems = payload.get("systems")
    if not isinstance(raw_systems, list):
        raise RuntimeError("model revision registry systems must be a list")
    by_id = {
        item.get("system_id"): item
        for item in raw_systems
        if isinstance(item, dict) and isinstance(item.get("system_id"), str)
    }
    if set(by_id) != {"laya", "clinical-encoder"}:
        raise RuntimeError("registry must contain exactly laya and clinical-encoder identities")

    expected = {
        "laya": {
            "model_id": LAYA_MODEL_ID,
            "source_revision": LAYA_SOURCE_REVISION,
            "license": "Apache-2.0",
            "role": "baseline",
        },
        "clinical-encoder": {
            "model_id": CLINICAL_MODEL_ID,
            "source_revision": CLINICAL_MODEL_REVISION,
            "license": "MIT",
            "role": "control",
        },
    }
    verified: list[dict[str, str]] = []
    for system_id in ("laya", "clinical-encoder"):
        item = by_id[system_id]
        for key, value in expected[system_id].items():
            if item.get(key) != value:
                raise RuntimeError(f"{system_id} {key} drift: expected {value!r}")
        revision = item.get("model_revision")
        if not isinstance(revision, str) or len(revision) != 40:
            raise RuntimeError(f"{system_id} model_revision must be a 40-char immutable SHA")
        resolution = _resolve(expected[system_id]["model_id"], revision)
        verified.append(
            {
                "system_id": system_id,
                "model_id": expected[system_id]["model_id"],
                "model_revision": resolution["model_revision"],
                "status": "verified",
            }
        )

    if by_id["clinical-encoder"].get("model_revision") != CLINICAL_MODEL_REVISION:
        raise RuntimeError("clinical-encoder immutable revision drifted from the prior freeze")
    if by_id["clinical-encoder"].get("tokenizer_revision") != CLINICAL_MODEL_REVISION:
        raise RuntimeError(
            "clinical-encoder tokenizer revision must match the frozen model revision"
        )
    return {
        "schema_version": "0.1",
        "final_test_access": "sealed",
        "verified_systems": verified,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.registry is None:
        result = _bootstrap_registry()
    else:
        result = _verify_registry(json.loads(args.registry.read_text(encoding="utf-8")))
    _write_json(args.output, result)


if __name__ == "__main__":
    main()
