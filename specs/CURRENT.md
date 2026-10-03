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
- **SG-000022 — DAL-P08 Authorized primary final evaluation — CLOSED_CANONICAL at `421ad093e1b89df69e10c763ec2474853c09d0e3`; post-closeout GAXBench `36903592739` SUCCESS.**
- **SG-000023 — DAL-P08 Immutable post-final analysis, claim freeze, and paper evidence packaging — CLOSED_CANONICAL at `f8e075c7620d32614ad0d6ca163e0f7db56e35da`; P08 CLOSED_CANONICAL.**
- **SG-000024 — DAL-P09 Study 0 manuscript and release-candidate packaging — CLOSED_CANONICAL; P08 and SG-000024 together form DAL Pilot Study / Study 0.**

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

Research contract: Issue #84 — completed.

Canonical closeout:

`421ad093e1b89df69e10c763ec2474853c09d0e3`

Post-closeout GAXBench:

`36903592739` — SUCCESS on Linux/Windows Python 3.11/3.12.

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
- evidence-promotion post-main GAXBench `36902663435` — SUCCESS;
- canonical closeout PR #90 exact head `b274b97f63caefc7365a1310cc0b032899859153` passed GAXBench `36903313627`, Alibaba OpenCodeReview `36903313590`, and secure TypeSafe Jev `36903313312`, then merged at `421ad093e1b89df69e10c763ec2474853c09d0e3`;
- closeout post-main GAXBench `36903592739` — SUCCESS.

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

## SG-000023 canonical post-final evidence package and claim freeze

Research contract: Issue #91 — completed.

Canonical dependency: `421ad093e1b89df69e10c763ec2474853c09d0e3` (SG-000022 closeout; post-closeout GAXBench `36903592739`).

Governed chain (each step qualified on its exact head with Linux/Windows Python 3.11/3.12 GAXBench, checksum-pinned Alibaba OpenCodeReview, and secure TypeSafe Jev; merged normally with an expected-head guard; post-main GAXBench verified):

- activation PR #92 exact head `e3e4ad8305815f5ee6a4cbe3baf1d354d0fe4f90` (GAXBench `36904301087`, OCR `36904301186`, Jev `36904754175`) merged at `7da5e1e2efc17e5fdad42e1d80da25139de74317`; post-main `36904770004`;
- evidence-availability matrix PR #94 exact head `18b2d36d6a5f4d357132973c0be2812f2db1d6a1` (GAXBench `36906443747`, OCR `36906443642`, Jev `36906444138`) merged at `fd77fbab3ebcf9917469ae189b167874b3e058b9`; post-main `36906737047`;
- derivation contract PR #95 exact head `ba01ab0beeb800d09008bd0e455a02bf3f8a91be` (GAXBench `36907598649`, OCR `36907598277`, Jev `36907593827`) merged at `d676beccfec001fd75d1b157b43068eb49a5733d`; post-main `36907824212`;
- paper-evidence package PR #96 exact head `78ac44b42a46e1ebe85e3f36bf04ea0ccd10d7eb` (GAXBench `36918104968`, OCR `36918105124`, Jev `36918100766`) merged at `a18c1e10a0d9eba16ba8bffc55b29988507772ff`; post-main `36918621970`;
- related-work refresh PR #97 exact head `f80fe231156c4cdc0b3be24cfdae57bfd4c2c135` (GAXBench `36920915256`, OCR `36920915443`, Jev `36920909597`) merged at `5ae1232fd6b66978e13a30a3046e8604bbff68cf`; post-main `36921122600`;
- ECAL table, figures, and action identity PR #98 exact head `b1ea52ecc78e61ecb9cc90bd9f7d204151d11a02` (GAXBench `36922216630`, OCR `36922216751`, Jev `36922216491`) merged at `fabbfdd9045415d49f91d56e4e1ba3cd24ac5c1d`; post-main `36922469753`;
- final result and claim freeze PR #99 exact head `3a359e7f8c9692a8798d09a8e1720a4fcc437195` (GAXBench `36922998071`, OCR `36922998021`, Jev `36922998241`) merged at `01831d44123e4db61a1f73116b6654d404b96fd8`; post-main `36923178122`.

Canonical artifacts:

- evidence-availability matrix: `registry/p08_sg000023_evidence_availability_matrix.json`;
- derivation contract: `registry/p08_sg000023_derivation_contract.json`;
- related-work refresh (2026-10-01, free sources only): `registry/p08_sg000023_related_work_refresh.json`;
- paper evidence package (14 artifacts, deterministic `--check`): `registry/p08_sg000023_paper_evidence/`, built by `tools/build_sg000023_paper_evidence.py`, which pins byte SHA-256 for every canonical input and refuses to derive on mismatch;
- claim freeze: `registry/p08_sg000023_paper_evidence/claim_freeze_manifest.json`, claim-set SHA-256 `ef2e347d9ef4298deb68a422c063aa92e9968ae5d00fb0c511576448eb7a2b9b`.

Frozen claim set: 8 affirmative claims (SG23-C001–C006, C012, C014) and 6 limitation-only statements (SG23-C007–C011, C013). Every exported claim is bound to an evidence packet whose canonical sources cover the claim's cited sources. Any change to a frozen result or claim requires a new governed SpecGrain and may not be motivated by final-test outcomes.

Findings frozen by SG-000023 beyond the SG-000022 headline results:

