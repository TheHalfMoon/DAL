# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers remain immutable compatibility and provenance identifiers where they name already-frozen artifacts, schemas, workflows, model roles, or evidence chains. DAL is the current program identity.

## Canonical completed grains

- SG-000001 through SG-000017 — PROVEN under their historical GAX/DAL evidence chains.
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement — CLOSED_CANONICAL.**
- **SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation — CLOSED_CANONICAL at `3ca0dd2aae85a68473849108764a45a538de1019`.**
- **SG-000020 — DAL-P08 Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze — CLOSED_CANONICAL at `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.**

SG-000020 post-closeout GAXBench run `36839981925` succeeded on Linux/Windows × Python 3.11/3.12.

## SG-000020 canonical evidence

Research contract: Issue #69 — completed.

Canonical frozen outputs:

- calibration method: `temperature-scaling-action+platt-sufficiency-v0.1`;
- canonical raw calibration logits SHA-256: `6aca49fd1a94be649737bc6076a9d818b6b67718fb1dac2412766ea8e286f109`;
- calibration evidence semantic SHA-256: `025d92c2d704dfa3889e267be8fac17037d034b5760e635886c536d198c8c8dc`;
- ECAL selection semantic SHA-256: `3bfb069bfdd3ee50890f97c3e4744024af14cb9c9a62211cca008eb4c5ef9bb8`;
- selected ECAL reporting component: `evidence`;
- rejected ECAL candidates: `hard-negative`, `proper-scoring`, `replay-retention`, `state-action-contrastive`;
- FHIR selection semantic SHA-256: `79ddfd4336b5b8a8376ff9761d40ae46fe890eef9962bc6205e8622533b85b9a`;
- selected FHIR representation: `canonical-structured`;
- selected FHIR representation semantic SHA-256: `10665e1fec0be7ec6d2bf6e3710f54b26ded79a16dc48d032a15c8862112963b`;
- authorization-candidate semantic SHA-256: `3f4000cb5616578332a85d00aeda18e120c2b959d59e32375696cd53486b5484`;
- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- coverage targets: `[0.50, 0.80, 0.90]`.

The SG-000020 authorization candidate remains non-executable and used zero final-test rows.

## Active grain — SG-000021

**DAL-P08 — Digest-bound final-test authorization qualification**

Research contract: Issue #78.

Canonical dependency:

`ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`

State: **ACTIVE**

Activation final-test access: **sealed**

SG-000021 is authorization-only. It must not run final-test inference, generate final-test predictions, compute final-test metrics, inspect final-test errors, or change any model/protocol choice.

### Authorization-critical systems

- DAL paper-candidate semantic bundle: `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`;
- clinical-encoder semantic bundle: `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`;
- Laya semantic bundle: `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`;
- selected DAL paper checkpoint SHA-256: `351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b`.

### Authorization-critical final-test surfaces

- `pubmedqa-pqal`: 500 frozen final-test rows; split manifest `7f5c65b88161911179fd95b372e615d802ba6558bc8bc64661bb447b38ed7723`;
- `gax-native-abstention-pqal`: 1000 frozen derived final-test rows; role manifest `d64bfdf057afeaae35fb4209a8513dfc48a6c52e2abd08260dbf111afec1474f`;
- `fhir-agentbench`: 173 patient-disjoint final-test rows across 40 patients; role manifest `7065cede39bdfea3db33d025687210f30f26683a38063f7150a807cd89f5e76c`.

MedAgentBench official runtime and MedQAbstain remain blocked and non-authorization-critical. MedMCQA/Med-PRM remain pending and MedQA remains blocked. They must stay visible but cannot silently enter the primary authorization scope.

### Authorization boundary

A branch-local artifact is not effective authorization. SG-000021 may set a machine-readable authorization artifact to `final_test_access = authorized` and `can_authorize_inference = true` only when every frozen binding validates exactly, but final-test execution remains forbidden until:

1. the authorization PR passes exact-head CI, Alibaba OpenCodeReview, and secure TypeSafe Jev;
2. the PR merges normally with an expected-head guard;
3. post-main authorization qualification succeeds;
4. the authorization artifact verifies from canonical `main`;
5. a later execution grain consumes that canonical authorization.

Any stale digest, revision, role/split identity, blocked-required dependency, or policy mismatch fails closed.

## Core P08 invariants

```text
final-test access != model selection
inventory readiness != final-test authorization
authorization candidate != authorization
branch-local authorization != canonical authorization
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

No paper-level claim for ECAL gains, evidence grounding, counterfactual robustness, FHIR gains, efficiency, baseline superiority, clinical safety, regulatory readiness, or SOTA performance is authorized by SG-000021 itself.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
