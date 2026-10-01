# DAL Reproducibility Checklist

This checklist covers reproducing the frozen P08 evidence and the manuscript from a clean clone. Items marked done have executable evidence in continuous integration. Independent third-party reproduction is P10 work and is **not** done.

## Environment

- [x] Python 3.11 or 3.12; `python -m pip install -e ".[dev]"`.
- [x] Linux and Windows (GAXBench CI runs both on every change).
- [x] TeX Live with `latexmk`, `pgfplots`, `natbib`, `booktabs`, `microtype`, and `lmodern` for the manuscript (the `DAL Manuscript` workflow installs signature-verified Ubuntu packages).
- [x] Zero founder cost: no paid compute, API, or service is needed for any step below.

## Frozen evidence

- [x] `python tools/build_sg000023_paper_evidence.py --check` refuses to derive anything unless every canonical input matches its pinned byte SHA-256, then reproduces the 14-artifact package exactly.
- [x] The claim freeze (`registry/p08_sg000023_paper_evidence/claim_freeze_manifest.json`) binds the final-evaluation run, artifact, ZIP digest, authorization digest, final manifest and metrics digests, and the claim-set SHA-256.
- [x] The final-evaluation artifacts in `registry/p08_sg000022_final_evaluation/` match the SG-000022 manifest digests.

## Manuscript

- [x] `python tools/build_sg000024_manuscript_inputs.py --check` verifies the package against its provenance index and the frozen claim digest, then reproduces every number, table, claim macro, figure, and bibliography entry.
- [x] `cd paper && latexmk -pdf main.tex` compiles with no undefined references or citations (`DAL Manuscript` workflow).
- [x] `tests/test_p09_sg000024_manuscript.py` enforces generated numbers, frozen claim wording, visible limitations, and resolvable citations.
- [x] The `DAL Manuscript` workflow assembles the arXiv source bundle (`dal-arxiv-source` artifact) with `main.bbl`, because arXiv does not run BibTeX.

## Release documents

- [x] `python tools/build_sg000024_release_docs.py --check` reproduces the README results block, the tool/model card, the Hugging Face card draft, and the release notes from the frozen claim ledger.

## Not done

- [ ] Independent third-party reproduction (P10).
- [ ] Human double screening of the related-work refresh and a human pre-submission literature check.
- [ ] Model-weight release (pending a founder license decision).
- [ ] Fine-tuning notebooks (deferred; they require execution evidence).
- [ ] arXiv submission, Hugging Face publication, and release tag (founder actions; see `ARXIV_AND_RELEASE_STEPS.md`).
