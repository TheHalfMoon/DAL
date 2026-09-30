# DAL P08 Calibration and Selection Protocol — SG-000020

Status: **pre-results contract frozen on the SG-000020 implementation branch; not canonical until merge and post-main qualification**

Research contract: Issue #69.

Canonical dependency: `3ca0dd2aae85a68473849108764a45a538de1019`.

SG-000020 activation revision: `851a4ebdd3bf1654cd5259c6a5e4121965b66144`.

Canonical machine-readable pre-results contract:

`registry/p08_calibration_selection_contract_sg000020.json`

Canonical JSON SHA-256:

`13f05f806ced6a4f2aa67543e1e4236ec0c6208a19905de7158fd96ce6bde637`

P08 final-test access remains **sealed**. This protocol cannot authorize final-test inference.

## 1. Frozen paper checkpoint

The selected DAL paper checkpoint is immutable:

- legacy system ID: `gax-paper-candidate`;
- selected seed: `0`;
- checkpoint SHA-256: `351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b`;
- training-contract SHA-256: `0b9b9bef795d1af39f94e45f89913038f68446f90c045e3747573d11c4a9dc2b`.

The repository does not store the checkpoint bytes directly. A deterministic rebuild is permitted only to recover the already-selected checkpoint. The rebuilt checkpoint must reproduce the frozen digest exactly. A mismatch fails closed and cannot trigger a new checkpoint, seed, model, architecture, or prompt search.

D01 and D02 remain rejected. D03 remains the final accepted assurance architecture. D04 or an equivalent architecture revision is forbidden on the same frozen development-selection set.

## 2. Calibration role separation

Frozen calibration method:

`temperature-scaling-action+platt-sufficiency-v0.1`

Frozen calibration manifest:

`89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`

The 491 reserved rows have distinct purposes:

1. `pubmedqa-pqal` — 50 rows — **action-temperature fit only**;
2. `gax-native-abstention-pqal` — 100 paired rows — **sufficiency Platt fit only**;
3. `fhir-agentbench` — 341 rows — **FHIR representation selection only**.

The PubMedQA action temperature is not fitted across heterogeneous action spaces. FHIR-AgentBench rows do not enter the PubMedQA temperature objective. Native evidence-present/evidence-withheld pairs do not alter the action checkpoint.

Coverage targets remain exactly `0.50`, `0.80`, and `0.90`.

Calibration is parameter fitting, not model training. It cannot change the model backbone, D03 architecture, action head, checkpoint, seed, prompt family, or final-test threshold policy.

## 3. Action-temperature optimizer

The scalar temperature uses the parameterization:

```text
T = exp(log_temperature)
```

The objective is multiclass negative log likelihood on the 50 qualified PubMedQA calibration rows.

The optimization rule is fixed before results:

- search domain for `log_temperature`: `[-5.0, 5.0]`;
- algorithm: deterministic golden-section search;
- iterations: `128`;
- ties: choose the lower `log_temperature`.

No final-test outcome can change this search rule.

## 4. Sufficiency Platt optimizer

The raw D03 sufficiency logit is calibrated as:

```text
p(sufficient) = sigmoid(a * raw_logit + b)
```

The objective is binary cross entropy plus fixed L2 regularization on the 100 native calibration rows.

Frozen optimizer:

- algorithm: deterministic damped two-parameter Newton optimization;
- L2 coefficient: `1e-6`;
- iterations: `100` maximum;
- gradient tolerance: `1e-12`;
- diagonal damping: `1e-8`;
- initial `a = 1.0`;
- initial `b = 0.0`.

The fitted `(a, b)` pair is calibration evidence only. It cannot trigger model or checkpoint reselection.

## 5. ECAL paper-mechanism selection

Frozen candidate order:

1. `evidence`;
2. `hard-negative`;
3. `proper-scoring`;
4. `replay-retention`;
5. `state-action-contrastive`.

SG-000020 does **not** reopen the paper architecture. Therefore ECAL selection in this grain freezes paper mechanism reporting/ablation scope rather than mutating the D03 checkpoint.

A component may be marked `keep` only when all of the following are true:

1. it has an exact canonical implementation/evidence mapping;
2. it is compatible with the frozen D03 checkpoint without retraining or checkpoint mutation;
3. keeping it does not change the frozen action output policy;
4. the evidence record can be reproduced without final-test access.

