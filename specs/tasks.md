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

Research contract: Issue #69. Canonical dependency: `3ca0dd2aae85a68473849108764a45a538de1019`.

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

Frozen candidate set:

- `evidence`
- `hard-negative`
- `proper-scoring`
- `replay-retention`
- `state-action-contrastive`

Tasks:

- [x] Persist ECAL selection objective before candidate outcome inspection
- [x] Persist deterministic ECAL tie-break rule before candidate outcome inspection
- [x] Evaluate every frozen candidate on authorized development/calibration evidence only
- [x] Preserve every null/negative/failed ECAL outcome
- [x] Freeze selected ECAL configuration
- [x] Bind selected ECAL configuration to immutable digest

#### FHIR representation selection

Frozen candidate set:

- `canonical-structured`
- `canonical-with-narrative`
- `flat-text`
- `source-order-json`

Tasks:

- [x] Persist FHIR selection objective before candidate outcome inspection
- [x] Persist deterministic FHIR tie-break rule before candidate outcome inspection
- [x] Evaluate every frozen representation on authorized development/calibration evidence only
- [x] Preserve parse/interface/failure accounting for every representation
- [x] Preserve every null/negative FHIR result
- [x] Freeze selected FHIR representation
- [x] Bind selected FHIR representation to immutable digest

#### Final-test authorization candidate

- [x] Bind canonical DAL paper-candidate bundle digest `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`
- [x] Bind canonical clinical-encoder bundle digest `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`
- [x] Bind canonical Laya bundle digest `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`
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
- [x] Separate SG-000020 canonical closeout at `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`
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
- [x] Qualify and merge a separate digest-bound final-test opening artifact under SG-000021

### SG-000021 — Final-test authorization qualification (CLOSED_CANONICAL)

Research contract: Issue #80. Canonical closeout: `ef36ae4d050cf2e1bb7ada07f4054b083e886045`.

- [x] Activate a separate research contract and SpecGrain for final-test authorization
- [x] Bind SG-000020 canonical closeout and all promoted semantic/byte digests
- [x] Re-verify required-system bundle and paper-checkpoint identities
- [x] Re-verify immutable final-test split/source manifests and leakage boundaries
- [x] Bind frozen coverage, hardware, multiplicity, failure-accounting, and no-post-test-tuning policies
- [x] Create machine-readable authorization artifact `626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`
- [x] Qualify exact implementation head `c88bbac110169a48ae6ce2288c5228a0d2b9980f` with GAXBench `36866528564`, Alibaba OpenCodeReview `36866528579`, and secure TypeSafe Jev `36866521762`
- [x] Merge authorization normally with expected-head guard at `1daa55d9742050f37fe56d2c84ccf4c8743ef984`
- [x] Verify implementation post-main with GAXBench `36866791467` SUCCESS
- [x] Qualify governance closeout head `6ff33ad96e636418429abf842175919243e66ecd` with GAXBench `36867843947`, Alibaba OpenCodeReview `36867844045`, and secure TypeSafe Jev `36867843711`
- [x] Merge canonical closeout at `ef36ae4d050cf2e1bb7ada07f4054b083e886045`
- [x] Verify post-closeout GAXBench `36868102682` SUCCESS
- [x] Preserve `final_test_inference_executed=false` and `final_test_rows_used=0`

SG-000021 executed no final-test inference. Its canonical authorization artifact is scoped only to SG-000022.

### SG-000022 — Authorized primary final evaluation (PROVEN by this closeout state transition)

Research contract: Issue #84. Canonical dependency: `ef36ae4d050cf2e1bb7ada07f4054b083e886045`.

#### Activation and implementation

- [x] Create SG-000022 research contract Issue #84
- [x] Bind SG-000021 canonical closeout and post-closeout run `36868102682`
- [x] Bind authorization digest `626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`
- [x] Freeze activation as governance-only with zero final-test rows
- [x] Require a separate implementation PR after canonical activation
- [x] Qualify activation exact head `638eec3132ca3ac87a9f36db8f195f1310a396f0` with GAXBench `36868975243`, Alibaba OpenCodeReview `36868975233`, and secure TypeSafe Jev `36868975703`
- [x] Merge activation normally at `c7ea6fbc81a1dd7526a6c453d12c585db6841cb3` with expected-head guard
- [x] Verify post-main activation with GAXBench `36869200519` before final-test inference
- [x] Implement fail-closed authorization verification at the execution entry point
- [x] Qualify implementation head `563883489fdb3df5ae337267cc2510d31551e53e` with GAXBench `36885982630`, Alibaba OpenCodeReview `36885982580`, and secure TypeSafe Jev `36886188326`
- [x] Merge implementation normally at `42e09ca1b1431340b26fe57ae318ff1b1b662fc3` with expected-head guard
- [x] Verify implementation post-main with GAXBench `36886206716` before final-test source access
- [x] Prospectively qualify the operational-only one-shot transport amendment before final-test access because connected tooling could not invoke `workflow_dispatch`
- [x] Qualify transport head `4cfee6e2b23637c117549c149efdd335456557c6` with GAXBench `36886639294`, Alibaba OpenCodeReview `36886639411`, and secure TypeSafe Jev `36886639719`
- [x] Merge one-shot transport normally at `f1955d5beeb2444f1d604626629036196a1dedd5`; no scientific binding changed

