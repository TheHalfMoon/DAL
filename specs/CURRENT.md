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

## Latest closeout — SG-000018

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

This corrects the stale pre-merge digest previously shown in this file. The canonical digest is the
one bound by the SG-000018 calibration manifest and verified by the implementation tests.

### Implementation evidence

- implementation PR: #60
- exact base: `0236a8219cecd03c7d9da52691ff67a8a2262ba4`
- exact implementation head: `bcc216885113a19d9eef8618c821b3712fa0d444`
- exact-head GAXBench CI: run `36635301300` — SUCCESS
- exact-head native-abstention qualification: run `36635301225` — SUCCESS
- exact-head PubMedQA qualification: run `36635301345` — SUCCESS
- exact-head FHIR-AgentBench qualification: run `36635301277` — SUCCESS
- exact-head MedAgentBench qualification: run `36635301311` — SUCCESS
- exact-head MedQAbstain qualification: run `36635301238` — SUCCESS
- exact-head Alibaba OpenCodeReview gate: run `36635301242` — SUCCESS
- exact-head secure Jev review: run `36635297195`, job `109638612830` — PASSED
- Jev coverage: 39/39 exact-diff hunks, zero blocking findings
- guarded normal implementation merge: `dfd9899f7b8b7ba4f515b1d773b806545b0361c3`

### Post-main evidence on implementation merge

- GAXBench CI: run `36636682683` — SUCCESS on Linux/Windows × Python 3.11/3.12
- native-abstention qualification: run `36636682707` — SUCCESS
- PubMedQA qualification: run `36636682657` — SUCCESS
- FHIR-AgentBench qualification: run `36636682597` — SUCCESS
- MedAgentBench qualification: run `36636682626` — SUCCESS
- MedQAbstain qualification: run `36636682649` — SUCCESS

The closeout PR contains only governance/evidence binding and the correction of the stale digest in
this index. The canonical closeout merge is represented by the merge commit that lands this file;
this file does not predict or self-reference a future merge SHA.

## Next governed frontier — P08 real-system qualification

No new final-test authorization exists. Before final-test access can open, a new SpecGrain must
prospectively bind development-only real-system qualification and model/protocol selection.

Authorization-critical unresolved systems:

- DAL/GAX paper candidate — immutable checkpoint identity, training recipe, and seeds;
- clinical encoder — immutable model/tokenizer/source identity and real execution evidence;
- Laya — immutable source/model identity and real execution evidence.

Development-only unresolved selections:

- DAL paper checkpoint and training seed selection;
- ECAL component keep/reject set;
- FHIR representation selection;
- required comparison model/tokenizer revisions.

Secondary/optional systems may be qualified when legally reproducible at zero founder cost, but
missing optional systems must remain explicit blocked/unavailable outcomes rather than silent
exclusions.

A separate digest-bound authorization artifact is still required before any sealed final-test model
inference. No threshold, checkpoint, prompt, ECAL component, FHIR representation, or claim may be
selected from final-test data.

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
