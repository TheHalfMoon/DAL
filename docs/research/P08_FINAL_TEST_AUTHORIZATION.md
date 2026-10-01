# P08 Final-Test Authorization — SG-000021

Status: **authorization qualification only; no final-test inference in this grain**

Research contract: Issue #80.

Canonical dependency: SG-000020 closeout `ebe981db8b2554a2b52037b8d3cdfc48ef42ba78`.

SG-000021 converts the fully frozen P08 pre-test evidence chain into one digest-bound permission artifact for the next governed final-evaluation grain. It does not produce paper results and it does not inspect final-test predictions, labels, errors, slices, metrics, tables, or figures.

## Authorization scope

The canonical authorization artifact is:

`registry/p08_final_test_authorization_sg000021.json`

Its authorization digest is:

`626aa097085649ebe6e70faf613f343b9ae7a69c337b76aa4b08ad6b7c0352de`

The artifact has exactly one scope:

`SG-000022 final evaluation`

It records `final_test_access = authorized` because it is the permission token consumed by SG-000022. At the same time it records:

- `final_test_inference_executed = false`;
- `final_test_rows_used = 0`;
- `no_post_test_tuning = true`;
- architecture reopening forbidden;
- calibration refit forbidden;
- ECAL reselection forbidden;
- FHIR representation reselection forbidden.

Therefore authorization is not evaluation. SG-000021 itself must never execute the final-test payload.

## Required systems

Authorization independently rebuilds the canonical semantic qualification digests for:

- DAL paper candidate: `0463662f4cff190150979f000e35562965635f818444ef6e195939457f8bb57b`;
- matched clinical-encoder control: `b7ee4e62c170b8cfa7aa1b65a7d15b2174ba858f4ffc5626021a21b2417e4388`;
- Laya: `b3147eabdb6e66f1622559879581b2b7341df218e587a76e66a4f1d638de4534`.

The DAL paper checkpoint remains:

`351513742474f71e0758854f15bd02ec1b7097c23a1ca17d05c7e95482e4168b`

No model, checkpoint, seed, adapter, prompt/interface family, or comparison family may be changed after authorization in response to final-test outcomes.

## Authorization-critical datasets

Only the prospectively frozen required set from SG-000018 is authorization-critical:

1. `pubmedqa-pqal` — 500 sealed final-test rows;
2. `gax-native-abstention-pqal` — 1000 sealed derived final-test variants;
3. `fhir-agentbench` — 173 patient-disjoint sealed final-test rows.

SG-000021 re-verifies each required source/data revision, split or role manifest digest, leakage-audit digest, qualified license status, and sealed-label boundary from canonical registry evidence.

MedAgentBench and MedQAbstain remain visible as blocked/secondary dependencies under the prospectively frozen SG-000018 policy. They are not silently removed and they are not authorization-critical.

## SG-000020 evidence bindings

The authorization rebuild re-validates the promoted SG-000020 evidence:

- calibration manifest: `89a1657b09e6d9cca6107bc92433baaf563e994fb26c177fe39689cfaf2c0230`;
- calibration evidence semantic digest: `025d92c2d704dfa3889e267be8fac17037d034b5760e635886c536d198c8c8dc`;
- ECAL selection semantic digest: `3bfb069bfdd3ee50890f97c3e4744024af14cb9c9a62211cca008eb4c5ef9bb8`;
- FHIR selection semantic digest: `79ddfd4336b5b8a8376ff9761d40ae46fe890eef9962bc6205e8622533b85b9a`;
- selected FHIR representation semantic digest: `10665e1fec0be7ec6d2bf6e3710f54b26ded79a16dc48d032a15c8862112963b`;
- SG-000020 authorization-candidate semantic digest: `3f4000cb5616578332a85d00aeda18e120c2b959d59e32375696cd53486b5484`.

The SG-000020 candidate must remain `sealed` and non-executable while SG-000021 is built. The candidate is evidence used to construct the separate SG-000021 authorization; it is not itself permission to run final-test inference.

## Frozen protocol

Authorization fixes:

- target coverages: `0.50`, `0.80`, `0.90`;
- hardware protocol: `p08-hardware-stratified-v0.1`;
- multiplicity policy: `holm-primary-family-v0.1`;
- explicit failure accounting for requested, completed, timeout, OOM, transport, interface, and parse outcomes;
- no silent denominator changes;
- no post-test tuning.

Null, negative, blocked, timeout, OOM, and parse/interface failures remain reportable. Wrong in-schema answers count as wrong.

## Qualification

`scripts/qualify_p08_final_test_authorization.py` rebuilds the artifact from canonical registry evidence and requires byte-independent semantic equality with the committed authorization artifact. Any source, split, leakage, system, checkpoint, calibration, ECAL, FHIR, policy, or authorization-digest mismatch fails closed.

Before SG-000021 can become canonical, its exact implementation head must pass:

- Linux/Windows Python 3.11/3.12 GAXBench CI;
- checksum-pinned Alibaba OpenCodeReview exact-range evidence;
- secure TypeSafe Jev exact-diff review with complete coverage and zero blocking findings;
- a normal expected-head merge;
- post-main authorization qualification;
- a separate SG-000021 closeout.

Only after that closeout may SG-000022 consume the authorization artifact and access final-test rows.

## Safety and cost boundary

This is research evaluation governance. It does not authorize autonomous diagnosis, treatment, prescribing, triage, emergency execution, EHR writes, clinical-safety claims, regulatory-readiness claims, or deployment claims.

Founder-paid cloud compute, paid APIs, paid SaaS, and paid reviewers remain prohibited.
