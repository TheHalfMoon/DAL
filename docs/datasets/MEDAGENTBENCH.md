# MedAgentBench qualification boundary

GAX P08 treats MedAgentBench as two separate reproducibility surfaces: a frozen public corpus and an external official runtime/scorer.

## Frozen public corpus

The repository surface is frozen to:

- repository: `stanfordmlgroup/MedAgentBench`
- commit: `99260117137b09f04837a8c18d18a1107efa55ae`
- repository license: MIT
- task corpus: `data/medagentbench/test_data_v2.json`
- task Git blob: `7f568f041f9d22e11b5bf31b80efd2219aaaf14f`
- task SHA-256: `b6e89b2ef82f1bef27c5778a644a8a66c7b25738bbd6a48d03ab3e5182df6ca8`
- task byte count: `118276`
- function catalog: `data/medagentbench/funcs_v1.json`
- function Git blob: `9b15acc0ccf402ede8964261c371d6a00889b436`
- function SHA-256: `c977266db5eca75182c0d12cac1962b33ae6b5a54b9029ceb104e1a93b4c38c1`
- function byte count: `12571`

The real-source probe records:

- 300 tasks;
- 300 unique task IDs and 0 duplicate task IDs;
- 10 task families with 30 tasks each;
- 9 function entries and 8 unique function names;
- 0 exact duplicate model-visible task strings;
- 2610 normalized five-token-shingle Jaccard >= 0.80 near-duplicate pairs;
- 0 of those 2610 pairs cross task-family boundaries.

The high within-family near-duplicate count is disclosed as benchmark template-family redundancy. It is not hidden or reclassified as independence. Because the entire corpus is one sealed final-test role, this finding is not a cross-role leakage result.

The metadata-only evidence is bound by:

- membership SHA-256: `85831df8b2b3e4f610186776b6e1e247a6cefd2113341675e7efc6318385a01d`
- role-manifest SHA-256: `daf963c8f1c13e974a4608a1cf222505f0013ed81a15616e129a106cb9a6dcb1`
- leakage-audit SHA-256: `b1fa338c510b4787e33cb40c525d5e2ca00154eae97b86c93c5a419abf143356`
- near-duplicate-pair digest: `f4e880f456b374c62d00a20c7e5e414544eb2ef57b4a5636057f68ca20f56718`

The dedicated qualification workflow downloads the exact frozen repository files, verifies Git blob identity, regenerates all metadata evidence, checks that the persisted leakage-audit digest matches the qualification report, and compares generated evidence against committed registry evidence.

## Final-test-only role

The complete published task corpus is **final-test-only** in GAX under role revision `gax-medagentbench-final-test-only-v0.1`.

It is not a source for:

- training;
- calibration;
- prompt selection;
- threshold selection;
- model selection;
- ECAL component selection;
- FHIR representation selection.

Committed GAX qualification artifacts contain no raw task text, patient names, dates of birth, MRNs, gold answers, or FHIR payloads.

Public benchmark release also means foundation-model pretraining contamination cannot be ruled out. GAX records this as `unresolved-public-benchmark` rather than claiming contamination is absent.

## External official runtime/scorer

The upstream README separately instructs users to run:

```text
docker pull jyxsu6/medagentbench:latest
```

and to download `refsol.py` from a Stanford Medicine Box link. The frozen evaluator imports that external module for official scoring.

These are not treated as automatically covered by the repository MIT license. The frozen instructions name a mutable Docker `latest` tag, not an immutable digest. A 2026-09-28 public Docker Hub observation exposed manifest digest `sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966`; this is retained only as a time-stamped observation and is **not** represented as the immutable image used to produce the frozen benchmark.

The official runtime remains blocked because:

- Docker image content and patient-environment rights are not established by the repository MIT license;
- the Stanford Medicine Box `refsol.py` share does not establish an immutable file revision in the frozen repository;
- an explicit `refsol.py` license is not proven;
- the frozen evaluator directly depends on `refsol.py` for official scoring.

Therefore GAX records the compound state:

```text
public corpus       = qualified
official runtime    = blocked
aggregate inventory = blocked
final-test access   = sealed
```

`required_for_authorization` remains true. A future governed paper-protocol decision may only change how the blocked official runtime is handled **before** final-test opening and without consulting MedAgentBench results. Until then, official MedAgentBench success-rate claims are forbidden.

## Safety and non-claims

SG-000016 is provenance and evaluation-governance work. It does not establish clinical correctness, patient safety, autonomous EHR operation, FHIR conformance certification, model/agent superiority, or SOTA performance. P08 final-test access remains sealed throughout this grain.
