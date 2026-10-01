# DAL Paper Workspace

Manuscript: `main.tex` — *A Frozen-Protocol Evaluation of a Decision Assurance Layer for Clinical Typed Decisions*.

## Rules

- Every result value is a `\dalnum{...}` macro and every claim sentence is a `\dalclaim{...}` or `\dallimitation{...}` macro. All are generated from the frozen SG-000023 evidence package; never type a result by hand.
- `\dalclaim` exists only for affirmative frozen claims and `\dallimitation` only for limitation statements, so a limitation can never be cited as a positive claim.
- Every citation key must exist in `generated/references.bib`, which is generated from the verified record `registry/p09_sg000024_bibliography.json`.
- Changing a frozen claim or result requires a new governed SpecGrain.

`tests/test_p09_sg000024_manuscript.py` enforces these rules.

## Build

```bash
python tools/build_sg000023_paper_evidence.py --check     # frozen evidence package
python tools/build_sg000024_manuscript_inputs.py           # regenerate paper/generated/
python tools/build_sg000024_manuscript_inputs.py --check   # verify committed inputs
cd paper && latexmk -pdf main.tex
```

The `DAL Manuscript` workflow repeats these steps in a clean Ubuntu runner using signature-verified TeX Live packages and uploads `main.pdf` as an artifact.

## Not yet done

arXiv submission, the author list, and the release tag are founder decisions and have not been made.
