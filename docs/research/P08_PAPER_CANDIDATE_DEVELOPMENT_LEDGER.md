# P08 Paper Candidate Development Ledger

Status: **development-only / pre-results**

SG-000019 remains `ACTIVE`. P08 final-test access remains `sealed`.

## Purpose

This ledger preserves development-selection results that are allowed to inform
paper-candidate architecture and training choices under Issue #63. Weak, null, and
negative development evidence is retained rather than filtered from the research record.

The frozen development-selection surface contains 90 rows and is reused only under the
bounded architecture-search sequence recorded here. D03 is the final architecture revision
allowed to use this selection surface. There is no D04 architecture tuning on these rows.

## Experiment D01 — typed diagonal evidence model v0.1

Exact implementation head: `a926c0695da185f58a059f2d65788ce692f4c9df`

GitHub Actions run: `36688015220`

Uploaded artifact digest:
`sha256:adb54d5973c07461088cf2b731f025aed7c9b4d41475e379c16ba12531a443b4`

Frozen backbone/model revision:
`thomas-sounack/BioClinical-ModernBERT-base@5e17e2f25260b6993e0fb60485f94678ff29779a`

Frozen development manifest:
`9e096564891b517440ae3e75a2261de5a0b97cbaa1605417f382a446c5169e6c`

Training-contract SHA-256:
`a96861e17c5f2300500d07245c7caae126bfa29db8ef420e7de1ce42c07e53e3`

The run completed both systems for all preregistered seeds `[0, 1, 2]` on CPU.
It used 360 train rows and 90 development-selection rows only. Calibration rows used:
`0`. Final-test rows used: `0`.

### Observed development-selection results

| System | Seed | Selected epoch | Selection metric | Action NLL | Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| DAL typed diagonal v0.1 | 0 | 80 | 0.9358626 | 0.9358410 | 50/90 (55.56%) |
| DAL typed diagonal v0.1 | 1 | 80 | 0.9358662 | 0.9358448 | 50/90 (55.56%) |
| DAL typed diagonal v0.1 | 2 | 80 | 0.9358715 | 0.9358501 | 50/90 (55.56%) |
| Matched clinical encoder | 0 | 2 | 0.9374377 | 0.9374377 | 50/90 (55.56%) |
| Matched clinical encoder | 1 | 2 | 0.9379826 | 0.9379826 | 50/90 (55.56%) |
| Matched clinical encoder | 2 | 2 | 0.9355481 | 0.9355481 | 50/90 (55.56%) |

The DAL seed-0 sufficiency Brier component at its selected checkpoint was
`0.0000432531`. This shows that the evidence-presence sufficiency task is learnable,
but it does **not** establish an action-decision advantage.

### Decision

`dal-typed-evidence-diag-v0.1` is **rejected as the headline paper-candidate
architecture**. The matched development result provides no action-accuracy improvement,
and its best action NLL is slightly worse than the best matched clinical-control seed.

No calibration result and no final-test result informed this decision.

## Experiment D02 — nested typed evidence residual v0.2

Exact implementation head: `426d6075db7193bfffe6742163a8adf506ec93f4`

GitHub Actions run: `36689541322`

Uploaded artifact digest:
`sha256:1fd2b1202470a11730d7782317406fc694a1c42af93e92259bf95d4f6a464e81`

Training-contract SHA-256:
`ba46fae8dbb05ff0c7930d39bbd665e7a85e9fa45d816894aa147ed266179b93`

D02 nested the matched clinical linear action head inside the DAL path and added only
three scalar DAL-specific parameters: one typed evidence-residual coefficient, one
sufficiency scale, and one sufficiency bias. Total fitted capacity was `3H+6` versus
`3H+3` for the matched control.

The run again completed both systems for all preregistered seeds `[0, 1, 2]` on CPU.
It used the same frozen 360/90 development split. Calibration rows used: `0`.
Final-test rows used: `0`.

### Observed development-selection results

| System | Seed | Selected epoch | Selection metric | Action NLL | Accuracy | Sufficiency Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DAL nested residual v0.2 | 0 | 36 | 0.9991197 | 0.9823022 | 47/90 (52.22%) | 0.0336350 |
| DAL nested residual v0.2 | 1 | 36 | 1.0020249 | 0.9852074 | 47/90 (52.22%) | 0.0336350 |
| DAL nested residual v0.2 | 2 | 36 | 1.0006883 | 0.9838708 | 46/90 (51.11%) | 0.0336350 |
| Matched clinical encoder | 0 | 2 | 0.9351184 | 0.9351184 | 50/90 (55.56%) | — |
| Matched clinical encoder | 1 | 2 | 0.9395543 | 0.9395543 | 50/90 (55.56%) | — |
| Matched clinical encoder | 2 | 2 | 0.9379920 | 0.9379920 | 50/90 (55.56%) | — |

### Decision

`dal-typed-evidence-residual-v0.2` is **rejected as the headline paper-candidate
architecture**. Unlike D01, D02 materially degraded both action NLL and action accuracy
relative to the matched control. Its sufficiency signal remained learnable, but that does
not justify changing the action distribution.

This negative result is retained as part of the paper-development evidence. No calibration
result and no final-test result informed this decision.

## Experiment D03 — final shadow assurance critic v0.3 (prospective freeze)

D03 is the **final architecture-search revision** permitted to use the frozen 90-row
development-selection surface. After D03 executes, no D04 architecture tuning, optimizer
revision, seed revision, or acceptance-threshold revision may be selected from these rows.
A weak or null D03 result must be reported rather than followed by another adaptive search.

### Architecture

D03 treats DAL as an assurance layer rather than a replacement action model:

1. train and select the matched clinical control independently for each seed;
2. clone the exact selected same-seed clinical action head into DAL and freeze it;
3. keep DAL action probabilities exactly identical to the same-seed clinical control;
4. train a shadow typed evidence critic whose logits are the frozen control logits plus
   a scalar-weighted typed evidence residual and three class biases;
5. train a separate information-sufficiency head using evidence-delta norm;
6. expose critic disagreement and sufficiency as assurance signals without modifying the
   base action distribution.

The paper candidate therefore contains the `3H+3` fitted clinical action head plus six
DAL assurance scalars: one critic residual scale, three critic class biases, one
sufficiency scale, and one sufficiency bias. Total fitted capacity is `3H+9`; only the six
assurance scalars are trainable during the D03 assurance stage.

### Frozen selection and acceptance contract

- seeds remain exactly `[0, 1, 2]`;
- the control epoch is selected by minimum development action NLL, lower epoch on ties;
- the control seed is selected by minimum development action NLL, lower seed on ties;
- D03 must use the same selected seed as the control;
- assurance epoch 0 is included and its critic is initialized exactly to the control logits;
- later assurance epochs are eligible only if critic NLL does not exceed the same-seed
  selected control NLL by more than `1e-9`;
- among eligible epochs, select minimum
  `critic NLL + 0.5 × sufficiency Brier`, lower epoch on ties;
- paper action logits/probabilities must be exactly equal to the same-seed control output;
- selected-seed sufficiency Brier must be `<= 0.25`;
- all three seeds, failures, checkpoints, predictions, and histories remain reportable;
- calibration rows used: `0`;
- final-test rows used: `0`;
- P08 final-test access remains `sealed`.

These rules are frozen before D03 execution. Passing them only qualifies D03 as the
final development paper candidate; it does not establish clinical superiority, safety,
regulatory readiness, or final-test benefit.
