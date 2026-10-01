# DAL Program Tasks

DAL is the current repository and program identity: **Decision Assurance Layer**. Historical `GAX` / `GAXBench` names remain where they identify immutable historical artifacts, revisions, workflows, schemas, or evidence chains.

## P00–P07 — Canonical foundations

- [x] P00 research foundation and publication contract
- [x] P01 benchmark kernel and selective-risk metrics
- [x] P02 matched baseline harness and external transport/revision freeze
- [x] P03 first trainable non-generative historical GAX v0 engineering model
- [x] P04 ECAL controlled-ablation framework
- [x] P05 native information sufficiency and selective abstention framework
- [x] P06 evidence interventions and counterfactual robustness framework
- [x] P07 FHIR interoperable read-only decision layer

## P08 — Full paper evaluation

### Canonical foundation through SG-000019

- [x] Final-test state sealed by default
- [x] Digest-bound final-test authorization schema foundation
- [x] Benchmark split/license/leakage hash requirements
- [x] Calibration and target-coverage contract frozen
- [x] Hardware/timing and multiplicity policies frozen
- [x] PubMedQA PQA-L immutable qualification
- [x] FHIR-AgentBench immutable qualification
- [x] DAL-native licensed abstention replacement
- [x] Paper candidate, matched clinical encoder, and Laya immutable qualification
- [x] Development-only 360-train / 90-selection child split
- [x] Multi-seed `[0,1,2]` checkpoint provenance
- [x] D01 and D02 negative architecture results preserved
- [x] D03 accepted only as the assurance path with unchanged action accuracy
- [x] Architecture search closed after D03
- [x] SG-000019 canonical closeout at `3ca0dd2aae85a68473849108764a45a538de1019`
- [x] SG-000019 post-closeout GAXBench `36743845440` SUCCESS
- [x] SG-000019 post-closeout Real-System Foundation `36743845501` SUCCESS

### SG-000020 — Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze (PROVEN)

Research contract: Issue #69. Canonical closeout: `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.

#### Calibration

- [x] Bind exact calibration manifest `89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`
- [x] Use exactly `temperature-scaling-action+platt-sufficiency-v0.1`
- [x] Confirm calibration roles contain exactly 50 PubMedQA + 100 native-abstention + 341 FHIR-AgentBench rows
- [x] Fit action temperature parameter(s) on permitted calibration evidence only
- [x] Fit sufficiency Platt parameter(s) on permitted calibration evidence only
- [x] Persist calibration parameters and canonical digest
- [x] Persist pre/post calibration diagnostics
- [x] Preserve calibration requested/completed/failure accounting
- [x] Prove calibration does not retrain or reselect model/backbone/checkpoint/seed
- [x] Keep coverage targets exactly `[0.50, 0.80, 0.90]`

#### ECAL selection

- [x] Persist ECAL selection objective before candidate outcome inspection
- [x] Persist deterministic ECAL tie-break rule before candidate outcome inspection
- [x] Evaluate every frozen candidate on authorized development/calibration evidence only
- [x] Preserve every null/negative/failed ECAL outcome
- [x] Freeze selected ECAL configuration
- [x] Bind selected ECAL configuration to immutable digest

#### FHIR representation selection

- [x] Persist FHIR selection objective before candidate outcome inspection
- [x] Persist deterministic FHIR tie-break rule before candidate outcome inspection
- [x] Evaluate every frozen representation on authorized development/calibration evidence only
- [x] Preserve parse/interface/failure accounting for every representation
- [x] Preserve every null/negative FHIR result
- [x] Freeze selected FHIR representation
- [x] Bind selected FHIR representation to immutable digest

#### Final-test authorization candidate

- [x] Bind canonical DAL paper-candidate, clinical-encoder, and Laya bundle digests
- [x] Bind selected calibration evidence digest
- [x] Bind selected ECAL configuration digest
- [x] Bind selected FHIR representation digest
- [x] Bind coverage targets `[0.50, 0.80, 0.90]`
- [x] Bind hardware protocol `p08-hardware-stratified-v0.1`
- [x] Bind multiplicity policy `holm-primary-family-v0.1`
- [x] Preserve explicit `final_test_access = sealed`
- [x] Make authorization candidate fail closed on any digest/revision mismatch
- [x] Require a separate later SpecGrain/PR before final-test access can be opened

#### Qualification and closeout

- [x] Exact-head Linux/Windows Python 3.11/3.12 CI
- [x] Affected P08 regression qualification
- [x] Checksum-pinned Alibaba OpenCodeReview exact-range evidence
- [x] Secure TypeSafe Jev exact-diff review with complete coverage and zero blocking findings
- [x] Guarded normal implementation merge with expected-head SHA
- [x] Post-main qualification
- [x] Canonical evidence promotion with byte/semantic digest verification
- [x] Separate SG-000020 canonical closeout
- [x] SG-000020 post-closeout GAXBench `36839981925` SUCCESS

