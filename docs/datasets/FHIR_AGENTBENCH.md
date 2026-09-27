# FHIR-AgentBench P08 Qualification

Status: **SG-000015 active / dataset-qualified evidence complete / final test sealed**

## Frozen artifact

GAX freezes the public upstream derived artifact at:

```text
repository: glee4810/FHIR-AgentBench
revision: bbb42909a5a7eb907d1cd91f72a560729e7037ea
path: final_dataset/questions_answers_sql_fhir.csv
Git blob SHA-1: b2225370feeaefe962c27c4d90f911584e098ac2
SHA-256: e2045692fef7f5f4f77496935160f5fc727e162d213e94feed61401948e512a0
source FHIR identity: R4
repository license: CC BY 4.0
```

GAX does not copy this CSV into the Apache-2.0 repository. The qualification workflow downloads it from the frozen upstream revision, verifies both Git blob identity and the frozen SHA-256, and commits only metadata-safe evidence.

## Upstream provenance

FHIR-AgentBench's `scripts/setup_data.sh` downloads the MIMIC-IV demo and performs an unpinned clone of `glee4810/ehrsql-2024`.

EHRSQL-2024 is CC BY 4.0. The latest EHRSQL commit that existed before the frozen FHIR-AgentBench revision was:

```text
1886034a8846dede2e8513a2ee16149c65a46fcf
```

That temporal fact is **not** evidence that the frozen FHIR-AgentBench CSV was generated from that exact commit. The upstream setup did not pin the clone revision, so GAX preserves the generation-revision uncertainty.

The MIMIC-IV Clinical Database Demo is open-access under ODbL 1.0. Database-derived material remains subject to the applicable upstream terms. GAX does not infer that the FHIR-AgentBench repository license erases EHRSQL or MIMIC source obligations.

## Zero-cost path

The upstream README documents a Google Cloud Healthcare FHIR-store workflow. GAX does not make GCP part of the qualification requirement.

The frozen repository already publishes the derived CSV required for metadata qualification. GAX therefore uses a public download plus local parser path in GitHub Actions. No paid API, paid cloud, or founder-funded compute is required.

## Real-source probe

The frozen CSV contains:

```text
rows: 2931
upstream train: 2098
upstream valid: 424
upstream test: 409
unique question IDs: 2931
duplicate question IDs: 0
unique patients in train: 94
unique patients in valid: 91
unique patients in test: 90
cross-upstream-split patient identities: 94
cross-upstream-split exact questions: 0
cross-upstream-split templates: 45
```

The upstream split is therefore not patient-disjoint. GAX does not silently treat it as leakage-safe.

The source probe contains only aggregate metadata, digests, counts, and schema information. It serializes no raw question, SQL, true answer, FHIR ID, patient identifier, or patient-level row.

## GAX role policy v0.2

Role revision:

```text
gax-fhir-agentbench-patient-disjoint-v0.2
```

The policy is frozen before any model comparison and does not use labels or answers for assignment.

1. Normalize each `patient_fhir_id` and hash it with SHA-256.
2. Among patients appearing in upstream `test`, sort patient digests and assign the first 40 patients to the GAX sealed-test role.
3. Remove those 40 patients from non-test role eligibility.
4. Sort the remaining 54 patient digests; assign the first 14 to calibration and the remaining 40 to validation.
5. Test-role patients contribute only upstream `test` rows.
6. Calibration/validation patients contribute only upstream `train` or `valid` rows.
7. Rows that cross that boundary are quarantined rather than reassigned.

Observed governed roles:

```text
calibration patients: 14
validation patients: 40
test patients: 40
calibration rows: 341
validation rows: 1122
sealed-test rows: 173
quarantined rows: 1295
  upstream-test rows for non-test-role patients: 236
  non-test rows for test-role patients: 1059
```

The quarantine itself is reproducible: every frozen source row is represented in the membership digest as either calibration, validation, test, or excluded with a deterministic exclusion reason.

Membership digest:

```text
b90e774067d0a0e4251e32584b3aeea9629a01df9201fc550988e70d17dbda15
```

Full role-manifest digest:

```text
7065cede39bdfea3db33d025687210f30f26683a38063f7150a807cd89f5e76c
```

## Leakage audit

Under the governed v0.2 roles:

```text
cross-role patient identity overlap: 0
cross-role exact-question overlap: 0
cross-role near-duplicate question pairs >= 0.80 Jaccard: 0
cross-role template overlap: 50
non-test roles containing upstream-test rows: false
test role containing upstream non-test rows: false
```

Template reuse is reported as a benchmark-native structural property, not silently conflated with exact or near-duplicate content leakage.

The near-duplicate audit uses lowercase Unicode word tokens, five-token shingles, and a preregistered Jaccard threshold of `0.80`.

Leakage-audit digest:

```text
1e45851f334cf5ab0522ac96766080566cb7609462d6917d625814a5612c6490
```

Public-benchmark/pretraining contamination remains unresolved. Dataset qualification does not imply that a pretrained model has never seen FHIR-AgentBench, EHRSQL, or related public material.

## Final-test boundary

Final-test access remains **SEALED**.

SG-000015 performs no model inference, opens no test performance result, and selects no model, prompt, threshold, ECAL component, or FHIR representation from test output.

The public upstream artifact contains supervision fields, but the qualification logic does not use test supervision to choose patient roles. GAX calibration and validation roles contain no upstream-test rows, and GAX sealed-test rows contain no upstream non-test rows.

Ground-truth SQL, answers, and true FHIR IDs remain supervision-only and may not appear in model-visible state.

## R4 boundary

FHIR-AgentBench source identity remains R4. GAX may render R4 content through its deterministic P07 representation contract, but this is not a semantic R4-to-R5 conversion and is not HL7 conformance certification.

## Qualification result

The frozen dataset path is **qualified as a P08 dataset artifact**, subject to the recorded source/license/provenance caveats and the sealed-test boundary.

This qualification does **not** authorize P08 final-test execution. The overall P08 inventory remains blocked by other required datasets, systems, and protocol freezes.

Qualification establishes only that this frozen source has a reproducible zero-founder-cost acquisition path, a deterministic patient-disjoint role policy, metadata-only provenance, and explicit leakage controls. It does not establish clinical correctness, patient safety, FHIR conformance certification, model superiority, agent superiority, or SOTA performance.
