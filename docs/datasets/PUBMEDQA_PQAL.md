# PubMedQA PQA-L qualification

Status: **SG-000014 active; final test sealed**

This document freezes the GAX P08 treatment of PubMedQA PQA-L before any real-model comparison.

## Frozen source

- Repository: `pubmedqa/pubmedqa`
- Commit: `1cbae8e92f72f20c8d3747cbb3bf5bc53554d997`
- File: `data/ori_pqal.json`
- Git blob SHA-1: `38db7750761c78950ed32303e7545bdaa513390c`
- Repository license: MIT
- Expected records: 1,000 expert-labeled PQA-L examples
- Natural answer set: `yes`, `no`, `maybe`

The GAX build verifies the Git object identity over the exact downloaded bytes. A mutable branch name or a matching filename is not sufficient evidence.

## Model-visible representation

A GAX PubMedQA item exposes only:

- `QUESTION` as the decision state;
- `CONTEXTS` as evidence text;
- an available `LABELS` section name as evidence structure;
- the explicit actions `maybe`, `no`, `yes`, in that order.

The following source fields are deliberately **not model-visible**:

- `LONG_ANSWER`;
- `final_decision`;
- `reasoning_required_pred`;
- `reasoning_free_pred`;
- PMID/source identity;
- `YEAR`;
- `MESHES`.

`LONG_ANSWER` is the article conclusion and is answer-adjacent. It is therefore excluded rather than treated as ordinary evidence.

PubMedQA `maybe` is an answer to the benchmark question. It is **not** GAX abstention and is **not** an information-sufficiency target.

## Preregistered role split

The split is fixed before any GAX or baseline result is observed.

GAX reproduces the upstream split algorithm exactly:

1. Python-compatible RNG seed `0`.
2. Group by `yes`, `no`, `maybe`.
3. Shuffle each label group with the same continuing RNG state.
4. Build the upstream two-way split: 500 CV / 500 test.
5. Split the 500 CV items into the upstream ten folds with the continuing RNG state.

GAX roles are then frozen as:

| GAX role | PQA-L membership | Count | Use |
|---|---|---:|---|
| training | none | 0 | PQA-L is not a GAX training source in SG-000014 |
| validation | upstream CV folds 1-9 | 450 | development-only model/mechanism analysis |
| calibration | upstream CV fold 0 | 50 | calibration/threshold selection only |
| test | upstream outer test half | 500 | sealed final evaluation only |

The manifest serializes PMIDs/role membership but no labels.

## Leakage audit

Qualification has two distinct leakage questions.

### 1. Within-GAX transformation leakage

This is actionable and can block qualification. GAX runs its existing exact audit across all roles for:

- duplicate item IDs;
- source IDs crossing roles;
- exact model-input fingerprints crossing roles;
- counterfactual groups crossing roles.

SG-000014 adds a preregistered near-duplicate check over model-visible question + abstract text:

- lowercase Unicode word-token normalization;
- 5-token shingles;
- Jaccard similarity;
- cross-role comparisons only;
- blocking threshold `>= 0.80`.

The report contains identifiers, roles, and similarity scores only; it does not reproduce source text or final-test labels.

### 2. Public-benchmark pretraining contamination

PubMedQA is public and has been used widely. GAX cannot establish that every evaluated backbone was never pretrained on PQA-L or its source articles. The qualification report therefore records this risk as:

`unresolved-public-benchmark`

A clean GAX split audit must **not** be described as proof of zero pretraining contamination.

## Final-test boundary

During qualification:

- test `BenchmarkItem.gold` is always `null`;
- the split manifest contains no answers;
- the leakage report contains no answers;
- the qualification report contains no answers or model metrics;
- no test item may be used for training, calibration, prompt selection, threshold selection, ECAL selection, FHIR representation selection, or model selection.

The original public source necessarily contains labels. The governance claim is therefore process isolation inside GAX, not cryptographic secrecy of a public dataset.

## Dedicated qualification job

`.github/workflows/p08-pubmedqa-qualification.yml` downloads the exact raw file at the frozen commit, verifies the Git blob, builds the role manifest, runs exact and near-duplicate audits, and uploads only metadata qualification artifacts.

The job performs no model inference and requires no paid API or cloud service.

The inventory entry `pubmedqa-pqal` may move from `pending` to `qualified` only after a real run over the frozen upstream source yields:

- matching source blob identity;
- a real split-manifest SHA-256;
- a real leakage-audit SHA-256;
- `status=qualified`;
- final-test access still `sealed`.

## Non-claims

Dataset qualification does not establish:

- clinical safety;
- clinical competence;
- absence of backbone pretraining contamination;
- superiority over any baseline;
- calibration quality;
- evidence-grounding quality;
- abstention quality;
- SOTA performance.
