# MedAgentBench qualification boundary

GAX P08 treats MedAgentBench as two separate reproducibility surfaces.

## Frozen public corpus

The repository surface is frozen to:

- repository: `stanfordmlgroup/MedAgentBench`
- commit: `99260117137b09f04837a8c18d18a1107efa55ae`
- repository license: MIT
- task corpus: `data/medagentbench/test_data_v2.json`
- task Git blob: `7f568f041f9d22e11b5bf31b80efd2219aaaf14f`
- task byte count: `118276`
- function catalog: `data/medagentbench/funcs_v1.json`
- function Git blob: `9b15acc0ccf402ede8964261c371d6a00889b436`
- function byte count: `12571`

The dedicated qualification workflow downloads these exact files from the frozen commit and verifies Git blob identity before producing metadata-only evidence.

The complete published task corpus is **final-test-only** in GAX. It is not a development, calibration, prompt-selection, threshold-selection, model-selection, ECAL-selection, or FHIR-representation-selection source.

Committed GAX qualification artifacts must not contain raw task text, patient names, dates of birth, MRNs, gold answers, or FHIR payloads.

## External official runtime/scorer

The upstream README separately instructs users to run:

```text
docker pull jyxsu6/medagentbench:latest
```

and to download `refsol.py` from a Stanford Medicine Box link. The frozen evaluator imports that external module for official scoring.

These are not treated as automatically covered by the repository MIT license. At SG-000016 activation:

- the Docker reference is a mutable `latest` tag in the frozen instructions;
- Docker image content/data rights are not proven by the repository license;
- the Box `refsol.py` link does not provide an immutable revision in the frozen repository;
- an explicit `refsol.py` license is not proven by the frozen repository;
- official success-rate scoring depends on `refsol.py`.

Therefore official-runtime/scorer status is fail-closed as **blocked** unless independent immutable identity and terms evidence is established.

A qualified public corpus does not imply a qualified official runtime. GAX may use the corpus only according to a separately frozen paper evaluation protocol, and must not report official MedAgentBench success rate while the runtime/scorer gate is blocked.

## Leakage and contamination

The qualification records exact visible-task duplication and a preregistered normalized five-token-shingle Jaccard audit at threshold `0.80`. Findings are stored as counts and digests only.

Because MedAgentBench is publicly released, possible foundation-model pretraining contamination is recorded as `unresolved-public-benchmark`; qualification does not claim that public models have never seen the benchmark.

## Safety and non-claims

SG-000016 is provenance and evaluation-governance work. It does not establish clinical correctness, patient safety, autonomous EHR operation, FHIR conformance certification, model/agent superiority, or SOTA performance. P08 final-test access remains sealed throughout this grain.
