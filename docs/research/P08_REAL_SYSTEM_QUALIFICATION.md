# P08 Real-System Qualification — SG-000019

Status: **ACTIVE / pre-results**
Research contract: `SG-000019` / Issue #63
Final-test access: **SEALED**

## Purpose

SG-000019 establishes real, reproducible development-time system evidence before any P08 final-test authorization. It does not authorize final-test inference and it does not permit final-test-derived model, checkpoint, threshold, prompt, ECAL, or FHIR representation selection.

The required primary systems are:

1. `gax-paper-candidate` — the stronger DAL paper candidate; `gax-bilinear-v0` remains an engineering/control model and is not promoted by convenience.
2. `clinical-encoder` — the matched BioClinical ModernBERT control.
3. `laya` — the frozen open typed-decision baseline.

## Frozen development surface

The canonical PubMedQA PQA-L development role is deterministically subdivided into:

- 360 training rows;
- 90 development-selection rows.

The 50 calibration rows and 500 final-test rows are excluded from this child split. The final-test role remains sealed.

Canonical artifacts:

- development manifest: `registry/p08_development_training_manifest_sg000019.json`
- manifest SHA-256: `9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c`
- development leakage audit: `registry/p08_development_leakage_audit_sg000019.json`
- leakage-audit SHA-256: `1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76`
- training seeds for trainable required systems: `0`, `1`, `2`

The child leakage audit is clean under the governed exact and near-duplicate policy. Public benchmark pretraining contamination risk remains a disclosure limitation rather than being silently treated as resolved.

## Frozen required-model identities

Model identities are recorded in `registry/p08_required_model_revisions_sg000019.json` and verified against immutable Hugging Face commits.

### Laya

- source revision: `3c68ca2ccf6a83640ab80c20379503fe72c772fd`
- model: `convaiinnovations/laya`
- model revision: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`
- license: Apache-2.0

### Clinical encoder

- model: `thomas-sounack/BioClinical-ModernBERT-base`
- model revision: `5e17e2f25260b6993e0fb60485f94678ff29779a`
- tokenizer revision: `5e17e2f25260b6993e0fb60485f94678ff29779a`
- license: MIT

## Real Laya qualification

A genuine CPU-only Laya run was executed on the 90 development-selection rows. No final-test row was opened or inferred.

Evidence-producing run:

- workflow run: `36644042755`
- evidence head: `7f75fb23677492258a855f99c6c406caaf61f849`
- requested: 90
- completed: 90
- preserved failures: 0
- development correct: 48 / 90
- development accuracy: **0.5333333333333333 (53.33%)**
- zero founder cost: true
- final-test access: sealed

The development result is retained exactly as observed. Qualification is based on immutable identity, reproducibility, complete request accounting, and failure preservation; it is not conditional on the baseline achieving a favorable score.

Evidence bindings:

- predictions SHA-256: `577b487ea4f4f7ad728d46fe216d56d693838a55cb23b4388e2edd0bdf797d9b`
- execution-evidence SHA-256: `4d4a3fcb141ead95352afd465139e0cc450b2073f9b14b1cc06988bfc551e42a`
- qualification-bundle SHA-256: `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`
- GitHub artifact ID: `11067464805`
- GitHub artifact digest: `sha256:0123a17c4f845f2701a749526ddc7ac112b01c6d389dde3867ce7fbdb9b9f9c5`

Persisted records:

- `registry/p08_laya_execution_evidence_sg000019.json`
- `registry/p08_laya_qualification_bundle_sg000019.json`
- `registry/p08_laya_qualification_summary_sg000019.json`

The canonical real inventory may mark `laya` qualified only when its `real_execution_evidence_id` binds the exact qualification-bundle digest and its source, model, and adapter revisions match the qualified execution.

## Remaining authorization-critical work

`SG-000019` is **not PROVEN** and this implementation tranche is **not a closeout**.

Still required:

- implement and train the stronger DAL paper-candidate architecture without promoting `gax-bilinear-v0` by convenience;
- train the paper candidate for the preregistered seeds `0`, `1`, and `2` using only the 360 training rows;
- train the matched BioClinical ModernBERT control for the same seeds and training-role policy;
- execute both trainable required systems on the 90 development-selection rows with immutable checkpoint provenance and complete failure accounting;
- keep the 50 calibration rows reserved for the frozen calibration policy;
- keep final-test data sealed until every authorization-critical dependency is genuinely qualified and a separate digest-bound authorization artifact permits final-test access.

Negative, null, or weaker-than-expected development results must remain in the evidence chain. Final-test results must never be used to revise the model, checkpoint, prompt, threshold, ECAL configuration, or FHIR representation.
