# DAL SG-000031 — prospective R2 Attempt-3 engineering readiness

**Status:** readiness-only design and read-only qualification. **NOT execution authorization.**

Founder decision: [Issue #166](https://github.com/TheHalfMoon/DAL/issues/166#issuecomment-6050120310). This engineering decision allows preparation and qualification but **not** scientific dispatch. The Attempt-3 authorization SHA-256 is deliberately \`null\`, and neither the Attempt-3 controller nor the Attempt-3 worker exists. Their reserved paths and Git ref/ledger namespaces are inert identifiers only.

## Immutable evidence boundary

Historical Attempt 1 remains infrastructure-failed (run \`37320473498\`), and Attempt 2 remains infrastructure-failed (run \`37653806159\`, consumed authorization \`64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48\`). Both generated zero new scientific model results. Historical SG-000028 remains 224 PASS / 1239 blockers on 1463 exposed-development rows, without relabeling.

Canonical preparation base: \`6b345396d16f4e827d6339fdd850ec86c6a9a399\`, tree \`233f0303d230458debc1e812045766e25c8fa323\`. Freeze identity and population are machine-verified against the immutable Attempt-2 contract and against 43 protected files. The 1463 development rows comprise 341 calibration and 1122 validation. Final 40 patients / 173 rows remain **SEALED**.

## Readiness grain and fail-closed checks

- The versioned, unarmed contract is \`registry/study1_sg000031_attempt3_readiness_contract.json\`. No previous execution authorization may be copied into the null Attempt-3 slot.
- The read-only verifier \`tools/qualify_sg000031_attempt3_readiness.py\` proves actual completed and failed historical run identities and immutable Attempt-2 tag, and rejects new/duplicate dispatches or a preexisting Attempt-3 claim tag.
- The real Git repository must be **non-shallow**. Attempt-2's canonical merge tree and ordered parents are verified from actual Git objects before reporting that the ancestry defect has been addressed.
- Candidate and post-main verification must bind to the exact local checkout and current GitHub HEAD. Candidate verification also checks live PR and base consistency.
- \`tests/test_study1_sg000031_attempt3_readiness.py\` covers replay, consumed-authorization reuse, unsupported scientific event entrypoints, altered R1/producer/population, wrong history/parents/trees, prohibited GitHub mutation, sealed final access, D4, training, and nonzero cost.
- CI is limited to \`pull_request\` and \`push\` on the named readiness files. There is **no workflow_dispatch** in the readiness workflow; GitHub \`GITHUB_TOKEN\` has read-only permissions, and native request audit rejects mutation.
- Exact-head GAXBench, manuscript/arXiv, synthetic SDK, genuine Jev, Alibaba OpenCodeReview, Graft structural validation, zero active review threads, normal expected-head merge and post-main checks are additional mandatory governance gates. Workflow success alone is not scientific PASS.

## What is not done and must never be inferred

This grain does **not** build a runnable Attempt-3 worker or controller and is **not** an executable admission contract. It does not attest that the frozen producer can generate a row, that all infrastructure is permanently available, or that prospective R1 recovery succeeds. Attempt-2's old scientific claim is not renewed. R2 is **BLOCKED**. No model POST, new scientific dispatch, permanent claim, ledger write, final data access, fine-tuning, training, D4 activation, or payment is authorized.

**Next decision:** after canonical qualification, the founder may separately authorize a *bounded execution-admission implementation grain* and then, in another independent decision, **exactly one** Attempt-3 scientific execution. Do not conflate either with this readiness-only agreement. Retain failures and prevent automatic retries or arbitrary reruns. Founder cost remains $0.
