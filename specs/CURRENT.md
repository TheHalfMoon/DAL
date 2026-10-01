# Current Frontier

Program: **DAL — Decision Assurance Layer**

Repository: `TheHalfMoon/DAL`

Historical `GAX` / `GAXBench` identifiers remain immutable compatibility and provenance identifiers where they name already-frozen artifacts, schemas, workflows, model roles, or evidence chains. DAL is the current program identity.

## Canonical completed grains

- SG-000001 through SG-000017 — PROVEN under their historical GAX/DAL evidence chains.
- **SG-000018 — DAL-P08 Native licensed abstention benchmark and pre-results protocol replacement — CLOSED_CANONICAL.**
- **SG-000019 — DAL-P08 Paper-candidate training freeze and required-system qualification foundation — CLOSED_CANONICAL at `3ca0dd2aae85a68473849108764a45a538de1019`.**
- **SG-000020 — DAL-P08 Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze — CLOSED_CANONICAL at `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.**
- **SG-000021 — DAL-P08 Final-test authorization qualification — CLOSED_CANONICAL at `ef36ae4d050cf2e1bb7ada07f4054b083e886045`; post-closeout GAXBench `36868102682` SUCCESS.**
- **SG-000022 — DAL-P08 Authorized primary final evaluation — PROVEN by this canonical closeout state transition; canonical evidence-promotion main is `4417a0fc294a3d35f76e54958f151884bf8bfe80`.**

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

Research contract: Issue #80 — completed.

Canonical dependency:

`ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`

Authorization implementation and closeout:

- activation PR #81 merged at `f8ac88c34557902d760d49b36227010d4fdc46a9`;
- implementation PR #82 exact head `c88bbac110169a48ae6ce2288c5228a0d2b9980f`;
- exact-head GAXBench CI `36866528564` — SUCCESS on Linux/Windows Python 3.11/3.12;
- exact-head Alibaba OpenCodeReview `36866528579` — SUCCESS;
- exact-head secure TypeSafe Jev `36866521762` — SUCCESS;
- implementation merged normally at `1daa55d9742050f37fe56d2c84ccf4c8743ef984` with expected-head guard;
- implementation post-main GAXBench `36866791467` — SUCCESS;
- governance closeout PR #83 exact head `6ff33ad96e636418429abf842175919243e66ecd`;
- closeout GAXBench `36867843947` — SUCCESS;
- closeout Alibaba OpenCodeReview `36867844045` — SUCCESS;
- closeout secure TypeSafe Jev `36867843711` — SUCCESS;
- closeout merged normally at `ef36ae4d050cf2e1bb7ada07f4054b083e886045`;
- post-closeout GAXBench `36868102682` — SUCCESS.

Canonical authorization artifact:

`registry/p08_final_test_authorization_sg000021.json`

Authorization SHA-256:

`626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`

The authorization is scoped **only** to `SG-000022`. SG-000021 itself executed no final-test inference and used exactly zero final-test rows. The authorization binds the required DAL paper candidate, clinical encoder, Laya, paper checkpoint, three authorization-critical dataset identities, frozen calibration, ECAL selection, FHIR selection, coverage targets, hardware protocol, multiplicity policy, failure accounting, and no-post-test-tuning policy.

No model, checkpoint, seed, architecture, calibration, ECAL, FHIR, coverage, hardware, multiplicity, prompt/interface, comparison-family, denominator, exclusion-rule, or failure-accounting reselection is permitted after authorization.

## SG-000022 canonical final-evaluation evidence

Research contract: Issue #84 — primary final-evaluation scope completed.

Canonical dependency:

`ef36ae4d050cf2e1bb7ada07f4054b083e886045`

Authorization digest:

`626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`

Governed execution chain:

- activation PR #85 exact head `638eec3132ca3ac87a9f36db8f195f1310a396f0` passed GAXBench `36868975243`, Alibaba OpenCodeReview `36868975233`, and secure TypeSafe Jev `36868975703`, then merged at `c7ea6fbc81a1dd7526a6c453d12c585db6841cb3`;
- activation post-main GAXBench `36869200519` — SUCCESS;
- implementation PR #86 exact head `563883489fdb3df5ae337267cc2510d31551e53e` passed GAXBench `36885982630`, Alibaba OpenCodeReview `36885982580`, and secure TypeSafe Jev `36886188326`, then merged at `42e09ca1b1431340b26fe57ae318ff1b1b662fc3`;
- implementation post-main GAXBench `36886206716` — SUCCESS;
- prospective execution-transport PR #87 exact head `4cfee6e2b23637c117549c149efdd335456557c6` passed GAXBench `36886639294`, Alibaba OpenCodeReview `36886639411`, and secure TypeSafe Jev `36886639719`, then merged at `f1955d5beeb2444f1d604626629036196a1dedd5`;
- one-shot final-evaluation run `36886952302` — SUCCESS;
- execution-main GAXBench `36886952212` — SUCCESS;
- canonical evidence PR #89 exact head `4ae8b39010a2b55f33258fdbf57ce1abc7a13ff3` passed GAXBench `36902369992`, Alibaba OpenCodeReview `36902369988`, and secure TypeSafe Jev `36902370171`, then merged at `4417a0fc294a3d35f76e54958f151884bf8bfe80`;
- evidence-promotion post-main GAXBench `36902663435` — SUCCESS.

The execution transport changed prospectively before final-test access because the connected interface could not invoke `workflow_dispatch`. PR #87 changed only transport to a fail-closed one-shot canonical-main sentinel, recorded zero final-test rows and no outcome information before amendment, and changed no scientific binding or policy.

Canonical result evidence root:

`registry/p08_sg000022_final_evaluation/`

Source Actions artifact ID: `11176566473`.

Source artifact ZIP SHA-256:

`8dcd894be6ae184aaf5311417d268a5500b89d0d78d14ee7a79305fbb3071136`

Frozen primary result facts:

- PubMedQA requested/completed: `500/500`; DAL accuracy `0.552`; matched clinical-control accuracy `0.552`; Laya accuracy `0.530`;
- DAL-minus-control PubMedQA accuracy estimate `0.0`, 95% paired-bootstrap CI `[0.0, 0.0]`;
- native abstention requested/completed: `1000/1000`; DAL risk@80 `0.655`; control risk@80 `0.6675`;
- DAL-minus-control native risk@80 estimate `-0.0125` (lower is better), 95% paired-bootstrap CI approximately `[-0.0200, -0.0050]`;
- unfavorable DAL target-policy outcomes are canonical: target coverage `0.8` and `0.9` both yielded actual coverage `1.0` and unsafe-commit rate `1.0`;
- FHIR-AgentBench remained `interface-blocked-preexecution`: denominator `173`, zero gold rows loaded, zero completed, and `173` interface failures per required system; no post-authorization adapter was created;
- Laya completed all 500 PubMedQA rows, but its pinned runtime emitted invalid/out-of-range-temperature warnings; affected confidence entries are uncalibrated and cannot support calibrated-confidence claims;
- no primary p-values were emitted because no p-value construction was preregistered; no significance, superiority, clinical-safety, regulatory-readiness, or SOTA claim is authorized from SG-000022.

All raw artifacts were persisted before derived metrics. Negative, null, blocked, failure, and calibration-pathology outcomes are immutable evidence. SG-000022 must not be rerun or tuned in response to these results.

## Next frontier — SG-000023

**P08 immutable post-final analysis, claim freeze, and paper-evidence packaging**

State: **NOT YET ACTIVATED**

SG-000023 must start only after the SG-000022 canonical closeout reaches `main` and passes post-closeout qualification. It may consume the immutable SG-000022 evidence and existing frozen development/calibration evidence only for analysis, limitations, claim-ledger mapping, reproducibility packets, and paper tables/figures that do not require a new final-test experiment.

SG-000023 must not rerun SG-000022 final-test inference; retrain or reselect models; refit calibration; create a new FHIR adapter; reselect ECAL/FHIR representations; alter denominators, coverage targets, metrics, bootstrap settings, multiplicity, comparison families, failure accounting, or exclusion rules; or convert blocked/negative outcomes into unsupported positive claims.

Remaining P08 tasks not actually executed by SG-000022 remain open. In particular, no completed status is asserted yet for the broader ECAL-ablation reporting, evidence-intervention analysis, counterfactual analysis, FHIR action evaluation beyond the canonical interface block, distribution-shift slices, frozen-hardware efficiency measurements, qualitative error analysis, or complete paper table/figure/claim-ledger packaging.

## Core P08 invariants

```text
final-test access != model selection
inventory readiness != final-test authorization
authorization candidate != authorization
authorization != evaluation
evaluation != supported claim
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

No paper-level claim becomes supported merely because a metric exists. Every claim must be mapped to canonical evidence or explicitly rejected, and the completed SG-000022 experiment remains under a permanent no-post-test-tuning/no-rerun lock.

Research claims remain subject to `docs/research/REPRODUCIBILITY.md`.
