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

## P08 — Full paper evaluation (CLOSED_CANONICAL)

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

### SG-000022 — Authorized primary final evaluation (CLOSED_CANONICAL)

Research contract: Issue #84. Canonical closeout: `421ad093e1b89df69e10c763ec2474853c09d0e3`. Post-closeout GAXBench: `36903592739` SUCCESS.

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

#### Canonical evidence promotion and closeout

- [x] Promote the six exact JSON members as text under `registry/p08_sg000022_final_evaluation/`
- [x] Bind source run, artifact, authorization digest, exact byte lengths, and SHA-256 values in `manifest.json`
- [x] Qualify evidence-promotion head `4ae8b39010a2b55f33258fdbf57ce1abc7a13ff3` with GAXBench `36902369992`, Alibaba OpenCodeReview `36902369988`, and secure TypeSafe Jev `36902370171`
- [x] Merge evidence promotion normally at `4417a0fc294a3d35f76e54958f151884bf8bfe80`
- [x] Verify evidence-promotion main with GAXBench `36902663435` SUCCESS
- [x] Qualify canonical closeout head `b274b97f63caefc7365a1310cc0b032899859153` with GAXBench `36903313627`, Alibaba OpenCodeReview `36903313590`, and secure TypeSafe Jev `36903313312`
- [x] Merge canonical closeout normally at `421ad093e1b89df69e10c763ec2474853c09d0e3`
- [x] Verify post-closeout GAXBench `36903592739` SUCCESS

### SG-000023 — Immutable post-final analysis, claim freeze, and paper evidence packaging (CLOSED_CANONICAL)

Research contract: Issue #91. Canonical dependency: `421ad093e1b89df69e10c763ec2474853c09d0e3`. Dependency post-closeout GAXBench: `36903592739` SUCCESS.

Every SG-000023 deliverable is derivation-only from immutable SG-000022 evidence. No final-test inference was rerun, and no model, threshold, calibration, denominator, metric, bootstrap, ECAL, or FHIR selection changed.

#### Activation contract

- [x] Create SG-000023 research contract Issue #91
- [x] Bind SG-000022 canonical closeout `421ad093e1b89df69e10c763ec2474853c09d0e3`
- [x] Bind SG-000022 post-closeout GAXBench `36903592739`
- [x] Bind canonical final-evidence root `registry/p08_sg000022_final_evaluation/`
- [x] Freeze a permanent no-rerun/no-post-test-tuning/no-reselection boundary
- [x] Require the evidence-availability matrix as the first implementation deliverable
- [x] Freeze availability statuses to `available`, `blocked`, `unavailable`, and `not-applicable`
- [x] Freeze the rule that supported claims require evidence-packet IDs and that null/rejected/blocked/exploratory outcomes remain visible
- [x] Preserve P06 synthetic fixtures as mechanics-only, not medical counterfactual evidence
- [x] Preserve FHIR final action-selection performance as blocked and forbid a replacement adapter
- [x] Preserve Laya affected confidence as uncalibrated
- [x] Forbid new post-hoc primary p-values/significance tests
- [x] Require deterministic qualitative-example selection rules before example inspection
- [x] Require matched canonical hardware/runtime evidence for direct efficiency claims; otherwise mark them blocked/unsupported
- [x] Qualify activation PR #92 exact head `e3e4ad8305815f5ee6a4cbe3baf1d354d0fe4f90` with GAXBench `36904301087`
- [x] Qualify activation exact head with Alibaba OpenCodeReview `36904301186`
- [x] Qualify activation exact head with secure TypeSafe Jev `36904754175`
- [x] Merge activation normally at `7da5e1e2efc17e5fdad42e1d80da25139de74317`
- [x] Verify post-main activation GAXBench `36904770004` SUCCESS

#### First implementation deliverable — evidence-availability matrix

