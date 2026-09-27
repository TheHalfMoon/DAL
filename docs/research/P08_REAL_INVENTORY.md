# P08 Real Evaluation Inventory

Status: **PRE-AUTHORIZATION / final-test access sealed**

SG-000013 turns the P08 freeze contract into an honest inventory of the real datasets,
systems, and protocol decisions that must exist before final-test authorization can be
considered.

This grain does not authorize final-test access.

## Core rule

```text
listed != qualified
adapter-qualified != real-model-qualified
repository license != automatic third-party-data permission
pending != failed
blocked != silently omitted
final-test inventory != final-test access
```

The machine-readable inventory is `registry/p08_real_inventory.json`.

## Dataset candidates

### PubMedQA PQA-L

Frozen source:

```text
repository: pubmedqa/pubmedqa
revision: 1cbae8e92f72f20c8d3747cbb3bf5bc53554d997
repository license: MIT
```

PQA-L is an especially clean GAX task because its expert-labelled answer space is already
`yes`, `no`, or `maybe`. GAX does not need to invent a clinical action taxonomy to evaluate
closed-choice biomedical evidence reasoning.

Status remains `pending` until GAX constructs an immutable split manifest and completes the
cross-source/train-development-calibration-test leakage audit. Public labels are not a license
to tune the final test.

### FHIR-AgentBench

Frozen source:

```text
repository: glee4810/FHIR-AgentBench
revision: bbb42909a5a7eb907d1cd91f72a560729e7037ea
repository license: CC BY 4.0
source FHIR version: R4
```

The repository license does not erase separate access or redistribution obligations for
MIMIC-derived, EHRSQL-derived, or other upstream source material. GAX therefore records the
candidate as restricted/pending until the exact normalized export surface and source-data
rights are audited.

### MedAgentBench

Frozen source:

```text
repository: stanfordmlgroup/MedAgentBench
revision: 99260117137b09f04837a8c18d18a1107efa55ae
repository license: MIT
```

The repository is MIT licensed, while the upstream setup also refers to separately supplied
FHIR-server images and reference-solution artifacts. Those artifacts retain separate terms.
GAX uses the P07 local normalized-export contract rather than requiring founder-paid cloud
infrastructure.

### MedQAbstain

Frozen code source:

```text
repository: disi-unibo-nlp/llm-medical-abstention
revision: 3c296b55686f1bcf3e0eccbdd12bfc57c4bfdd1d
```

MedQAbstain is highly relevant because it converts medical MCQA into abstention-only cases by
removing the original correct option and adding an abstention action. Its published dataset
combines material derived from multiple upstream benchmarks and includes separately sourced
multimodal assets. GAX therefore records the license state as `ambiguous` until every component
used by the intended text-only evaluation slice has an immutable revision and compatible use
terms.

### MedMCQA

Frozen repository source:

```text
repository: medmcqa/medmcqa
revision: c59ef14ca1990266c4107c7864b45a20fd93e5e0
repository license file: MIT
```

The README downloads the dataset from a separate archive. The repository's MIT license text
uses the conventional "software and associated documentation" language. GAX will not silently
infer that this establishes redistribution rights for all exam-question content. MedMCQA is
optional/pending until that scope is resolved.

### MedQA

MedQA remains optional and `blocked` for paper-evaluation admission until the rights and
redistribution status of the underlying exam-derived question content are sufficiently clear.
A popular benchmark is not automatically a legally reproducible benchmark package.

### Med-PRM

Med-PRM is retained as evidence/verifier related work and a potential external validation
source. It is not admitted as a required evaluation dataset until its exact artifacts,
licenses, and task conversion are frozen.

## System inventory

P08 distinguishes source identity from real execution.

The existing P02 registry already freezes source/model identities for:

- CLM;
- Laya;
- decider;
- the open restricted-logit control;
- BioClinical ModernBERT Base;
- Qwen3.5-4B structured-output control;
- conditional Jev access.

SG-000013 imports those identities into a stricter paper inventory but leaves them `pending`
until a real zero-founder-cost run produces an evidence packet under the matched P08 protocol.

The GAX paper candidate is also `pending`: P03 proved a trainable reference implementation,
not the final paper checkpoint. Final checkpoint identity, training seeds, training data
manifest, development-selection history, and real execution evidence must be frozen before
final-test authorization.

Jev remains optional and explicitly `blocked` unless reproducible evaluation access, immutable
identity, and applicable terms permit matched measurement. Its absence must be reported rather
than hidden.

## Protocol inventory

The following candidates are recorded before final-test opening but are not yet declared
winners:

- target coverages: `0.50`, `0.80`, `0.90`;
- ECAL components: evidence, hard-negative, proper-scoring, replay-retention, and
  state-action-contrastive;
- FHIR representations: canonical-structured, canonical-with-narrative, flat-text, and
  source-order-json.

Development evidence must freeze:

- the calibration method and calibration split hash;
- which ECAL components are retained or rejected;
- the FHIR representation selection rule;
- the hardware/timing protocol and comparability classes;
- primary comparison families and multiplicity policy.

Test labels cannot participate in any of those choices.

## Machine gate

Run:

```bash
gax-p08-inventory --inventory registry/p08_real_inventory.json
```

The command emits a canonical inventory digest and a sorted blocker list.

`ready_for_authorization` is expected to be `false` in SG-000013. That is not a failed grain;
it is the truthful state before real dataset acquisition, leakage audits, model qualification,
and protocol freeze.

A later grain may change entries to `qualified` only when the required immutable evidence is
available. Final-test authorization remains governed separately by `p08_freeze.py` and cannot
be created merely by editing this inventory.

## Publication consequence

The paper may eventually use a smaller final suite than this candidate inventory, but removals
must be decided from licensing, feasibility, or preregistered development criteria before
final-test access. A benchmark cannot be dropped after seeing an unfavorable final result.
