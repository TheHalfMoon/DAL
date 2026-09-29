# MedQAbstain qualification boundary

GAX treats MedQAbstain as a derived abstention benchmark whose source families and media rights must be qualified independently.

## Frozen research source

- research repository: `disi-unibo-nlp/llm-medical-abstention`
- research revision: `3c296b55686f1bcf3e0eccbdd12bfc57c4bfdd1d`
- dataset repository: `disi-unibo-nlp/MedQAbstain`
- dataset revision: **not frozen until the dedicated Hugging Face metadata probe records an immutable 40-character revision**

No moving `main` reference is accepted as publication evidence.

## Upstream transformation

The frozen upstream README describes MedQAbstain as a transformation of medical MCQA sources that removes the original gold answer from the visible option set and adds an explicit abstention/escalation option. GAX will not infer clinical safety from this construction. The paper may only describe performance on this deliberately constructed insufficiency/unsafe-commit condition.

The qualification must prove that the original correct option is absent from model-visible choices before assigning abstention as the transformed gold target. Original answer identity and threat/source labels remain supervision/evaluation metadata unless a later preregistered protocol explicitly admits a field.

## Component-level rights

The benchmark exposes at least these source families:

| Component | Preliminary evidence state | GAX publication state |
| --- | --- | --- |
| MedXpertQA text | upstream card currently advertises MIT; immutable source revision still to freeze | pending |
| MedXpertQA multimodal | text/card evidence is not sufficient by itself for every image/media asset | pending |
| MedMCQA | official HF repository advertises Apache-2.0 metadata; content lineage/revision still to freeze | pending |
| MedQA 4-option | available dataset metadata has historically exposed unclear/unknown content licensing | pending rights review |
| MedQA 5-option | same source-content rights question as MedQA 4-option | pending rights review |
| AfriMedQA | current public metadata shows Creative Commons licensing, but exact source/version used by MedQAbstain must be frozen before selecting the applicable terms | pending |

These are **preliminary research notes**, not qualification conclusions. The machine-readable component-rights artifact created by SG-000017 is authoritative after exact source revisions are frozen.

A repository/software license never automatically relicenses exam questions, transformed medical content, or third-party images.

## Role policy

Default GAX role: **final-test-only**.

MedQAbstain items cannot be used to choose GAX checkpoints, prompts, calibration methods, thresholds, ECAL components, learned information-sufficiency variants, FHIR representations, or repair rules. Any future non-test role requires a separately licensed and prospectively frozen development surface before model comparison.

## Evidence policy

Committed GAX evidence may contain:

- immutable repository/file identities;
- SHA-256/LFS digests;
- schemas and aggregate counts;
- per-component license/redistribution states;
- duplicate/near-duplicate counts and digests;
- role-manifest and transformation-audit digests.

It must not contain copied source questions, original answers, images, or other upstream payloads merely to make the benchmark convenient to redistribute.

## Current non-claims

SG-000017 is not a performance study. Until a later digest-authorized P08 opening manifest exists, it establishes no GAX accuracy, abstention superiority, clinical safety, calibration superiority, or SOTA claim. Final-test access remains sealed.
