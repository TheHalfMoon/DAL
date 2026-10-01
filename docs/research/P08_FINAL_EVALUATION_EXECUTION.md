# DAL P08 Final Evaluation Execution — SG-000022

Status: **implementation / pre-execution**

No SG-000022 final-test row had been accessed when this implementation contract was written. The canonical SG-000021 authorization permits final-test inference only for SG-000022 and remains bound by digest `626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`.

## Pre-execution statistical amendment

The earlier P08 protocol froze 95% confidence intervals, paired bootstrap inference, the Holm primary family, the target coverage grid, and the no-silent-denominator-change rule. It did not serialize three exact real-run implementation parameters: the bootstrap replicate count, the bootstrap seed, or the per-benchmark primary metric names.

Before any final-test source access, SG-000022 freezes:

- CI level: `0.95`;
- paired bootstrap replicates: `10000`;
- paired bootstrap seed: `1729`;
- PubMedQA PQA-L primary metric: action accuracy;
- DAL-native abstention primary metric: risk at 80% coverage;
- FHIR-AgentBench primary metric: action accuracy;
- primary comparison: DAL paper candidate versus the matched clinical-encoder control;
- Laya remains a required reported baseline where its already-frozen adapter is executable.

The numeric bootstrap choice uses the documented P08 statistics CLI example rather than the synthetic freeze fixture. No outcome information was available when this choice was made.

## FHIR interface preflight

A pre-execution interface review found that the required frozen systems do not expose a compatible FHIR action interface:

- the DAL paper candidate and matched clinical control have exactly three frozen PubMedQA logits: `maybe`, `no`, and `yes`;
- the frozen Laya adapter is a PubMedQA `yes`/`no`/`maybe` choice adapter;
- FHIR-AgentBench exposes variable read-only candidate sets for resource selection, read/search routing, sufficiency/stopping, and support verification.

Creating a new output-affecting FHIR adapter after authorization would violate the no-post-authorization interface-change boundary. SG-000022 therefore freezes FHIR primary execution as `interface-blocked-preexecution`: requested denominator `173`, completed `0`, interface failures `173` for each required system. The benchmark remains visible in the primary family and limitations; it is not silently removed or replaced.

This is an interface limitation, not evidence that the benchmark or systems perform poorly.

## Execution boundary

Final-test execution is exposed only through `.github/workflows/p08-sg000022-final-evaluation.yml`, which is `workflow_dispatch` only. The workflow:

1. requires canonical `main`;
2. requires the exact SG-000021 authorization digest as an explicit input;
3. validates authorization and the SG-000022 contract before downloading the PubMedQA final-test source;
4. uses only pinned zero-founder-cost CPU runtimes and frozen model/source revisions;
5. writes raw PubMedQA, native-abstention, Laya, and blocked-FHIR artifacts before deriving metrics;
6. preserves requested/completed/timeout/OOM/transport/interface/parse accounting;
7. derives metrics only from the persisted raw artifacts;
8. emits no clinical-safety, regulatory-readiness, SOTA, or automatic superiority claim.

The implementation PR itself must never dispatch the final evaluation. It must pass cross-platform GAXBench CI, checksum-pinned Alibaba OpenCodeReview, and secure TypeSafe Jev first, merge normally with an expected-head guard, and pass post-main verification. Only then may the canonical `main` workflow be dispatched.

## Native abstention semantics

The evidence-withheld condition remains a constructed evidence-availability intervention. `abstain` is not added to the action candidates.

For selective-risk evaluation:

- evidence-present rows use ordinary PubMedQA action correctness and `gold_sufficient=true`;
- evidence-withheld rows use `gold_sufficient=false`; ordinary action correctness is not reported for those rows;
- a committed evidence-withheld row counts as a selective-decision error/unsafe commit;
- DAL selection uses its frozen calibrated information-sufficiency score;
- the clinical control uses its frozen calibrated action distribution with max-probability as the confidence-only selector;
- risk@50, risk@80, risk@90, AURC, unsafe-commit rate, over-abstain rate, actual policy coverage, and evidence-present action accuracy remain visible.

## Multiplicity and claims

`holm-primary-family-v0.1` remains the multiplicity policy. The frozen repository does not define a primary p-value construction, so SG-000022 does not manufacture one after authorization. It emits paired bootstrap confidence intervals and no significance/superiority claim. A future p-value analysis may not be promoted to a primary claim unless separately preregistered without using SG-000022 outcomes.

Null, negative, blocked, unavailable, timeout, OOM, transport, interface, and parse outcomes remain publication-eligible evidence.