- the paper system and the clinical control emit identical action-probability vectors on 500/500 PubMedQA final rows and identical action correctness on 1000/1000 native rows; they differ only in selection scores, so the PubMedQA comparison isolates no action-selection difference;
- no ECAL benefit is established: SG-000020 kept `evidence` for frozen-checkpoint compatibility, not for a measured ablation benefit, and every P04 paper decision is `defer-real-data`;
- the related-work refresh removed every "first"-style novelty claim (medical abstention, governance/assurance layer, typed-decision evaluation in medicine, typed-readout accuracy benefit, pre-registered typed-decision evaluation, hash-verified provenance / evidence ledger, FHIR capability, counterfactual robustness) and narrowed native-abstention superiority to descriptive reporting;
- evidence interventions and counterfactual robustness remain blocked (synthetic mechanics only), distribution-shift slices remain unavailable, direct efficiency remains blocked, and FHIR action selection remains interface-blocked.

## P08 closeout

P08 is **CLOSED_CANONICAL** at the SG-000023 closeout. The P08 exit gate — all paper figures and tables generated from evidence packets — is met by `EP-SG23-TABLES-001` and `EP-SG23-FIGURES-001`. Closeout does not convert blocked or unavailable analyses into results; those rows stay explicit in `evidence_boundaries.json` and the claim ledger.

## DAL Pilot Study / Study 0 — closed

On 2026-10-02 the founder authorized a scientific restart. The complete P08 evaluation (SG-000018 to SG-000023) and the SG-000024 manuscript and release package are preserved, unchanged, as **DAL Pilot Study / Study 0**.

- SG-000024 is **CLOSED_CANONICAL**. Its chain is PRs #102 to #105, each qualified on its exact head with GAXBench, Alibaba OpenCodeReview, and secure Jev and verified post-main. The final merge is `cf9212eca4c37be3c9b8af65db703f7b40341c9b`.
- The deterministic arXiv source bundle (SHA-256 `94c91de9912f188df6b6e56782b8f9f99c43c59b66eb8a72c29d607787c029a3`) compiles standalone. Nothing was submitted or published.
- Study 0 results, including the PubMedQA 0.552 tie, the identical action probabilities, the descriptive risk@80 difference, the unsafe-commit failure, the Laya calibration limitation, and the FHIR block, remain immutable historical evidence under the frozen claim set `ef2e347d9ef4298deb68a422c063aa92e9968ae5d00fb0c511576448eb7a2b9b`.
- Study 0 no longer constrains the architecture of the definitive study.
- **The SG-000022 PubMedQA PQA-L final test has been inspected. It may be used only as pilot evidence and never as a blind final evaluation for any later study.**

## Study 1 redesign foundation — SG-000025 closed

**Research redesign, pilot diagnosis, and preregistered protocol**

Research contract: Issue #107. Canonical dependency: `4e6ed79aebffce10d812bf6871888eb028b8af09` (Study 0 closeout).

State: **CLOSED_CANONICAL**

SG-000025 completed the Study 1 redesign without model training, tuning, Study 1 evaluation, or sealed-final label inspection. Canonical outputs are the D1 pilot forensic diagnosis, literature refresh and novelty-gap boundary, benchmark/licensing/contamination dossier, zero-cost compute plan, preregistered protocol, and `registry/study1_sg000025_closeout.json`. The FHIR-AgentBench final role remains sealed at 40 patients / 173 rows with `test_gold_serialized=false`. Study 0 PubMedQA PQA-L rows remain pilot-only and can never be a blind final evaluation.

D2 baseline qualification is now activated separately as **SG-000026** under Issue #115, with canonical dependency `16682ea9dff2f3ccfb0ed818b352eaaa0ccdc167`. D2 is limited to B0/B1/B2 semantic/interface qualification, deterministic denominator accounting, and read-only local FHIR R4 compatibility on the governed 341-row calibration and 1122-row validation roles. The 40-patient / 173-row final role remains sealed and forbidden to D2.

## Active frontier — Study 1, SG-000026 / D2

**Baseline qualification and local FHIR compatibility**

Research contract: Issue #115. Contract artifact: `registry/study1_sg000026_contract.json`. Recovery governance gate: Issue #120.

State: **ACTIVE — OPTION_A_AUTHORIZED / CUSTODIAN_PENDING_CANONICALIZATION**

Canonical D2 grains now include activation (PR #116, merge `e4b9e22`), the B0/B1/B2 semantic and exact denominator-accounting kernel (PR #117, merge `0cfc2db`), the synthetic read-only FHIR compatibility kernel and sealed-role firewall (PR #118, merge `5ea436e`), and the zero-cost MIMIC-IV FHIR Demo v2.1.0 runtime/checksum manifest (PR #119, merge `aa59981`). Each grain was exact-head qualified before normal merge and post-main verified.

The remaining D2 blocker is real FHIR-AgentBench qualification on the governed 341-row calibration + 1122-row validation projection. Canonical DAL artifacts intentionally do not serialize a development-only row projection or patient-role membership map, while the frozen public source CSV also contains the sealed 40-patient / 173-row final role. Reconstructing the development projection therefore requires an explicit governance decision under Issue #120; no metadata-only custodian exception, protocol amendment, or final-role access is authorized yet.

D3 architecture candidates, D4 training/objective experiments, D5 calibration/assurance development, D6 ablations, D7 model selection, D8 protocol freeze, D9 untouched final evaluation, and D10 paper evidence/publication packaging remain unactivated. The sealed final role remains untouched and forbidden to D2.

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
