# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers remain immutable compatibility and provenance identifiers where they name already-frozen artifacts, schemas, workflows, model roles, or evidence chains. DAL is the current program identity.

## Canonical completed grains

- SG-000001 through SG-000017 — PROVEN under their historical GAX/DAL evidence chains.
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement — CLOSED_CANONICAL.**
- **SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation — CLOSED_CANONICAL at `3ca0dd2aae85a68473849108764a45a538de1019`.**
- **SG-000020 — DAL-P08 Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze — CLOSED_CANONICAL at `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.**
- **SG-000021 — DAL-P08 Final-test authorization qualification — PROVEN by this canonical closeout state transition; implementation main is `1daa55d9742050f37fe56d2c84ccf4c8743ef984`.**

## SG-000020 canonical evidence

Research contract: Issue #69.

Canonical evidence-promotion main before closeout:

`7464393fd955e9653a59d6535f0c46a03522a384`

Implementation and repair chain:

- PR #72 implementation merged at `9180dd5c0fcda3ae619eeffeab3aee0fc04da291`;
- PR #74 reproducibility repair merged at `f69eb3ee5b0c0313b10cf8a628f298229b1082ca`;
- PR #75 canonical evidence promotion merged at `7464393fd955e9653a59d6535f0c46a03522a384`;
- PR #76 closeout merged at `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.

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
- FHIR references resolved: `7382/7382`, zero missing;
- authorization-candidate semantic SHA-256: `3f4000cb5616578332a85d00aeda18e120c2b959d59e32375696cd53486b5484`;
- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- coverage targets: `[0.50, 0.80, 0.90]`.

Reproducibility is fail-closed: live calibration inference must remain within absolute raw-logit drift `1e-4` of the canonical evidence before canonical replay is accepted. The post-main reproducibility run observed maximum drift `1.43051147461e-05` and reproduced all frozen semantic digests exactly.

Qualification evidence includes exact-head Linux/Windows Python 3.11/3.12 CI, checksum-pinned Alibaba OpenCodeReview, secure TypeSafe Jev exact-diff review, real SG-000020 execution, canonical evidence promotion, and post-main verification. No Cubic, CodeRabbit, Qodo, or similar output is qualification evidence.

## SG-000021 canonical authorization evidence

Research contract: Issue #80.

Canonical dependency:

`ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`

Authorization implementation:

- activation PR #81 merged at `f8ac88c34557902d760d49b36227010d4fdc46a9`;
- implementation PR #82 exact head `c88bbac110169a48ae6ce2288c5228a0d2b9980f`;
- exact-head GAXBench CI `36866528564` — SUCCESS on Linux/Windows Python 3.11/3.12;
- exact-head Alibaba OpenCodeReview `36866528579` — SUCCESS;
- exact-head secure TypeSafe Jev `36866521762` — SUCCESS;
- implementation merged normally at `1daa55d9742050f37fe56d2c84ccf4c8743ef984` with expected-head guard;
- post-main GAXBench `36866791467` — SUCCESS.

Canonical authorization artifact:

`registry/p08_final_test_authorization_sg000021.json`

Authorization SHA-256:

`626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`

The authorization is scoped **only** to `SG-000022`. SG-000021 itself executed no final-test inference and used exactly zero final-test rows. The authorization binds the required DAL paper candidate, clinical encoder, Laya, paper checkpoint, three authorization-critical dataset identities, frozen calibration, ECAL selection, FHIR selection, coverage targets, hardware protocol, multiplicity policy, failure accounting, and no-post-test-tuning policy.

No model, checkpoint, seed, architecture, calibration, ECAL, FHIR, coverage, hardware, multiplicity, prompt/interface, comparison-family, or failure-accounting reselection is permitted after authorization. Any such change invalidates the authorization and requires a new governed experiment revision.

## Next frontier — SG-000022

**P08 final evaluation under canonical authorization**

State: **NOT YET ACTIVATED**

SG-000022 may be activated only from the canonical SG-000021 closeout. It may consume the SG-000021 authorization artifact and access only the preregistered final-test surfaces bound by that artifact.

The next grain must preserve complete requested/completed/failure accounting; generate immutable raw result artifacts; retain null, negative, timeout, OOM, transport, parse, and interface failures; and prohibit all post-test tuning or reselection.

No paper claim becomes supported merely because SG-000021 authorized evaluation. Claims require SG-000022 result evidence and later claim-ledger qualification.

## Core P08 invariants

```text
final-test access != model selection
inventory readiness != final-test authorization
authorization candidate != authorization
authorization != evaluation
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

No paper-level claim for ECAL gains, evidence grounding, counterfactual robustness, FHIR gains, efficiency, baseline superiority, clinical safety, regulatory readiness, or SOTA performance is authorized until SG-000022 runs exactly under the canonical SG-000021 authorization and the resulting evidence is qualified.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
