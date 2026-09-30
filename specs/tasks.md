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

### SG-000020 — Calibration, ECAL, FHIR selection, and final-test authorization candidate freeze (ACTIVE)

Research contract: Issue #69. Canonical dependency: `3ca0dd2aae85a68473849108764a45a538de1019`.

#### Calibration

- [ ] Bind exact calibration manifest `89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`
- [ ] Use exactly `temperature-scaling-action+platt-sufficiency-v0.1`
- [ ] Confirm calibration roles contain exactly 50 PubMedQA + 100 native-abstention + 341 FHIR-AgentBench rows
- [ ] Fit action temperature parameter(s) on permitted calibration evidence only
- [ ] Fit sufficiency Platt parameter(s) on permitted calibration evidence only
- [ ] Persist calibration parameters and canonical digest
- [ ] Persist pre/post calibration diagnostics
- [ ] Preserve calibration requested/completed/failure accounting
- [ ] Prove calibration does not retrain or reselect model/backbone/checkpoint/seed
- [ ] Keep coverage targets exactly `[0.50, 0.80, 0.90]`

#### ECAL selection

Frozen candidate set:

- `evidence`
- `hard-negative`
- `proper-scoring`
- `replay-retention`
- `state-action-contrastive`

Tasks:

- [ ] Persist ECAL selection objective before candidate outcome inspection
- [ ] Persist deterministic ECAL tie-break rule before candidate outcome inspection
- [ ] Evaluate every frozen candidate on authorized development/calibration evidence only
- [ ] Preserve every null/negative/failed ECAL outcome
- [ ] Freeze selected ECAL configuration
- [ ] Bind selected ECAL configuration to immutable digest

#### FHIR representation selection

Frozen candidate set:

- `canonical-structured`
- `canonical-with-narrative`
- `flat-text`
- `source-order-json`

Tasks:

- [ ] Persist FHIR selection objective before candidate outcome inspection
- [ ] Persist deterministic FHIR tie-break rule before candidate outcome inspection
- [ ] Evaluate every frozen representation on authorized development/calibration evidence only
- [ ] Preserve parse/interface/failure accounting for every representation
- [ ] Preserve every null/negative FHIR result
- [ ] Freeze selected FHIR representation
- [ ] Bind selected FHIR representation to immutable digest

#### Final-test authorization candidate

- [ ] Bind canonical DAL paper-candidate bundle digest `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`
- [ ] Bind canonical clinical-encoder bundle digest `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`
- [ ] Bind canonical Laya bundle digest `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`
- [ ] Bind selected calibration evidence digest
- [ ] Bind selected ECAL configuration digest
- [ ] Bind selected FHIR representation digest
- [ ] Bind coverage targets `[0.50, 0.80, 0.90]`
- [ ] Bind hardware protocol `p08-hardware-stratified-v0.1`
- [ ] Bind multiplicity policy `holm-primary-family-v0.1`
- [ ] Preserve explicit `final_test_access = sealed`
- [ ] Make authorization candidate fail closed on any digest/revision mismatch
- [ ] Require a separate later SpecGrain/PR before final-test access can be opened

#### Qualification and closeout

- [ ] Exact-head Linux/Windows Python 3.11/3.12 CI
- [ ] Affected P08 regression qualification
- [ ] Checksum-pinned Alibaba OpenCodeReview exact-range evidence
- [ ] Secure TypeSafe Jev exact-diff review with complete coverage and zero blocking findings
- [ ] Guarded normal implementation merge with expected-head SHA
- [ ] Post-main qualification
- [ ] Separate SG-000020 canonical closeout

Final-test access remains **sealed** throughout SG-000020.

### Freeze before final-test access

- [x] Freeze benchmark versions and immutable split manifests
- [x] Freeze DAL paper candidate, clinical control, and Laya identities
- [x] Freeze calibration method, calibration split, and coverage targets
- [x] Freeze hardware/timing protocol and comparability rules
- [x] Freeze multiplicity policy
- [x] Complete required dataset license/redistribution audit
- [x] Complete required train/development/calibration/test leakage audit
- [ ] Execute calibration under frozen method without model retraining
- [ ] Freeze ECAL component selection
- [ ] Freeze FHIR representation selection
- [ ] Bind final selected system/protocol/checkpoint digests into an authorization candidate
- [ ] Qualify and merge a separate digest-bound final-test opening artifact

Final-test access remains **sealed** until the last item above is satisfied.

### Primary paper evaluation — after separate final-test authorization only

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
