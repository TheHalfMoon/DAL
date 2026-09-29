# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers are retained where they name already-frozen
artifacts, workflows, schemas, model roles, or evidence chains. DAL is the current program
identity. A later governed identity-migration grain may rename compatibility surfaces, but it
must not rewrite historical evidence or silently change artifact identity.

## Canonical state

Canonical `main` before the active SG-000018 implementation is:

`a97bd6b637be2d98ef98758749edf5f197cc97f8`

Completed grains:

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

The detailed historical evidence for each completed grain is preserved in its SpecGrain JSON,
its implementation/closeout PRs, Git history, workflow runs, and research evidence files. This
file is intentionally a current-frontier index rather than a second mutable copy of every prior
closeout packet.

## Latest canonical closeout — SG-000017

Research outcome:

- MedQAbstain is reproducibly frozen at immutable dataset revision
  `d215847217bb5f4124b9110379d33b9eb2f8d3f7`.
- 11,232 source rows were identified; 11,215 are construction-eligible and 17 anomalous rows are
  quarantined.
- The metadata-only leakage audit records 5 exact visible duplicate pairs and 1,264 preregistered
  near-duplicate pairs, including 1,261 MedQA 4-option / 5-option pairs.
- The immutable derived dataset exposes no license grant sufficient for paper-required use, so
  the aggregate benchmark remains **blocked**, not silently dropped and not represented as
  qualified.
- Public-pretraining contamination remains unresolved and disclosed.
- Final-test access remained sealed and no model-performance result was produced.

Evidence chain:

- implementation PR: #56
- implementation exact head: `2834eb79b99834b99d738cbebcf4fd948bb49444`
- implementation exact-head GAXBench CI: run `36614891027` — SUCCESS
- implementation exact-head MedQAbstain qualification: run `36614891098` — SUCCESS
- implementation exact-head FHIR-AgentBench regression: run `36614891225` — SUCCESS
- implementation exact-head MedAgentBench regression: run `36614891295` — SUCCESS
- implementation exact-head PubMedQA regression: run `36614891396` — SUCCESS
- implementation merge: `db44fc9b3f76d877cb664065b275e7c9652cc335`
- post-main GAXBench CI: run `36616090694` — SUCCESS
- post-main MedQAbstain qualification: run `36616090738` — SUCCESS
- post-main FHIR-AgentBench regression: run `36616090733` — SUCCESS
- post-main MedAgentBench regression: run `36616090684` — SUCCESS
- post-main PubMedQA regression: run `36616090701` — SUCCESS
- closeout PR: #58
- closeout exact head: `9d7523803be689fde47215e9fe4d69eeac4ef6fd`
- closeout exact-head GAXBench CI: run `36620424236` — SUCCESS
- canonical closeout merge: `a97bd6b637be2d98ef98758749edf5f197cc97f8`

SG-000017 is **CLOSED_CANONICAL**. Its blocked licensing result is preserved as a research result,
not treated as a reason to remove the benchmark after seeing model performance.

## Active frontier — SG-000018 / Issue #57 / PR #60

**P08 — Native licensed abstention benchmark and pre-results paper protocol replacement**

SG-000018 is the sole active governed unit. PR #60 remains a draft until its exact final head is
qualified. Do not bind this file to an intermediate branch SHA; the final implementation head
must be recorded from the PR at qualification/merge time.

### Research purpose

SG-000018 resolves paper-critical blockers prospectively, before final-test model inference:

1. replace the blocked paper-required abstention dependency with a deterministic native benchmark
   derived from already-qualified PubMedQA PQA-L;
2. keep `abstain` outside the ordinary candidate-action distribution;
3. freeze benchmark, calibration, coverage, hardware, multiplicity, ECAL-selection, and
   FHIR-representation policy before final-test access;
4. reclassify non-reproducible heavyweight comparisons as secondary/optional only from
   reproducibility, rights, and zero-founder-cost constraints — never observed model performance;
5. retain MedQAbstain and MedAgentBench runtime blockers visibly in the inventory.

### Native abstention benchmark

