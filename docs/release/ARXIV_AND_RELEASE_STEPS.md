# Founder Steps for arXiv, Hugging Face, and Release

Everything up to these steps is prepared and verified in continuous integration. Each step below needs the founder's own account, identity, or legal decision, so none has been performed.

## 1. Confirm the author list

`paper/main.tex` currently reads "Author list to be confirmed by the project founder before submission". Replace it with the final author list and affiliations. Authorship is the founder's decision.

## 2. Human pre-submission checks

- Read the compiled manuscript end to end.
- Do a human check of the 2026-10-01 related-work refresh. Screening was done by a single automated agent without double screening, citation chasing, or Semantic Scholar/OpenAlex searches.
- Check the manuscript against the 14-item typed-decision evaluation checklist in arXiv:2609.32160.

Any change to a frozen claim or result needs a new governed SpecGrain.

## 3. arXiv submission

1. On canonical `main`, open the latest successful `DAL Manuscript` workflow run and download the `dal-arxiv-source` artifact. It contains `main.tex`, `main.bbl`, and `generated/*.tex`; its SHA-256 is printed in the run log.
2. Sign in to arXiv with the founder's account and start a new submission.
3. Choose a license. This is a legal decision for the founder.
4. Choose categories. `cs.CL` with cross-list `cs.LG` fits the content; confirm against arXiv's category guidance.
5. Upload the tarball, check arXiv's compiled PDF against the workflow PDF, and enter the title and abstract. The abstract should be the manuscript abstract with its macros expanded, copied from the compiled PDF.
6. After the identifier is assigned, record it in `CITATION.cff` through a governed PR.

## 4. Hugging Face (optional)

`docs/release/HUGGINGFACE_CARD_DRAFT.md` is a draft card for the evidence package. Before publishing, the founder must choose the license field (it is `other` / `to-be-confirmed-by-founder`) and create the repository under their own account. Model weights are not part of it.

## 5. Release tag

Create the tag only after the arXiv version exists, so that the tag, the arXiv source, and the repository revision match. Tagging is a founder decision.
