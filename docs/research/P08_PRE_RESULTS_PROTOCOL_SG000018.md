# P08 Pre-Results Protocol Freeze — SG-000018

Status: **frozen before final-test model inference**

This protocol resolves paper-scope dependencies that were blocked for rights/runtime reasons without using final-test performance to decide what remains required.

## Required benchmark suite

The authorization-critical benchmark set is:

1. `pubmedqa-pqal` — closed biomedical action selection and calibration;
2. `gax-native-abstention-pqal` — evidence-availability sufficiency/selective decision;
3. `fhir-agentbench` — FHIR retrieval/routing/action-selection evaluation under its already-qualified patient-disjoint policy.

`medqabstain` remains visible as a blocked external benchmark but is no longer authorization-critical. Its derived dataset card provides no license grant, so keeping it required would make the paper depend on an unresolved rights boundary.

The MedAgentBench public corpus remains qualified and may be reported as secondary analysis. Its official Docker/refsol runtime remains blocked. That runtime is no longer authorization-critical because its immutable external identity/terms are not reproducible under the zero-founder-cost requirement.

These decisions are frozen before any P08 final-test model inference.

## Required comparison systems

The primary matched comparison requires:

- the final GAX paper candidate;
- the frozen BioClinical ModernBERT clinical-encoder control;
- Laya as the required open typed-decision baseline.

CLM, decider, the restricted-logit control, Qwen structured-output LLM, and Jev remain valuable secondary comparisons where reproducible zero-founder-cost execution is available. They are not authorization-critical. This classification is based on reproducibility/compute/access constraints and the need for a minimal matched primary comparison, never on observed final-test performance.

The tiny deterministic `gax-bilinear-v0` remains an engineering/control model and is not eligible to become the headline paper model by convenience.

## Calibration and selectivity

Frozen calibration method revision:

`temperature-scaling-action+platt-sufficiency-v0.1`

- action probabilities: scalar temperature selected on calibration data only;
- information-sufficiency score: Platt/logistic calibration selected on calibration data only;
- no final-test threshold tuning;
- target coverages: 0.50, 0.80, 0.90;
- headline selective reporting includes full risk-coverage curves and risk at the frozen coverage targets;
- insufficient/evidence-withheld cases are evaluated separately from ordinary action correctness.

The calibration-manifest digest binds the qualified PubMedQA, GAX-native abstention, and FHIR-AgentBench calibration-role manifests. It is not a hash of final-test labels.

## Primary comparisons and multiplicity

Frozen multiplicity revision: `holm-primary-family-v0.1`.

The primary comparison family is GAX versus the matched clinical-encoder control on the preregistered primary metric for each required benchmark family. Family-wise inferential comparisons use Holm adjustment. Additional systems, subgroups, and mechanism interactions are reported as secondary/exploratory unless separately preregistered before final-test authorization.

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

Frozen hardware protocol revision: `p08-hardware-stratified-v0.1`.

Accuracy/calibration/selectivity comparisons may use reproducible zero-founder-cost hardware appropriate to each system, but latency/throughput/peak-memory claims are only directly compared inside the same hardware/runtime stratum. Every measured run records accelerator/CPU identity, software lock, precision, batch size, candidate count, context length, warm-up policy, timed repetitions, wall time, and peak-memory method.

A model that cannot be run reproducibly at zero founder cost is reported as unavailable/blocked for that comparison rather than silently estimated or replaced after results.

## Safety boundary

P08 final-test access remains sealed after this protocol freeze. This document does not authorize final-test inference. It does not establish clinical safety, superiority, SOTA status, or deployment fitness.
