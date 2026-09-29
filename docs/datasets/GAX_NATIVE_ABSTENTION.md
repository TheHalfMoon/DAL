# DAL Native Abstention / PubMedQA PQA-L

Compatibility dataset ID: `gax-native-abstention-pqal`

Status: **SG-000018 pre-results qualification; canonical only after implementation merge, post-main qualification, and closeout**

This benchmark is a deterministic paired transformation of the already-qualified PubMedQA PQA-L source frozen by SG-000014. It exists to replace a blocked paper-required abstention dependency without weakening the scientific question after observing model results. The legacy `gax-*` dataset identifier is retained in this grain as a compatibility/provenance identifier rather than rewritten mid-evidence-chain.

## What it measures

The benchmark measures **evidence-availability insufficiency** for a closed biomedical decision task. Each source item yields two variants:

- `evidence-present`: original question, allowed `yes` / `no` / `maybe` actions, and the supplied PubMedQA abstract sections;
- `evidence-withheld`: the same question and the same allowed actions, but the benchmark evidence is intentionally removed.

For development and calibration roles, the evidence-present variant has `sufficient=true` and retains the source action target. The evidence-withheld variant has `sufficient=false` and **no gold action target**. This prevents the task from teaching the model that abstention is an ordinary answer option.

`abstain` is never inserted into the candidate action list. It remains a separate decision-policy output alongside `information_sufficiency`.

## Final-test protection

The inherited PubMedQA roles remain 450 validation, 50 calibration, and 500 sealed test source items. The paired benchmark therefore contains 900 validation, 100 calibration, and 1,000 sealed test variants.

While P08 remains sealed:

- final-test variants serialize no action gold;
- final-test variants serialize no sufficiency gold;
- no threshold, prompt, checkpoint, ECAL component, or FHIR representation may be selected from the final-test role;
- no model inference is performed by this qualification grain.

The final-test pair role is nevertheless deterministic from the frozen source membership: every source item has exactly one evidence-present and one evidence-withheld variant.

## Leakage boundary

The source split and cross-role leakage audit are inherited from canonical PubMedQA qualification. The transformation preserves source identity and split, so it cannot move an item across roles. The two variants from one source are intentionally paired and share question/action content; that within-source relationship is part of the benchmark design and is not represented as independent data.

Public-backbone pretraining contamination remains unresolved and must be disclosed.

## What this does not prove

Evidence withholding is an intentionally constructed benchmark intervention. A low sufficiency score or correct abstention on this task does **not** prove that a model is clinically safe, that a real patient record is globally insufficient, or that the model should autonomously diagnose, treat, prescribe, or triage.

The supported claim scope is narrower: whether a typed decision system can distinguish a decision state with the benchmark's supplied evidence from the same state after that evidence is deliberately withheld, under a frozen selective-decision protocol.