- [x] Create `registry/p08_sg000023_evidence_availability_matrix.json` (PR #94, merge `fd77fbab3ebcf9917469ae189b167874b3e058b9`, post-main `36906737047`)
- [x] Cover every remaining P08 analysis and paper-claim family
- [x] Bind each row to the exact preregistered contract source
- [x] Bind each row to exact canonical evidence files/run IDs/hashes
- [x] Record whether each computation is derivation-only or would require forbidden new inference
- [x] Record `available`, `blocked`, `unavailable`, or `not-applicable`
- [x] Record permitted metrics/artifacts and prohibited interpretations
- [x] Bind evidence-packet IDs or an explicit reason no packet can exist
- [x] Prove no task is completed merely because an evaluator or synthetic fixture exists
- [x] Freeze the derivation and qualitative-selection contract before example inspection (PR #95, merge `d676beccfec001fd75d1b157b43068eb49a5733d`, post-main `36907824212`)

#### Remaining P08 analysis and reporting work

Package: `registry/p08_sg000023_paper_evidence/`, built and checked by `tools/build_sg000023_paper_evidence.py --check`.

- [x] Produce paper-ready main action-selection tables from versioned raw artifacts (`main_results.json`)
- [x] Produce reliability analysis from valid calibrated evidence only; preserve the Laya uncalibrated-confidence limitation (`reliability_source_data.json`, `figure_reliability.svg`)
- [x] Produce risk-coverage curves from canonical native-abstention evidence (`risk_coverage_source_data.json`, `figure_risk_coverage.svg`)
- [x] Report the frozen selected ECAL configuration without implying unmeasured ablation performance (`ecal_selection_table.json`); **no ECAL benefit is established** — selection was checkpoint-compatibility-based and every P04 paper decision is `defer-real-data` (SG23-C013)
- [x] Evidence interventions — recorded **blocked**: canonical P06 evidence is synthetic/mechanics-only (SG23-C007)
- [x] Counterfactual material-sensitivity and irrelevant-edit stability — recorded **blocked**: no qualified immutable real-data evidence (matrix row `counterfactual-robustness`)
- [x] Preserve the FHIR final-evaluation result as interface-blocked; no new adapter (`fhir_block_table.json`, SG23-C006)
- [x] Distribution-shift slices — recorded **unavailable**: no preregistered slice semantics bound to final rows (SG23-C008)
- [x] Produce failure taxonomy and qualitative error analysis under deterministic non-cherry-picked selection rules (`qualitative_examples.json`)
- [x] Latency, throughput, and peak memory — recorded **blocked**: canonical evidence does not satisfy `p08-hardware-stratified-v0.1` matched-stratum requirements (SG23-C009)
- [x] Generate every paper table from versioned canonical artifacts with exact provenance (`EP-SG23-TABLES-001`)
- [x] Generate every paper figure from versioned canonical artifacts with exact provenance (`EP-SG23-FIGURES-001`)
- [x] Report the exact paper/control action identity found in raw final rows: identical action probabilities on 500/500 PubMedQA rows and identical action correctness on 1000/1000 native rows (SG23-C014)

### Reproducibility and claim freeze

- [x] Complete an evidence packet for every paper-table row; the packet registry mechanically equals the matrix declarations (PR #96, merge `a18c1e10a0d9eba16ba8bffc55b29988507772ff`, post-main `36918621970`)
- [x] Map every manuscript/README/release claim to exact evidence or explicit limitation, with public-use class, prohibited wording, and scope (`claim_ledger.json`)
- [x] Refresh related work before final novelty/claim freeze; all "first"-style novelty claims removed (PR #97, merge `5ae1232fd6b66978e13a30a3046e8604bbff68cf`, post-main `36921122600`; `registry/p08_sg000023_related_work_refresh.json`)
- [x] Complete ECAL, figure, and action-identity reporting (PR #98, merge `fabbfdd9045415d49f91d56e4e1ba3cd24ac5c1d`, post-main `36922469753`)
- [x] Freeze P08 final results and claims without post-test tuning; claim-set SHA-256 `ef2e347d9ef4298deb68a422c063aa92e9968ae5d00fb0c511576448eb7a2b9b` (PR #99, merge `01831d44123e4db61a1f73116b6654d404b96fd8`, post-main `36923178122`)
- [x] Canonical SG-000023 and P08 closeout (this closeout PR)

P08 closes with blocked/unavailable rows kept explicit: ECAL ablation benefit, evidence interventions, counterfactual robustness, distribution shift, direct efficiency, and FHIR action-selection performance. Closing P08 does not complete those analyses; it records that the frozen evidence cannot support them.

## P09 — Study 0 (pilot) paper and release package

On 2026-10-02 the founder authorized a scientific restart. The P08 evaluation (SG-000018 to SG-000023) and its SG-000024 package are preserved unchanged as **DAL Pilot Study / Study 0**. They are immutable historical evidence and no longer constrain the architecture of the definitive DAL study (Study 1). The SG-000022 PubMedQA final test has been inspected and can never serve as a blind final evaluation for Study 1.

### SG-000024 — Study 0 manuscript, reproducibility bundle, and release-candidate packaging (CLOSED_CANONICAL)

Research contract: Issue #101. Canonical dependency: `f8e075c7620d32614ad0d6ca163e0f7db56e35da`. Frozen claim-set SHA-256: `ef2e347d9ef4298deb68a422c063aa92e9968ae5d00fb0c511576448eb7a2b9b`.

- [x] Activation PR #102 exact head `307aff9ac865e8ee4dea0f870f668c02b9eb866b` (GAXBench `36924631199`, OCR `36924631206`, Jev `36924628705`); merged `51a39994834d0a0d56cfb35079d5737d4bf88b33`; post-main `36924929802`
- [x] Manuscript-input generator and verified bibliography: PR #103 exact head `584973f0fa6b23b18e5006971b5afbc73288668a` (GAXBench `36925726225`, OCR `36925725824`, Jev `36925725052`); merged `f3a917c27ff647c4f3468186ef8c1633acbfbded`; post-main `36925949948`
- [x] Manuscript, appendix, lint tests, and clean-room compile workflow: PR #104 exact head `82f6b4b33d64cc4aa289ce36c56bd3e0a14320c6` (GAXBench `36927926410`, OCR `36927926437`, Jev `36927924247`, Manuscript `36927926425`); merged `29d1d17176a4e7a4c17c644682adca43f6e94090`; post-main GAXBench `36928142149`, Manuscript `36928142095`
- [x] Release-candidate documents and deterministic arXiv bundle (SHA-256 `94c91de9912f188df6b6e56782b8f9f99c43c59b66eb8a72c29d607787c029a3`, reproduced in three runs, compiles standalone without BibTeX): PR #105 exact head `c6af7122393bc15da0efe42082f62c4b0c8e61a5` (GAXBench `36928966622`, OCR `36928966639`, Jev `36928963962`, Manuscript `36928966643`); merged `cf9212eca4c37be3c9b8af65db703f7b40341c9b`; post-main GAXBench `36931619661`, Manuscript `36931619705`
- [x] Canonical SG-000024 closeout and Study 0 designation (this closeout)

### Study 0 items intentionally not pursued

- Study 0 is not developed further as the definitive paper. Whether to post it on arXiv as a pilot report is a founder decision; the packaged bundle stays available.
- Model release, fine-tuning notebooks, Hugging Face release, and release tag for Study 0 are not pursued.
- The governed DAL naming migration / GAXBench compatibility release moves to the Study 1 program.

## Study 1 — Definitive DAL study

### SG-000025 — Research redesign, pilot diagnosis, and preregistered protocol (CLOSED_CANONICAL)

Research contract: Issue #107. Canonical dependency: `4e6ed79aebffce10d812bf6871888eb028b8af09`.

- [x] Create research contract Issue #107
- [x] Qualify and merge activation; verify post-main - PR #108 merged `d1d2728d3472b0384a40210ff509fa596e297234`; post-main GAXBench and Manuscript SUCCESS
- [x] D1 pilot forensic diagnosis artifact (deterministic, from immutable Study 0 raw predictions) - PR #109 merged `a81a69e878535d3812bde4235798577f83e16651`; post-main GAXBench and Manuscript SUCCESS
- [x] Literature refresh with citation chasing, tool-substitution record, and candidate novelty-gap statement - `registry/study1_literature_refresh_2026-10-02.json`; PR #110 merged `0b6e9dcabc558ee7c8fd61fc39c6a68050bda1c0`; post-main GAXBench `37058978862` and Manuscript `37058978882` SUCCESS; novelty remains unfrozen until the protocol grain closes
- [x] Benchmark dossier (versions, hashes, licenses, Study 0 exposure, contamination risk) - `registry/study1_benchmark_dossier_2026-10-02.json`; PR #111 merged `1c816fafb67c9b6813caecf4051e29ef1adae9dd`; post-main GAXBench `37062757509` and Manuscript `37062757512` SUCCESS; final benchmark selection remains unfrozen
- [x] Zero-cost compute plan with founder-account boundaries - `registry/study1_zero_cost_compute_plan_2026-10-02.json`; PR #112 merged `defff28527260c81d4482925cd43a47f12a21e25`; post-main GAXBench `37063390389` and Manuscript `37063390221` SUCCESS; final benchmark suite and final split remained sealed until this protocol grain
- [x] Preregistered Study 1 protocol with sealed final split - `registry/study1_preregistered_protocol_2026-10-02.json`; PR #113 merged `535efada86f7c5863b6eeda18b76d17a78e36b4e`; post-main GAXBench `37065781852` and Manuscript `37065781811` SUCCESS; final-test access remains `sealed`
- [x] Canonical SG-000025 closeout (this closeout PR; evidence record `registry/study1_sg000025_closeout.json`)

### SG-000026 - D2 baseline qualification and local FHIR compatibility (CLOSED_CANONICAL - MODEL_INDEPENDENT_D2_PROVEN)

Research contract: Issue #115. Canonical dependency: `16682ea9dff2f3ccfb0ed818b352eaaa0ccdc167`. Option A projection recovery gate: Issue #120. Query-trace recovery authorization: Issue #126, founder comment `5970310150`. Stage-order repair authorization: Issue #128, founder comment `5970595978`.

- [x] Create research contract Issue #115
- [x] Founder-authorize Option A blind metadata-only custodian under Issue #120 — comment 5963555775
- [x] Record and merge the governed D2 frontier — PR #121 merge `b46d3de2`; post-main GAXBench `37081145272` and Manuscript `37081145291` SUCCESS
- [x] Exact-head qualify and normally merge the Option A custodian implementation and repair; PRs #122-#123, canonical custodian run `37084890139` SUCCESS
- [x] Qualify and merge SG-000026 activation; verify post-main — PR #116 merge `e4b9e22`
- [x] Prove B0/B1/B2 matched-input base-answer identity and wrapper semantics — PR #117 merge `0cfc2db`
- [x] Implement deterministic denominator and failure accounting for D2 baselines — PR #117 merge `0cfc2db`
- [x] Implement synthetic read-only local FHIR R4 compatibility mechanics and explicit unsupported-semantics handling — PR #118 merge `5ea436e`
- [x] Prove the 40-patient / 173-row sealed-final firewall mechanically in the D2 compatibility surface — PR #118 merge `5ea436e`
- [x] Pin and offline-verify the zero-cost MIMIC-IV Clinical Database Demo on FHIR v2.1.0 runtime identity — PR #119 merge `aa59981`
- [x] Qualify real direct-ID FHIR retrieval on the governed 341 calibration + 1122 validation rows without sealed-test supervision — run `37088504254` SUCCESS; 21,527/21,527 references resolved; zero mismatch/missing/parse failures
- [x] Persist real development direct-ID resource-equivalence evidence and exact provenance (`study1_sg000026_real_direct_id_qualification.json`, execution receipt)
- [x] Founder-authorize the blind development-only query-trace recovery boundary under Issue #126 - comment `5970310150`; no D3 activation or model selection authorized
- [x] Verify from frozen upstream source that direct-request query traces are model/strategy dependent; record governance evidence in `registry/study1_sg000026_query_trace_governance.json` without accessing development question text or final-role content
- [x] Founder-authorize Issue #128 Option A stage-order repair - comment `5970595978`; the observed-query-pattern criterion is preserved and moved to a mandatory post-D3/pre-D4 gate
- [x] Record the preregistered stage-order amendment in `registry/study1_sg000026_stage_order_amendment.json` while leaving the immutable parent protocol unchanged
- [x] Canonical SG-000026 / D2 closeout using model-independent exit criteria only - `registry/study1_sg000026_closeout.json`; closeout qualification is bound by this closeout PR and required post-main verification
- [ ] Post-D3/pre-D4 observed governed query/search-pattern qualification - mandatory after prospective D3 model/agent freeze; SQL `proc_query`, expected resource IDs, static source inspection, and invented traces remain invalid substitutes
- [ ] D4 activation remains blocked until the observed query/search-pattern gate passes

### SG-000027 - D3 architecture candidates (CLOSED_CANONICAL)

Research contract: Issue #132. Canonical dependency: SG-000026 closeout merge `07ad6a3f0af0f5a460cd469e029b26274f1a7416`.

- [x] Create D3 research contract Issue #132
- [x] Record governance-only D3 activation contract in `registry/study1_sg000027_contract.json`
- [x] Canonically qualify and merge SG-000027 activation; PR #133 merge `aba35ac15fd56ed255565327c059a22104012f4e`, post-main verified
- [x] Define a bounded candidate family and retain every rejected/blocked candidate
- [x] Bind candidate model/tokenizer revisions, license, release date, provenance, contamination-risk metadata, and zero-cost compute-path status in the bounded inventory
- [x] Prospectively freeze one trace-producing base-model + FHIR-agent-strategy identity before query-trace qualification - `registry/study1_sg000027_trace_producer_freeze.json`
- [x] Execute the mandatory post-D3/pre-D4 gate; run `37156028113` completed with scientific BLOCKED status
- [x] Record SG-000027 / D3 closeout - `registry/study1_sg000027_closeout.json` (becomes canonical only after this closeout PR qualifies, merges, and passes post-main verification)

- [x] Bound the D3 base-model candidate family and retain excluded candidates with exact revisions, license/gating, release-date contamination proxy, and zero-cost compute evidence - `registry/study1_sg000027_candidate_inventory.json`
- [x] Freeze the D3 FHIR agent strategy prospectively to frozen-upstream `single_turn_request` without using development outcomes
- [x] Execute canonical zero-cost CPU smoke run `37140291946`; Qwen retained `blocked-behavior-changing`, Phi/Smol retained provider-routing blocks, and no model/tokenizer was frozen
- [x] Diagnose raw OpenAI-compatible structured tool transport versus the frozen Qwen parser - canonical run `37142304592` proved `parser-transport-mismatch`
- [x] Canonically qualify the minimal Qwen structured-tool transport compatibility repair; PR #137 merge `26069715534ba693049795fdb5dc6929ab807a7d`, repaired CPU smoke `37143422780` PASS
- [x] Prospectively freeze Qwen3-4B-Instruct-2507 base-model + tokenizer identity using only preregistered non-final, non-query-trace-outcome technical criteria
- [x] Execute the blind development-only query-trace gate; full 1463-row result retained as BLOCKED
- [ ] D4 remains blocked until the observed query/search-pattern gate passes

### Later Study 1 stages (not activated)

- [ ] D4 training/objective experiments
- [ ] D5 calibration/assurance development (including DAL-R controlled revision if development evidence supports it)
- [ ] D6 ablations
- [ ] D7 model selection
- [ ] D8 protocol freeze
- [ ] D9 untouched final evaluation
- [ ] D10 paper evidence, claim ledger, manuscript, Hugging Face and arXiv packages

## P10 — Peer review / external validation

- [ ] Independent reproduction
- [ ] Active venue CFP review
- [ ] Peer-reviewed submission
- [ ] Reviewer response artifacts
- [ ] Journal extension decision

### SG-000028-E1 - Complete canonical negative-evidence persistence

Research contract: Issue #141; source run `37156028113` on `f8f5c1c8ebfbe2e044ad9beae55e56b94f1f449d`.

- [x] Verify all eight shards, aggregate, and successful raw-source cleanup
- [x] Verify all nine artifact ZIP digests and extracted bytes; recompute the aggregate exactly
- [x] Persist complete privacy-safe sufficient statistics, blocker taxonomy, pattern identities, producer/runtime provenance, and final firewall evidence
- [x] Preserve earlier provenance/dependency failures as historical records
- [x] Exact-head qualify persistence: PR #145 merged 48b73aa6ba75b2b1c6e1b11f26e762ca8d010200; all required exact-head and post-main checks passed
- [x] SG-000028-R1 output firewall CLOSED_CANONICAL via PR #146; all 1463 structural rows replay unchanged; required exact-head and post-main checks passed
- [x] Investigate all 106 reason keys across the full 1239-row blocker set; preserve unknown target/runtime causes and distinguish empty-parameter repair candidates from invalid comparison modifiers
- [ ] SG-000028 PASS / closeout remains blocked
- [ ] D4 separate activation remains blocked

### SG-000028-G1 - Complete blocker investigation and program-direction decision gate

- [x] Classify every observed reason key from complete canonical development evidence
- [x] Verify FHIR R4 prefix placement and distinguish standard empty-parameter handling
- [x] Preserve the negative result and keep producer, pass criteria, roles, and final firewall unchanged
- [x] Create decision-only Issue #147 with concrete options and scientific consequences
- [x] SG-000028-G1 investigation CLOSED_CANONICAL via PR #148 merge `ad67bf48138da8aa260844ae92eee74c16e53971`; required exact-head and post-main checks passed; durable qualification in `registry/study1_sg000028_governance_gate_closeout.json`
- [ ] Founder program-direction decision under Issue #147; no replacement experiment is authorized

### SG-000030 / R1 - Canonical recovery system

- [x] Prospective recovery protocol and separate finite R1 implementation qualified
- [x] R1 G1/G2 and closeout reviewed, normally merged, and verified post-main
- [x] Preserve canonical main `ef9102ea3afda800e3fc25d38072b9e18fd3f9af` and manifest `220c676df241d8dc1ac8ccd83e81d54554e7618fc5acf016eaa32ec6302ca2b0`
- [x] Open separate R2 decision gate Issue #158 without inference

### SG-000031 / R2 - Founder-approved bounded recovery

- [x] Record direct founder Option A authorization separately from the agent transcription
- [ ] Fully qualify the separate R2 contract and runner on exact head
- [ ] Verify actual Jev, Alibaba delegation-accounting, and synthetic SDK reports
- [ ] Guarded normal merge and complete post-main qualification before inference
- [ ] Claim and execute exactly one main-only attempt over all 1463 development rows
- [ ] Retain all rows, blockers, transformations, immutable lineage, and interrupted evidence
- [ ] Qualify and canonically persist the separate R2 scientific classification
- [ ] D4 remains inactive pending canonical R2 PASS and separate future founder authorization

### SG-000031-E1 / R2 - Retained failed attempt

- [x] Qualify the separate runner with actual exact-head Jev, Alibaba delegated inspection, synthetic SDK and GAXBench 4/4 evidence
- [x] Normally merge PR #159 and verify post-main CI, manuscript/arXiv and synthetic SDK before dispatch
- [x] Perform exactly one authorized dispatch: run `37320473498`, attempt 1
- [x] Retain admission failure and stop; all eight model workers were skipped, with zero study model calls
- [x] Verify the failure artifact ZIP and report hashes and reproduce the native trailing-slash HTTP 404 read-only
- [x] Retain all 1463 historical development identities as unattempted with the exact population hash
- [ ] Qualify and canonically merge this separate BLOCKED evidence closeout, then verify post-main and record the external receipt
- [ ] New founder decision before any new model-call attempt; the missing permanent tag does not renew authorization
- [ ] D4 remains inactive; scientific PASS, training and final evaluation are not authorized

### SG-000031-A1 / R2 - Founder-authorized admission repair only

- [x] Preserve separate direct founder repair-only authorization and exact failure base
- [x] Normalize native repository metadata URL and fail closed on ambiguous admission URLs
- [x] Share native authenticated receipt validation with a mutation-prohibited preflight
- [x] Add deterministic fixtures for the retained HTTP 404 and corrected lookup, URL boundaries, authentication, read-only transport and live-main guard
- [ ] Persist Graft structural impact and actual test/source hashes
- [ ] Qualify genuine Jev, approved Alibaba, full CI, manuscript/arXiv, unchanged SDK and actual native workflow-token preflight on exact head
- [ ] Normal expected-head merge, intended-tree verification and complete post-main checks
- [ ] Record canonical repair receipt and stop before any model call for a separate founder decision
- [ ] No new R2 attempt, row replay, model call, final access, D4, training, scoring or final evaluation is authorized

### SG-000031-A1 / PR #161 - Founder-authorized CRLF extension

- [x] Retain separate verbatim founder extension; preserve original authorization and failed qualification evidence
- [x] Normalize only CRLF pairs to LF at the local receipt parsing boundary before unchanged validation
- [x] Add LF/CRLF equality and malformed/incomplete/structural/semantic rejection regression fixtures
- [ ] Refresh Graft and actual test/hash evidence, then qualify the revised exact head through every required gate
- [ ] Protected normal merge, post-main verification and external canonical repair receipt
- [ ] Stop before any model call; R2 remains BLOCKED pending a separate future execution decision
