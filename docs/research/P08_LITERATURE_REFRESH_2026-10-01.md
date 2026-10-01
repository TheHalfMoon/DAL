# P08 Literature Refresh — 2026-10-01 (SG-000023 pre-claim-freeze)

This is the SG-000023 related-work refresh required before the final novelty and claim freeze. It supplements `P08_LITERATURE_REFRESH_2026-09-26.md` and `LITERATURE_MAP.md`.

The machine-readable record is `registry/p08_sg000023_related_work_refresh.json`. It holds the search date, every query and its result IDs, the included works with verified identifiers and URLs, notable exclusions with reasons, and the novelty-disposition ledger. Evidence packet `EP-SG23-LIT-001` binds that record, and claim `SG23-C011` in the SG-000023 claim ledger is generated from it.

## Method

- Search date: 2026-10-01.
- Sources: arXiv API, PubMed via NCBI E-utilities, Crossref REST API, ACL Anthology, PMLR proceedings, and GitHub REST API. All are free; no paid service (for example Scite) was used.
- Every returned record was screened by title, and abstracts were reviewed for records that passed title screening.
- Bibliographic fields for arXiv entries come from the arXiv API responses. DOIs were checked against Crossref, and repository licenses against the GitHub API.
- This is not a systematic review. Semantic Scholar and OpenAlex were not queried, and no forward or backward citation chasing was done. Screening was done by a single AI implementation agent without human double screening, so a human pre-submission check is still required.
- The refresh changes no model, threshold, calibration, benchmark, denominator, or result.

## Findings by area

### Medical abstention and selective prediction

MedQAbstain (ACL 2026), MedAbstain (arXiv 2601.12471), AbstentionBench (arXiv 2506.09038), MedBayes-Lite (arXiv 2511.16625), and a peer-reviewed npj Digital Medicine review (doi:10.1038/s41746-026-02882-1) already establish medical abstention benchmarks, protocols, and decision-theoretic framing. MedBayes-Lite describes itself as a clinical "uncertainty governance layer", and AgentAbstain and Agentic Abstention extend when-not-to-act evaluation to agents.

Implication: DAL makes no novelty claim for abstention, an abstain option, or an assurance/governance layer. The DAL native risk@80 difference stays descriptive, and the frozen-policy unsafe-commit pathology is reported as a negative result consistent with documented overconfidence under missing information (arXiv 2608.09080).

### FHIR and healthcare agent evaluation

FHIR-AgentBench (PMLR 297), MedAgentBench (NEJM AI), HealthAgentBench (arXiv 2606.31179), FHIRPath-QA, CliniCARE-Bench, and concurrent FHIR-AgentBench method work (arXiv 2605.14126) define the field. A serialization study (arXiv 2604.21076) supports DAL's rule that serialization-only effects cannot carry FHIR capability claims.

Implication: DAL makes no FHIR capability claim. The final FHIR result remains `interface-blocked-preexecution`.

### Typed-decision / System-One models

"Jev in Medicine" (arXiv 2609.34024) already evaluates a typed-decision model on PubMedQA and other medical benchmarks, covering calibration and selective prediction. An early evidence audit (arXiv 2609.32160) finds that the typed readout shows no independent accuracy advantage over label-probability readouts, and proposes a 14-item checklist. A pre-registered typed-decision study (arXiv 2609.34227) also exists.

Implication: DAL is not the first typed-decision evaluation in medicine, nor the first pre-registered typed-decision evaluation. The DAL PubMedQA tie (estimate 0.0, 95% interval [0.0, 0.0]) agrees with the audit's finding. The manuscript should be checked against that checklist before submission.

### Evaluation governance and provenance

MedSci Skills (arXiv 2606.09500) already uses deterministic halt-on-failure integrity gates and content-hash manifests to verify manuscript numbers. CANONIC and LEDGERMIND describe evidence-ledger governance and provenance-constrained claims.

Implication: DAL's claim-ledger and evidence-packet binding is engineering practice of this study, not a new method.

### Evidence grounding, calibration, and counterfactuals

Med-PRM, MedTrust-RAG, Med-V1, EHRNote-ChatQA, a clinical calibration benchmark (arXiv 2506.10769), a Journal of Medical Systems calibration study (doi:10.1007/s10916-026-02430-0), and MamaBench (arXiv 2607.14385) cover evidence verification, calibration measurement, and real-data counterfactual robustness.

Implication: DAL has no qualified real-data evidence-intervention or counterfactual result and makes no grounding, calibration-superiority, or robustness claim.

## Novelty disposition

All "first"-style novelty claims are removed. The native-abstention comparison is narrowed to descriptive reporting. The only retained contribution statement describes this study: one frozen-protocol evaluation in which every exported claim is bound to source-hashed evidence packets, and null, negative, blocked, and calibration-pathology outcomes are reported. It explicitly disclaims methodological novelty for abstention, typed decisions, pre-registration, and provenance verification. The exact wording and scope are in the machine-readable record.

## Next refresh

Repeat immediately before arXiv submission and again before peer-reviewed submission. Narrow or remove any further claim when concurrent work closes a gap.