The active implementation creates deterministic PubMedQA evidence-availability pairs:

- `evidence-present`: the original closed biomedical action set plus PubMedQA evidence;
- `evidence-withheld`: the same state/action identity with benchmark evidence intentionally removed.

Development/calibration behavior:

- evidence-present preserves typed action supervision and sets `Gold.sufficient=true`;
- evidence-withheld sets `Gold.sufficient=false` and `Gold.action=null`;
- abstention is never inserted into `BenchmarkItem.actions`.

Sealed final-test behavior:

- neither action supervision nor sufficiency supervision is serialized;
- no threshold, prompt, checkpoint, ECAL component, FHIR representation, or paper claim may be
  selected from final-test data;
- this grain performs no final-test model inference.

Frozen inherited source roles are 450 validation / 50 calibration / 500 sealed test source items,
which deterministically produce 900 validation / 100 calibration / 1,000 sealed-test variants.

The benchmark claim scope is deliberately narrow: **evidence-availability insufficiency and
selective-decision behavior under a constructed intervention**. It is not generic clinical-safety,
diagnosis, treatment, triage, or deployment evidence.

### Proposed authorization-critical dataset suite

The SG-000018 pre-results proposal makes these datasets authorization-critical:

- `pubmedqa-pqal` — qualified;
- `gax-native-abstention-pqal` — qualified by the active grain once canonical;
- `fhir-agentbench` — qualified.

These remain visible but secondary/optional for authorization:

- `medagentbench` — public corpus qualified; official external runtime/scorer blocked;
- `medqabstain` — immutable dataset identified, but paper-required use blocked by absent derived
  dataset license grant.

No blocked source is represented as successful and no blocker is removed from the evidence record.

### Proposed protocol freeze

The active inventory proposal freezes, before final-test model inference:

- calibration: `temperature-scaling-action+platt-sufficiency-v0.1`;
- calibration split digest:
  `11d347a4763475749e9f8e63532f1b26023d9d8c16c077b5005961c314f9c291`;
- target coverages: 0.50 / 0.80 / 0.90;
- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- test tuning: forbidden.

These fields are not canonical until SG-000018 implementation merges and post-main qualification
succeeds.

### Current authorization blockers

Even after the SG-000018 dataset/protocol proposal, final-test access remains **sealed**.
Authorization still requires real, immutable execution evidence for the required systems:

- DAL/GAX paper candidate;
- clinical encoder;
- Laya.

CLM, decider, restricted-logit, structured-output LLM, and Jev are secondary/optional under the
active proposal when they can be reproduced legally and at zero founder cost. A missing optional
system must be disclosed, not converted into a hidden success or silently excluded result.

## SG-000018 implementation exit requirements

PR #60 must remain unmerged until all of the following are true on the same exact final head:

- Linux Python 3.11 CI — SUCCESS;
- Linux Python 3.12 CI — SUCCESS;
- Windows Python 3.11 CI — SUCCESS;
- Windows Python 3.12 CI — SUCCESS;
- dedicated native-abstention qualification — SUCCESS;
- affected PubMedQA, FHIR-AgentBench, MedAgentBench, and MedQAbstain regressions — SUCCESS;
- registry and governance documents agree with the typed inventory;
- no final-test inference or test-derived selection occurred;
- independent review evidence is recorded honestly;
- implementation merge uses an expected-head guard and normal merge semantics;
- post-main qualification succeeds;
- a separate closeout marks SG-000018 PROVEN.

No Jev, Alibaba Open Code Review, or other independent-review evidence may be claimed unless the
actual tool execution and its revision-bound result are available. CodeRabbit, Qodo, Cubic, or
similar service output is not qualification evidence for this program.

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

Final-test labels remain sealed. No paper-level claim for ECAL, learned information sufficiency,
evidence grounding, counterfactual robustness, FHIR gains, efficiency, baseline superiority,
clinical safety, or SOTA performance is authorized until the real P08 model/data/protocol freeze
is complete, audited, digest-authorized, and evaluated under the preregistered contract.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
