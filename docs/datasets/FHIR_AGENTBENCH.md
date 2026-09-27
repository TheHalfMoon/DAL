# FHIR-AgentBench P08 Qualification

Status: **SG-000015 active / source probe first / final test sealed**

## Frozen artifact

GAX freezes the public upstream derived artifact at:

```text
repository: glee4810/FHIR-AgentBench
revision: bbb42909a5a7eb907d1cd91f72a560729e7037ea
path: final_dataset/questions_answers_sql_fhir.csv
Git blob SHA-1: b2225370feeaefe962c27c4d90f911584e098ac2
source FHIR identity: R4
repository license: CC BY 4.0
```

GAX does not copy this CSV into the Apache-2.0 repository. The qualification workflow downloads it from the frozen upstream revision, verifies the Git blob identity, and commits only metadata-safe evidence.

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

The frozen repository already publishes the derived CSV required for metadata qualification. GAX therefore uses a public download + local parser path in GitHub Actions. No paid API, paid cloud, or founder-funded compute is required.

## Source probe

The first SG-000015 gate intentionally does not decide dataset qualification before reading the real frozen artifact. It records only:

- SHA-256 and byte count;
- exact CSV headers;
- row and upstream-split counts;
- unique/duplicate question-ID counts;
- column missingness counts;
- unique patient-FHIR-ID counts per split when the field is present;
- aggregate cross-split patient-identity overlap;
- aggregate exact-question overlap;
- aggregate template overlap.

The report must not contain raw questions, SQL, true answers, FHIR IDs, patient identifiers, or patient-level rows.

## Final-test boundary

Upstream test membership remains sealed. SG-000015 does not run models and does not inspect test performance.

Any later calibration role must be created deterministically from non-test membership before model comparison. Ground-truth SQL, answers, and FHIR IDs are supervision-only and may not appear in model-visible state.

## R4 boundary

FHIR-AgentBench source identity remains R4. GAX may render R4 content through its deterministic P07 representation contract, but this is not a semantic R4-to-R5 conversion and is not HL7 conformance certification.

## Qualification decision

After the real source probe, SG-000015 must choose one evidence-supported state:

- `qualified` — reproducible role/provenance/leakage contract is complete;
- `pending` — required evidence remains incomplete but has a defined resolution path;
- `blocked` — rights, provenance, leakage, or access constraints prevent paper-eligible use.

The project must not force a positive qualification result.
