# P08 Paper Candidate Development Ledger

Status: **development-only / pre-results**

SG-000019 remains `ACTIVE`. P08 final-test access remains `sealed`.

## Purpose

This ledger preserves development-selection results that are allowed to inform paper-candidate architecture and training choices under Issue #63. It is intentionally retained when a candidate is weak or null; negative development evidence must not disappear from the research record.

## Experiment D01 — typed diagonal evidence model v0.1

Exact implementation head: `a926c0695da185f58a059f2d65788ce692f4c9df`

GitHub Actions run: `36688015220`

Uploaded artifact digest: `sha256:adb54d5973c07461088cf2b731f025aed7c9b4d41475e379c16ba12531a443b4`

Frozen backbone/model revision: `thomas-sounack/BioClinical-ModernBERT-base@5e17e2f25260b6993e0fb60485f94678ff29779a`

Frozen development manifest: `9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c`

Training-contract SHA-256: `a96861e17c5f2300500d07245c7caae126bfa29db8ef420e7de1ce42c07e53e3`

The run completed both systems for all preregistered seeds `[0, 1, 2]` on CPU. It used 360 train rows and 90 development-selection rows only. Calibration rows used: `0`. Final-test rows used: `0`.

### Observed development-selection results

| System | Seed | Selected epoch | Selection metric | Action NLL | Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| DAL typed diagonal v0.1 | 0 | 80 | 0.9358626 | 0.9358410 | 50/90 (55.56%) |
| DAL typed diagonal v0.1 | 1 | 80 | 0.9358662 | 0.9358448 | 50/90 (55.56%) |
| DAL typed diagonal v0.1 | 2 | 80 | 0.9358715 | 0.9358501 | 50/90 (55.56%) |
| Matched clinical encoder | 0 | 2 | 0.9374377 | 0.9374377 | 50/90 (55.56%) |
| Matched clinical encoder | 1 | 2 | 0.9379826 | 0.9379826 | 50/90 (55.56%) |
| Matched clinical encoder | 2 | 2 | 0.9355481 | 0.9355481 | 50/90 (55.56%) |

The DAL seed-0 sufficiency Brier component at its selected checkpoint was `0.0000432531`. This demonstrates that the evidence-presence sufficiency task is learnable, but it does **not** establish an action-decision advantage.

### Decision

`dal-typed-evidence-diag-v0.1` is **rejected as the headline paper-candidate architecture**. The matched development result provides no action-accuracy improvement and its best action NLL is slightly worse than the best matched clinical-control seed.

This is a development-only architecture decision explicitly permitted by Issue #63. No calibration result and no final-test result informed it.

## Experiment D02 — prospectively revised nested residual architecture

Before executing D02, freeze a revised architecture that contains the matched clinical linear action head as a nested submodel and adds only three scalar DAL-specific parameters:

1. a scalar typed evidence-residual coefficient over frozen evidence-delta/action embeddings;
2. a scalar sufficiency scale over evidence-delta norm;
3. a scalar sufficiency bias.

The resulting trainable capacity is `3H+6` versus `3H+3` for the matched clinical control. The difference is exactly three scalar evidence/sufficiency parameters, while the frozen backbone, tokenizer, input policy, train rows, selection rows, optimizer family, seeds, and final-test seal remain matched.

D02 must be frozen in the machine-readable training contract before execution. Its null or negative result must also remain reportable.
