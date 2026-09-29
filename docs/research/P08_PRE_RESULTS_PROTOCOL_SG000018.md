# DAL P08 Pre-Results Protocol Freeze — SG-000018

Status: **prospectively frozen on the SG-000018 implementation branch; not canonical until merge and post-main qualification**

This protocol resolves paper-scope dependencies that were blocked for rights/runtime reasons without using final-test performance to decide what remains required. P08 final-test access remains sealed, so the choices below are made before any final-test model result exists.

Historical `GAX` / `gax-*` identifiers are retained where they are frozen compatibility/provenance identifiers. The current program identity is **DAL — Decision Assurance Layer**.

## Required benchmark suite

The proposed authorization-critical benchmark set is:

1. `pubmedqa-pqal` — closed biomedical action selection and calibration;
2. `gax-native-abstention-pqal` — compatibility ID for DAL-native evidence-availability sufficiency/selective-decision evaluation;
3. `fhir-agentbench` — FHIR retrieval/routing/action-selection evaluation under its already-qualified patient-disjoint policy.

`medqabstain` remains visible as a blocked external benchmark but is no longer authorization-critical under this prospective protocol. Its frozen derived dataset card provides no license grant, so keeping it required would make the paper depend on an unresolved rights boundary.

The MedAgentBench public corpus remains qualified and may be reported as secondary analysis. Its official Docker/refsol runtime remains blocked. That runtime is no longer authorization-critical under this proposal because its immutable external identity/terms are not reproducible under the zero-founder-cost requirement.

These decisions are prospective and must not be changed in response to final-test performance. They become canonical only after SG-000018 implementation and post-main qualification succeed.

## Required comparison systems

The proposed primary matched comparison requires:

- the final DAL paper candidate (legacy inventory ID `gax-paper-candidate`);
- the frozen BioClinical ModernBERT clinical-encoder control;
- Laya as the required open typed-decision baseline.

CLM, decider, the restricted-logit control, Qwen structured-output LLM, and Jev remain valuable secondary comparisons where reproducible zero-founder-cost execution is available. They are not authorization-critical under this proposal. This classification is based on reproducibility/compute/access constraints and the need for a minimal matched primary comparison, never on observed final-test performance.

The tiny deterministic `gax-bilinear-v0` remains an engineering/control model and is not eligible to become the headline paper model by convenience.

## Native abstention decision boundary

The native benchmark deliberately keeps **information sufficiency separate from the action distribution**:

- evidence-present development/calibration items retain typed action supervision and set `Gold.sufficient=true`;
- evidence-withheld development/calibration items set `Gold.sufficient=false` and `Gold.action=null`;
- `abstain` is never inserted into `BenchmarkItem.actions`;
- sealed final-test variants serialize neither action nor sufficiency supervision.

The evidence-withheld condition is a constructed benchmark intervention. It must be described as evidence-availability insufficiency/selective-decision evaluation, not generic clinical safety or real-world medical insufficiency.

## Calibration and selectivity

Prospectively frozen calibration method revision:

`temperature-scaling-action+platt-sufficiency-v0.1`

- action probabilities: scalar temperature selected on calibration data only;
- information-sufficiency score: Platt/logistic calibration selected on calibration data only;
- no final-test threshold tuning;
- target coverages: 0.50, 0.80, 0.90;
- headline selective reporting includes full risk-coverage curves and risk at the frozen coverage targets;
- insufficient/evidence-withheld cases are evaluated separately from ordinary action correctness.

Calibration split digest:

`11d347a4763475749e9f8e63532f1b26023d9d8c16c077b5005961c314f9c291`

The calibration manifest binds the qualified PubMedQA, native abstention, and FHIR-AgentBench calibration-role identities. It is not a hash of final-test labels.

## Primary comparisons and multiplicity

Prospectively frozen multiplicity revision: `holm-primary-family-v0.1`.

The primary comparison family is DAL versus the matched clinical-encoder control on the preregistered primary metric for each required benchmark family. Family-wise inferential comparisons use Holm adjustment. Additional systems, subgroups, and mechanism interactions are reported as secondary/exploratory unless separately preregistered before final-test authorization.

Confidence intervals use the already-frozen P08 paired bootstrap infrastructure. Null and negative results remain reportable; no benchmark/system may be removed because its result is unfavorable.

## ECAL and FHIR development selection

The existing ECAL candidate list remains fixed:

- evidence;
- hard-negative;
- proper-scoring;
- replay-retention;
- state-action-contrastive.

Keep/reject decisions are made from licensed development/validation evidence only and are frozen before final-test authorization.

The FHIR representation candidate list remains fixed:

- canonical-structured;
- canonical-with-narrative;
- flat-text;
- source-order-json.

Representation selection uses development/validation evidence only and is frozen before final-test authorization.

## Hardware and efficiency

Prospectively frozen hardware protocol revision: `p08-hardware-stratified-v0.1`.

Accuracy/calibration/selectivity comparisons may use reproducible zero-founder-cost hardware appropriate to each system, but latency/throughput/peak-memory claims are only directly compared inside the same hardware/runtime stratum. Every measured run records accelerator/CPU identity, software lock, precision, batch size, candidate count, context length, warm-up policy, timed repetitions, wall time, and peak-memory method.

A model that cannot be run reproducibly at zero founder cost is reported as unavailable/blocked for that comparison rather than silently estimated or replaced after results.

## Review and canonicalization boundary

Before this protocol is canonical, the exact final SG-000018 implementation head must have:

- Linux/Windows Python 3.11/3.12 CI success;
- native-abstention qualification success;
- PubMedQA, FHIR-AgentBench, MedAgentBench, and MedQAbstain regression qualification success;
- registry/tests/governance consistency;
- honestly recorded independent review evidence or an explicit unavailable-tool record;
- an expected-head normal merge followed by post-main qualification;
- a separate SG-000018 canonical closeout.

Jev or Alibaba Open Code Review results must not be claimed unless those tools actually execute against the bound revision. CodeRabbit, Qodo, Cubic, or similar output is not a substitute for the program's qualification evidence.

## Safety boundary

P08 final-test access remains sealed after this branch-level protocol freeze. This document does not authorize final-test inference. It does not establish clinical safety, diagnosis/treatment correctness, superiority, SOTA status, or deployment fitness.
