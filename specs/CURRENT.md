# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers remain immutable compatibility and provenance identifiers where they name already-frozen artifacts, schemas, workflows, model roles, or evidence chains. DAL is the current program identity.

## Canonical completed grains

- SG-000001 through SG-000017 — PROVEN under their historical GAX/DAL evidence chains.
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement — PROVEN.**
- **SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation — PROVEN by this closeout.**

Detailed evidence remains in each SpecGrain JSON, implementation/promotion/closeout PR, Git history, workflow runs, and research evidence files. This file is the current-frontier index rather than a duplicate of every historical packet.

## Latest canonical research outcome — SG-000019

SG-000019 completed the development-only training and real-system qualification foundation without opening the P08 final test.

### Frozen development surface

- source: PubMedQA PQA-L at `1cbae8e92f72f20c8d3747cbb3bf5bc53554d997`;
- qualified source role: 450 development rows;
- nested train: 360 rows;
- nested development-selection: 90 rows;
- calibration reserved: 50 rows;
- sealed final test: 500 rows;
- development manifest SHA-256: `9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c`;
- development leakage-audit SHA-256: `1ed3dc8bbf740888e60d1b36ac7b94d5b3a75c8f120c9129c2ad996e24984a76`.

No calibration or final-test row was used for model training or architecture selection.

### Required-system state

All three authorization-critical systems are now `qualified` in `registry/p08_real_inventory.json` while `final_test_access` remains `sealed`:

- `gax-paper-candidate` — legacy inventory ID for the DAL paper candidate;
- `clinical-encoder` — matched BioClinical ModernBERT control;
- `laya` — frozen real baseline.

Canonical semantic qualification-bundle digests:

- DAL paper candidate: `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`;
- clinical encoder: `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`;
- Laya: `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`.

The inventory audit is authorization-ready with respect to the required system/dataset inventory, but that state **does not itself authorize final-test execution**.

### Paper-candidate development decision

Architecture search on the frozen 90-row development-selection set is closed after D03.

- D01 — rejected;
- D02 — rejected;
- D03 — accepted as the paper assurance path;
- selected seed — 0 for DAL and matched control;
- action accuracy — DAL = control = `0.5555555820465088`;
- control action NLL — `0.9351183772087097`;
- DAL shadow-critic NLL — `0.9342377781867981`;
- DAL sufficiency Brier — `0.007211523596197367` versus preregistered ceiling `0.25`;
- action-superiority claim — **not supported and not made**.

D03 preserves the matched control action outputs and qualifies the additional assurance path; it is not evidence that DAL improves base action-selection accuracy.

### Canonical evidence chain

Foundation tranche:

- PR #65 — merged; genuine Laya development execution preserved, including the weak 48/90 = 53.33% result.

Paper-candidate tranche:

- PR #66 exact head: `31580aee46198b84fcbfe61c70e0522a639a6bb5`;
- exact-head GAXBench CI: `36696007258` — SUCCESS;
- exact-head Alibaba OpenCodeReview: `36696007334` — SUCCESS;
- exact-head secure Jev: `36696003579` — SUCCESS;
- exact-head Real-System Foundation: `36696007260` — SUCCESS;
- exact-head Laya qualification: `36696007254` — SUCCESS;
- exact-head paper training qualification: `36696007200` — SUCCESS;
- implementation merge: `54bdd9e18cf5e7d1dbcbc6dbfd3a4e12e58a70a5`;
- post-main GAXBench CI: `36726951396` — SUCCESS;
- post-main Real-System Foundation: `36726951278` — SUCCESS;
- post-main Laya qualification: `36726951197` — SUCCESS;
- post-main paper training qualification: `36726951419` — SUCCESS.

Required-system promotion tranche:

- PR #67 exact head: `690400ea5de8af457f8206a7fb5b0e52d0f33b77`;
- exact-head GAXBench CI: `36730760363` — SUCCESS;
- exact-head Alibaba OpenCodeReview: `36730760422` — SUCCESS;
- exact-head secure Jev: `36730755431` — SUCCESS;
- exact-head Real-System Foundation: `36730760378` — SUCCESS;
- exact-head Native Abstention: `36730760367` — SUCCESS;
- exact-head PubMedQA: `36730760394` — SUCCESS;
- exact-head FHIR-AgentBench: `36730760411` — SUCCESS;
- exact-head MedAgentBench: `36730760480` — SUCCESS;
- exact-head MedQAbstain: `36730760395` — SUCCESS;
- exact-head Laya: `36730760393` — SUCCESS;
- promotion merge: `de0a14cfb7c77385457c603cd177b734a86b437c`;
- post-promotion GAXBench CI: `36731436133` — SUCCESS;
- post-promotion Native Abstention: `36731436164` — SUCCESS;
- post-promotion PubMedQA: `36731436260` — SUCCESS;
- post-promotion FHIR-AgentBench: `36731436493` — SUCCESS;
- post-promotion MedAgentBench: `36731436398` — SUCCESS;
- post-promotion MedQAbstain: `36731436243` — SUCCESS;
- post-promotion Real-System Foundation: `36731436301` — SUCCESS;
- post-promotion Laya: `36731436447` — SUCCESS.

SG-000019 is eligible for canonical closeout on this governance-only branch. Issue #63 may be closed only after the closeout merge and post-closeout verification succeed.

## Next governed frontier

A new SpecGrain is required before further P08 model/protocol selection. The next grain must remain development/calibration-only and freeze the remaining pre-final-test choices:

1. execute the already-frozen calibration method on the reserved calibration roles without retraining on calibration;
2. select/freeze ECAL component configuration from authorized development/calibration evidence only;
3. select/freeze FHIR representation from authorized development/calibration evidence only;
4. bind selected checkpoint/model/protocol/hardware/multiplicity digests into a final-test authorization candidate;
5. keep final-test access sealed until a separate digest-bound authorization artifact is qualified and merged.

The next grain must not reopen D01–D03 architecture search on the same 90-row development-selection set.

## Core P08 invariants

```text
final-test access != model selection
inventory readiness != final-test authorization
confidence != information sufficiency
abstain != candidate action
FHIR formatting != clinical correctness
faster on different hardware != speed superiority
missing/failed inference != silent exclusion
negative result != disposable result
blocked dependency != permission to hide it
formatting equality != semantic evidence equality
```

No paper-level claim for ECAL gains, evidence grounding, counterfactual robustness, FHIR gains, efficiency, baseline superiority, clinical safety, regulatory readiness, or SOTA performance is authorized until the remaining P08 protocol freeze is complete, a separate final-test authorization artifact is qualified, and final evaluation runs exactly under the preregistered contract.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
