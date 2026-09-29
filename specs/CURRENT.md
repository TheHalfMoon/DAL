# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers are retained where they name already-frozen
artifacts, workflows, schemas, model roles, or evidence chains. DAL is the current program
identity. Any future identity migration must not rewrite historical evidence or silently change
artifact identity.

## Canonical completed grains

- **SG-000001 — GAX-P00 Research foundation and publication contract** — PROVEN
- **SG-000002 — GAX-P01 Benchmark kernel and selective-risk metric contract** — PROVEN
- **SG-000003 — GAX-P02 Core matched baseline harness and evidence-packet contract** — PROVEN
- **SG-000004 — GAX-P02 External transport adapters and upstream revision freeze** — PROVEN
- **SG-000005 — GAX-P02 Phase closeout and final baseline identity freeze** — PROVEN
- **SG-000006 — GAX-P03 First trainable non-generative GAX v0** — PROVEN
- **SG-000007 — GAX-P04 ECAL controlled ablation framework** — PROVEN
- **SG-000008 — GAX-P05 Native information sufficiency and selective abstention** — PROVEN
- **SG-000009 — GAX-P06 Evidence interventions and counterfactual robustness** — PROVEN
- **SG-000010 — GAX-P07 FHIR interoperable read-only decision layer** — PROVEN
- **SG-000011 — GAX-P08 Final-test freeze and claim-evidence contract** — PROVEN
- **SG-000012 — GAX-P08 Statistical uncertainty and evidence aggregation infrastructure** — PROVEN
- **SG-000013 — GAX-P08 Real evaluation inventory and pre-authorization freeze** — PROVEN
- **SG-000014 — GAX-P08 PubMedQA PQA-L qualification and split/leakage manifest** — PROVEN
- **SG-000015 — GAX-P08 FHIR-AgentBench frozen local R4 dataset qualification** — PROVEN
- **SG-000016 — GAX-P08 MedAgentBench public corpus and external runtime qualification** — PROVEN
- **SG-000017 — GAX-P08 MedQAbstain immutable dataset and component-rights qualification** — PROVEN
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement** — PROVEN

The detailed evidence for each grain is preserved in its SpecGrain JSON, implementation/closeout
PRs, Git history, workflow runs, and research evidence files. This file is a current-frontier index,
not a mutable duplicate of every historical packet.

## Latest canonical closeout — SG-000018

SG-000018 prospectively resolved the paper-critical benchmark/protocol blockers without opening
final-test access or using final-test model performance for selection.

### Research outcome

- The required native abstention benchmark reuses the already-qualified PubMedQA PQA-L source.
- Deterministic `evidence-present` / `evidence-withheld` pairs preserve state/action identity and
  keep abstention outside `BenchmarkItem.actions`.
- Development/calibration sufficiency supervision is separated from action supervision.
- Sealed final-test variants serialize neither action nor sufficiency gold.
- `medqabstain` remains visible and blocked for paper-required use because the frozen derived
  dataset exposes no license grant.
- The MedAgentBench public corpus remains qualified while its official external runtime/scorer
  remains blocked and secondary/optional for authorization.
- The authorization-critical dataset suite is PubMedQA PQA-L, the DAL-native PubMedQA abstention
  benchmark, and FHIR-AgentBench.
- Final-test access remains **sealed**.

### Frozen pre-results protocol

- calibration: `temperature-scaling-action+platt-sufficiency-v0.1`;
- calibration manifest: `registry/p08_calibration_manifest_sg000018.json`;
- calibration manifest canonical JSON SHA-256:
  `89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`;
- target coverages: 0.50 / 0.80 / 0.90;
- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- final-test tuning: forbidden.

### Canonical evidence

- implementation PR: #60
- exact implementation head: `bcc216885113a19d9eef8618c821b3712fa0d444`
- implementation merge: `dfd9899f7b8b7ba4f515b1d773b806545b0361c3`
- implementation exact-head GAXBench CI: `36635301300` — SUCCESS
- implementation exact-head secure Jev: `36635297195` / job `109638612830` — PASSED, 39/39 hunks, zero blocking findings
- implementation exact-head Alibaba OpenCodeReview: `36635301242` — SUCCESS
- post-main GAXBench CI: `36636682683` — SUCCESS
- canonical closeout PR: #62
- closeout exact head: `f72f4b1c8dc6c566ce63768097b1d6093a553bb6`
- closeout GAXBench CI: `36637213255` — SUCCESS
- closeout secure Jev: `36637212993` / job `109640678356` — PASSED, 11/11 hunks, zero blocking findings
- closeout Alibaba OpenCodeReview: `36637213442` — SUCCESS
- canonical closeout merge: `54ffad6005e3848058be59870f1fee408073ef55`
- post-closeout GAXBench CI: `36637386023` — SUCCESS on Linux/Windows × Python 3.11/3.12