A component is rejected when it requires new training, changes the frozen checkpoint/action head, or lacks an exact canonical implementation mapping. Every candidate remains in the ledger. Null and negative evidence cannot be deleted.

Historical mapping is frozen before the SG-000020 decision ledger is generated:

- `evidence` → P04 evidence intervention objective plus D03 evidence-delta assurance path;
- `hard-negative` → P04 hard-negative training objective;
- `proper-scoring` → P04 Brier/proper-scoring training objective;
- `replay-retention` → P04 replay sampling policy;
- `state-action-contrastive` → **no exact same-name canonical P04 component**. P04 bidirectional multi-positive alignment is related but must not be silently renamed.

A `keep` decision authorizes only manuscript/ablation scope. It does not change D03 model weights.

## 6. FHIR representation selection

Frozen candidate order:

1. `canonical-structured`;
2. `canonical-with-narrative`;
3. `flat-text`;
4. `source-order-json`.

The FHIR-AgentBench source remains frozen at repository revision:

`bbb42909a5a7eb907d1cd91f72a560729e7037ea`

The 341 qualified calibration rows are the only FHIR-AgentBench rows eligible for representation selection.

The actual FHIR resources are recovered locally from the open **MIMIC-IV Clinical Database Demo on FHIR v2.1.0** rather than a paid GCP FHIR store. The release is frozen by project/version and its official PhysioNet `SHA256SUMS.txt` must be recorded and verified before representation selection.

Source boundary:

- project: `mimic-iv-fhir-demo`;
- version: `2.1.0`;
- license: `ODbL-1.0`;
- access: open;
- release size class: approximately 49.5 MB uncompressed.

Every FHIR candidate must record:

- requested resource count;
- resolved resource count;
- missing-resource failures;
- strict parse/FHIR validation failures;
- repeated-render determinism;
- key-order perturbation behavior;
- narrative exposure;
- rendered byte distribution.

Eligibility requires all referenced calibration resources to resolve, zero strict parse/FHIR validation failures, and deterministic repeated rendering.

`canonical-structured`, `canonical-with-narrative`, and `flat-text` must also be invariant to input key-order perturbation. `source-order-json` is not penalized for source-order sensitivity because preserving source order is its defined behavior, but that sensitivity must be explicitly recorded.

Among eligible representations, select the minimum median rendered byte length. Exact ties use the frozen candidate order above.

This objective intentionally selects a deterministic, compact representation before final-test access. It is not a clinical-performance superiority claim.

## 7. Failure accounting

The ledger preserves these failure categories:

- timeout;
- OOM;
- transport;
- interface;
- parse;
- missing-resource;
- other.

Failures cannot be converted into silent exclusions.

## 8. Final-test authorization candidate

SG-000020 may produce a machine-readable authorization **candidate** binding:

- SG-000019 canonical dependency;
- selected paper checkpoint digest;
- all required-system semantic qualification-bundle digests;
- this SG-000020 pre-results contract digest;
- calibration evidence digest;
- selected ECAL configuration digest;
- selected FHIR representation digest;
- coverage targets;
- hardware protocol `p08-hardware-stratified-v0.1`;
- multiplicity policy `holm-primary-family-v0.1`.

The candidate must contain:

```text
final_test_access = sealed
can_authorize_inference = false
```

A separate later SpecGrain/PR must qualify and explicitly open final-test access. SG-000020 itself is structurally incapable of doing so.

## 9. Review boundary

The exact implementation head must pass:

- Linux/Windows Python 3.11/3.12 CI;
- affected P08 regression qualification;
- checksum-pinned Alibaba OpenCodeReview exact-range evidence;
- secure TypeSafe Jev exact-diff semantic review with complete coverage and zero blocking findings;
- expected-head normal merge;
- post-main qualification;
- separate SG-000020 canonical closeout.

Cubic, CodeRabbit, Qodo, and similar services are not qualification evidence.

## 10. Non-claims

This grain does not establish clinical safety, treatment correctness, autonomous diagnosis, deployment fitness, regulatory readiness, efficiency superiority, baseline superiority, or SOTA performance. Negative and null results remain part of the paper evidence ledger.
