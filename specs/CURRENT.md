# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers remain immutable compatibility and provenance identifiers where they name already-frozen artifacts, schemas, workflows, model roles, or evidence chains. DAL is the current program identity.

## Canonical completed grains

- SG-000001 through SG-000017 — PROVEN under their historical GAX/DAL evidence chains.
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement — CLOSED_CANONICAL.**
- **SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation — CLOSED_CANONICAL at `3ca0dd2aae85a68473849108764a45a538de1019`.**

SG-000019 post-closeout verification succeeded:

- GAXBench CI `36743845440` — SUCCESS on Python 3.11/3.12 × Ubuntu/Windows;
- Real-System Foundation `36743845501` — SUCCESS;
- Issue #63 — closed as completed.

## Active grain — SG-000020

**DAL-P08 — Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze**

Research contract: Issue #69.

Canonical dependency:

`3ca0dd2aae85a68473849108764a45a538de1019`

State: **ACTIVE**

Final-test access: **sealed**

### Frozen system identities inherited from SG-000019

- DAL paper-candidate semantic qualification bundle: `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`;
- matched clinical-encoder semantic qualification bundle: `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`;
- Laya semantic qualification bundle: `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`.

Architecture search is closed after D03. D01 and D02 remain rejected; D03 remains the accepted assurance path. No D04 or equivalent architecture/checkpoint search on the frozen 90-row development-selection set is permitted.

### Frozen calibration contract

- method: `temperature-scaling-action+platt-sufficiency-v0.1`;
- calibration manifest SHA-256: `89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`;
- total reserved calibration rows: 491;
- PubMedQA PQA-L: 50;
- DAL-native evidence-availability surface: 100;
- FHIR-AgentBench: 341;
- coverage targets: `0.50`, `0.80`, `0.90`.

Calibration may fit calibration parameters only. It cannot retrain or reselect the model, backbone, checkpoint, seed, prompt family, or D03 architecture.

### Frozen ECAL candidates

- `evidence`
- `hard-negative`
- `proper-scoring`
- `replay-retention`
- `state-action-contrastive`

SG-000020 must persist the deterministic selection rule and tie-breaks before candidate outcome inspection, retain every null/negative/failed candidate result, and bind the selected configuration to an immutable digest.

### Frozen FHIR representation candidates

- `canonical-structured`
- `canonical-with-narrative`
- `flat-text`
- `source-order-json`

SG-000020 must persist the deterministic selection rule and tie-breaks before candidate outcome inspection, retain every null/negative/parse/interface result, and bind the selected representation to an immutable digest.

### Frozen statistical/runtime policy

- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- failure accounting must preserve requested/completed/timeout/OOM/transport/interface/parse outcomes;
- different hardware classes cannot support direct speed-superiority claims.

### Exit target

SG-000020 must produce a machine-readable **final-test authorization candidate** binding the final selected system/checkpoint, calibration, ECAL, FHIR, coverage, hardware, multiplicity, and evidence digests.

That candidate is **not** authorization. It must explicitly retain `final_test_access = sealed`. A separate later governed grain/PR is required to qualify and explicitly open final-test access before any P08 final-test inference.

## Core P08 invariants

```text
final-test access != model selection
inventory readiness != final-test authorization
authorization candidate != authorization
confidence != information sufficiency
abstain != candidate action
calibration != model retraining
FHIR formatting != clinical correctness
faster on different hardware != speed superiority
missing/failed inference != silent exclusion
negative result != disposable result
blocked dependency != permission to hide it
formatting equality != semantic evidence equality
```

No paper-level claim for ECAL gains, evidence grounding, counterfactual robustness, FHIR gains, efficiency, baseline superiority, clinical safety, regulatory readiness, or SOTA performance is authorized until SG-000020 closes, a separate final-test authorization artifact is qualified, and final evaluation runs exactly under the preregistered contract.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