#### Canonical primary final evaluation

- [x] Pass one-shot canonical boundary and authorization preflight before final-test source download
- [x] Persist immutable raw predictions/results before derived analysis
- [x] Preserve exact requested/completed/timeout/OOM/transport/interface/parse accounting
- [x] Execute `pubmedqa-pqal` 500-row authorized final-test surface
- [x] Execute `gax-native-abstention-pqal` 1000-variant authorized final-test surface
- [x] Preserve `fhir-agentbench` as the preregistered `interface-blocked-preexecution` outcome: denominator 173, zero gold rows loaded, zero completed, 173 interface failures per required system, and no post-authorization adapter
- [x] Complete one-shot final-evaluation run `36886952302` on canonical main with zero founder cost
- [x] Preserve source Actions artifact `11176566473` and ZIP SHA-256 `8dcd894be6ae184aaf5311417d268a5500b89d0d78d14ee7a79305fbb3071136`
- [x] Compute main PubMedQA action-selection metrics
- [x] Compute PubMedQA NLL, multiclass Brier, and ECE without claiming Laya affected confidence as calibrated
- [x] Compute native-abstention AURC and risk@50/80/90
- [x] Compute frozen target-policy coverage, unsafe-commit, and over-abstain outcomes and preserve unfavorable DAL target 0.8/0.9 unsafe-commit rate `1.0`
- [x] Compute paired-bootstrap confidence intervals and declared primary comparisons with 10000 replicates and seed 1729
- [x] Enforce the frozen Holm multiplicity boundary without fabricating p-values because no primary p-value construction was preregistered
- [x] Preserve all null, negative, timeout, OOM, transport, parse, interface-failure, blocked, and calibration-pathology outcomes
- [x] Preserve no significance, superiority, clinical-safety, regulatory-readiness, or SOTA claim from SG-000022

#### Canonical evidence promotion

- [x] Promote the six exact JSON members as text under `registry/p08_sg000022_final_evaluation/`
- [x] Bind source run, artifact, authorization digest, exact byte lengths, and SHA-256 values in `manifest.json`
- [x] Qualify evidence-promotion head `4ae8b39010a2b55f33258fdbf57ce1abc7a13ff3` with GAXBench `36902369992`, Alibaba OpenCodeReview `36902369988`, and secure TypeSafe Jev `36902370171`
- [x] Merge evidence promotion normally at `4417a0fc294a3d35f76e54958f151884bf8bfe80`
- [x] Verify evidence-promotion main with GAXBench `36902663435` SUCCESS
- [x] Start a separate governance-only canonical closeout boundary with no final-test rerun or tuning

### SG-000023 — Remaining P08 immutable post-final analysis and claim freeze (NOT YET ACTIVATED)

The following tasks remain open because SG-000022 did **not** execute or qualify them. They must not be marked complete by inference from the primary final-evaluation run:

- [ ] Create SG-000023 research contract and SpecGrain after SG-000022 canonical closeout and post-closeout verification
- [ ] Determine which remaining analyses are valid derivations from immutable canonical evidence and which must be recorded unavailable/blocked rather than rerun
- [ ] Produce paper-ready main action-selection tables from versioned raw artifacts
- [ ] Produce reliability plots/analysis from valid calibrated evidence only; preserve the Laya uncalibrated-confidence limitation
- [ ] Produce risk-coverage curves from canonical native-abstention evidence
- [ ] Evaluate/report the frozen selected ECAL configuration and declared ablations only where already-authorized immutable evidence supports the analysis, without reselection
- [ ] Evaluate/report evidence interventions without post-test tuning only where immutable evidence supports them; otherwise record the result unavailable/blocked
- [ ] Evaluate/report counterfactual material-sensitivity and irrelevant-edit stability without post-test tuning only where immutable evidence supports them; otherwise record the result unavailable/blocked
- [ ] Preserve the FHIR final-evaluation result as interface-blocked; do not create a new adapter or claim FHIR action-selection performance
- [ ] Produce valid preregistered distribution-shift slices only where canonical source data and pre-result contracts support them
- [ ] Produce failure taxonomy and qualitative error analysis without silent exclusion or cherry-picking
- [ ] Measure/report latency, throughput, and peak memory only if the frozen hardware protocol can still be satisfied without rerunning the completed final-test experiment; otherwise mark efficiency claims unsupported
- [ ] Generate every paper table from versioned canonical artifacts with exact provenance
- [ ] Generate every paper figure from versioned canonical artifacts with exact provenance

### Reproducibility and claim freeze

- [ ] Complete evidence packet for every paper-table row
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
