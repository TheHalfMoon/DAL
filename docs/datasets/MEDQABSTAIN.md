# MedQAbstain qualification boundary

GAX treats MedQAbstain as a derived abstention benchmark whose source families and media rights must be qualified independently.

## Frozen identity

- research repository: `disi-unibo-nlp/llm-medical-abstention`
- research revision: `3c296b55686f1bcf3e0eccbdd12bfc57c4bfdd1d`
- dataset repository: `disi-unibo-nlp/MedQAbstain`
- immutable dataset revision: `d215847217bb5f4124b9110379d33b9eb2f8d3f7`
- dataset files at that revision: 5
- parquet files: 2
- image archive: 1 (`images.zip`)
- dataset-card license field: **absent / null**

Moving `main` is not accepted as publication evidence. The dedicated qualification workflow re-fetches the public Hub metadata and frozen parquet files and verifies committed metadata-only evidence.

## Upstream transformation

The frozen upstream code removes the original gold option from model-visible choices and adds an explicit `I abstain` choice. GAX independently audits this property rather than trusting the transformation description.

The frozen dataset contains 11,232 rows across six source components. The transformation audit records 11,215 construction-eligible rows and quarantines 17 rows before any paper evaluation:

| Component | Source rows | Eligible | Quarantined | Observed anomaly |
| --- | ---: | ---: | ---: | --- |
| AfriMedQA | 2,350 | 2,336 | 14 | original gold remains visible |
| MedMCQA | 1,886 | 1,885 | 1 | original gold remains visible |
| MedQA 4-option | 1,273 | 1,272 | 1 | transformed gold is not abstention |
| MedQA 5-option | 1,273 | 1,273 | 0 | none under the frozen rule |
| MedXpertQA text | 2,450 | 2,450 | 0 | none under the frozen rule |
| MedXpertQA multimodal | 2,000 | 1,999 | 1 | transformed gold is not abstention |

The quarantine membership is represented only by digests. GAX does not commit raw item IDs, questions, answers, or images as qualification evidence.

The lineage key is `dataset + id`, not raw `id`. This is required because the 4-option and 5-option MedQA variants reuse source identifiers.

## Component-level rights outcome

The immutable MedQAbstain dataset card exposes no license grant. GAX therefore does **not** infer redistribution or paper-evaluation permission from public download access.

| Component | Source evidence | Derived MedQAbstain publication state |
| --- | --- | --- |
| MedXpertQA text | current source card advertises MIT | blocked |
| MedXpertQA multimodal | current source card advertises MIT; per-image rights not independently proven | blocked |
| MedMCQA | current source card advertises Apache-2.0 | blocked |
| MedQA 4-option | source-content license unresolved | blocked |
| MedQA 5-option | source-content license unresolved | blocked |
| AfriMedQA | current source card advertises CC BY 4.0 | blocked |

The block is deliberate: source-component licenses do not automatically relicense MedQAbstain's transformed collection, threat labels, prompts, or repackaged media. The exact upstream generation revisions used to create the frozen MedQAbstain files are also not pinned by the frozen preprocessing code.

This is a **qualification result**, not an unfinished rights review. SG-000017 may close with a blocked aggregate outcome once the preregistered leakage audit and exact-head/post-main CI evidence are bound.

## Role policy

MedQAbstain remains **final-test-only candidate data with paper evaluation unauthorized**.

It cannot be used to choose GAX checkpoints, prompts, calibration methods, thresholds, ECAL components, learned information-sufficiency variants, FHIR representations, or repair rules. P08 final-test access remains sealed.

Because aggregate paper use is blocked, GAX will not make MedQAbstain a hidden dependency of the paper. A later pre-results governance grain may define a GAX-native abstention benchmark from independently frozen sources with explicit compatible licenses and provenance.

## Evidence policy

Committed GAX evidence may contain immutable repository/file identities, SHA-256/LFS digests, schemas and aggregate counts, per-component rights states, duplicate/near-duplicate counts and digests, and role/transformation membership digests.

It must not contain copied source questions, original answers, images, or other upstream payloads merely to make the benchmark convenient to redistribute.

## Non-claims

SG-000017 is not a performance study. It establishes no GAX accuracy, abstention superiority, clinical safety, calibration superiority, or SOTA claim. Quarantining construction anomalies does not establish absence of public-benchmark pretraining contamination, which remains unresolved and must be disclosed.