Issue #57 is closed as completed. SG-000018 is CLOSED_CANONICAL.

## Active frontier — SG-000019

**SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation** is ACTIVE under Issue #63.

Canonical dependency:

`54ffad6005e3848058be59870f1fee408073ef55`

### Why SG-000019 exists

The authorization-critical system set is:

- `gax-paper-candidate` — legacy inventory ID for the DAL paper candidate — **pending**;
- `clinical-encoder` — **pending**;
- `laya` — **qualified in the current SG-000019 implementation tranche from genuine development-only execution evidence**.

The tiny deterministic `gax-bilinear-v0` remains an engineering/control model and must not become
the headline paper model merely because it is already runnable.

A second gap is now explicitly governed: the qualified PubMedQA PQA-L role surface contains 450
development, 50 calibration, and 500 sealed final-test rows, while the trainable reference path
requires explicit training items. SG-000019 therefore derives training only inside the 450-row
development surface:

- 360 deterministic train rows;
- 90 deterministic selection/validation rows;
- stratified by the frozen yes/no/maybe label;
- calibration rows remain reserved for calibration;
- final-test rows remain sealed and unavailable to model/protocol selection.

PQA-A and PQA-U are not silently admitted because upstream distributes them as separate artifacts;
any use would require separate immutable identity and rights qualification.

### Current SG-000019 implementation evidence

The current implementation tranche has established the GPU-independent qualification foundation:

- development manifest: `registry/p08_development_training_manifest_sg000019.json`;
- development manifest SHA-256:
  `9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c`;
- child development leakage audit: `registry/p08_development_leakage_audit_sg000019.json`;
- leakage-audit SHA-256:
  `1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76`;
- exact Laya source revision: `3c68ca2ccf6a83640ab80c20379503fe72c772fd`;
- exact Laya model revision: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`;
- exact BioClinical ModernBERT model/tokenizer revision:
  `5e17e2f25260b6993e0fb60485f94678ff29779a`;
- real Laya evidence-producing run: `36644042755` on head
  `7f75fb23677492258a855f99c6c406caaf61f849`;
- Laya execution: 90 requested / 90 completed / 0 preserved failures;
- Laya development-only result: 48 / 90 correct = **53.33% accuracy**;
- Laya qualification-bundle SHA-256:
  `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`;
- final-test access remained **sealed** throughout the run.

The 53.33% result is retained because qualification means immutable, reproducible, completely
accounted real execution; it does not mean the baseline achieved a favorable result. Null or weak
development evidence must not be discarded.

`registry/p08_real_inventory.json` binds the Laya promotion to the exact qualification bundle,
source revision, model revision, and execution adapter. `gax-paper-candidate` and
`clinical-encoder` remain pending and therefore still block final-test authorization.

### SG-000019 required outputs

- nested development split manifest and leakage audit;
- stronger DAL paper-candidate architecture/training/checkpoint provenance path;
- matched clinical-encoder control path;
- exact Laya checkpoint/model identity and zero-founder-cost qualification path;
- preregistered training seeds `[0, 1, 2]`;
- machine-readable training recipe, selection history, checkpoint, hardware/runtime, failure, and
  real-execution evidence manifests;
- fail-closed inventory promotion rules;
- zero-founder-cost accelerator notebook/workflow for runs ordinary CI cannot complete;
- exact-head CI, Alibaba OpenCodeReview, and secure TypeSafe Jev evidence before merge.

The intended DAL paper candidate is non-autoregressive and typed: a frozen clinical/biomedical
encoder backbone, typed candidate-action scoring, an evidence-sensitive path, and an explicit
information-sufficiency mechanism separated from the action distribution. Qwen3.5-4B remains a
structured-output generative comparison rather than the DAL headline model.

### Safety boundary

P08 final-test access remains **sealed** throughout SG-000019. No final-test inference, checkpoint
selection, threshold selection, prompt selection, ECAL selection, FHIR representation selection,
or public superiority claim is authorized. A separate later digest-bound authorization artifact is
still mandatory before final-test execution.

## Core P08 invariants

```text
final-test access != model selection
confidence != information sufficiency
abstain != candidate action
FHIR formatting != clinical correctness
faster on different hardware != speed superiority
missing/failed inference != silent exclusion
negative result != disposable result
blocked dependency != permission to hide it
formatting equality != semantic evidence equality
```

No paper-level claim for ECAL, learned information sufficiency, evidence grounding,
counterfactual robustness, FHIR gains, efficiency, baseline superiority, clinical safety, or SOTA
performance is authorized until the real P08 model/data/protocol freeze is complete, audited,
digest-authorized, and evaluated under the preregistered contract.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