Final-test access remained **sealed** throughout SG-000020.

### Freeze before final-test access

- [x] Freeze benchmark versions and immutable split manifests
- [x] Freeze DAL paper candidate, clinical control, and Laya identities
- [x] Freeze calibration method, calibration split, and coverage targets
- [x] Freeze hardware/timing protocol and comparability rules
- [x] Freeze multiplicity policy
- [x] Complete required dataset license/redistribution audit
- [x] Complete required train/development/calibration/test leakage audit
- [x] Execute calibration under frozen method without model retraining
- [x] Freeze ECAL component selection
- [x] Freeze FHIR representation selection
- [x] Bind final selected system/protocol/checkpoint digests into an authorization candidate
- [ ] Qualify and merge a separate digest-bound final-test opening artifact under SG-000021

Final-test access remains **sealed** until the last item above is satisfied canonically.

### SG-000021 — Final-test authorization qualification (ACTIVE)

Research contract: Issue #78. Canonical dependency: `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.

- [x] Activate a separate research contract and SpecGrain for final-test authorization
- [ ] Bind SG-000020 canonical closeout and post-closeout CI
- [ ] Bind SG-000020 authorization-candidate semantic digest
- [ ] Re-verify DAL paper-candidate, clinical-encoder, and Laya qualification-bundle digests
- [ ] Re-verify selected paper checkpoint SHA-256
- [ ] Re-verify PubMedQA PQA-L source/split/leakage identity and 500-row final-test scope
- [ ] Re-verify DAL-native abstention source/role/membership/leakage identity and 1000-row final-test scope
- [ ] Re-verify FHIR-AgentBench source/role/patient-membership/leakage identity and 173-row/40-patient final-test scope
- [ ] Preserve MedAgentBench/MedQAbstain blocked-secondary and MedMCQA/MedQA/Med-PRM non-authorization states
- [ ] Bind frozen calibration, ECAL, FHIR, coverage, hardware, multiplicity, failure-accounting, and no-post-test-tuning policies
- [ ] Bind explicit zero-founder-cost requirement
- [ ] Create a machine-readable authorization artifact with deterministic self-verifying authorization digest
- [ ] Prove branch-local authorization cannot trigger final-test inference
- [ ] Qualify exact-head Linux/Windows Python 3.11/3.12 CI
- [ ] Qualify checksum-pinned Alibaba OpenCodeReview exact-range evidence
- [ ] Qualify secure TypeSafe Jev exact-diff review with complete coverage and zero blocking findings
- [ ] Merge authorization with normal expected-head guard
- [ ] Verify post-main authorization artifact from canonical `main`
- [ ] Complete separate SG-000021 canonical closeout

No final-test inference, prediction generation, metric computation, or final-test error review is permitted inside SG-000021.

### Primary paper evaluation — after canonical SG-000021 authorization only

- [ ] Main action-selection tables
- [ ] NLL, Brier, ECE, and reliability analysis
- [ ] Risk-coverage curves, AURC, and risk@50/80/90
- [ ] Matched-coverage abstention analysis
- [ ] ECAL selected configuration and declared ablations
- [ ] Evidence-intervention evaluation
- [ ] Counterfactual material-sensitivity and irrelevant-edit stability evaluation
- [ ] FHIR representation and EHR-agent action-selection evaluation
- [ ] Distribution-shift slices
- [ ] Failure taxonomy and qualitative error analysis
- [ ] Latency, throughput, peak-memory, and scaling analysis under frozen hardware protocol
- [ ] Paired bootstrap confidence intervals and declared primary comparisons
- [ ] Preserve null, negative, timeout, OOM, and parse/interface-failure outcomes

### Reproducibility and claim freeze

- [ ] Complete evidence packet for every paper-table row
- [ ] Generate every table from raw versioned artifacts
- [ ] Generate every figure from raw versioned artifacts
- [ ] Map every manuscript claim to exact evidence or explicit rejection
- [ ] Freeze P08 final results without post-test tuning
- [ ] Canonical P08 closeout

## P09 — arXiv and release

- [ ] Paper manuscript
- [ ] Appendix
- [ ] Reproducibility bundle
- [ ] Governed DAL naming migration / GAXBench compatibility release
- [ ] Model release
- [ ] Fine-tuning notebooks
- [ ] Hugging Face release
- [ ] arXiv submission package
- [ ] Public release tag

## P10 — Peer review / external validation

- [ ] Independent reproduction
- [ ] Active venue CFP review
- [ ] Peer-reviewed submission
- [ ] Reviewer response artifacts
- [ ] Journal extension decision
