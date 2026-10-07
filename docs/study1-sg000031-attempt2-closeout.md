# SG-000031-E2: Attempt 2 failed before worker inference

The founder-authorized second R2 execution was dispatched exactly once from
canonical main `8fcf29f2e0c1b6cf78661acd2f5e1340a578ac03`, tree
`430da88b2cd85a32b41cac5d6d2951fb8ebfb944`. Run `37653806159`, workflow attempt 1,
consumed authorization SHA-256
`64eeb307da268144cde54af9b143e136e82cbb069b3a12c1909dd0a775dbcb48`.
Admission passed against Issue #158 receipt `6005216567`, created permanent tag
`dal-r2-issue158-attempt2` with claim `14a92834c3e9e28f83dd6cb696d7c3e78bea9c17`,
and retained a full development plan on the forward-only journal branch.

Shard 0 failed at permanent-claim verification before its infrastructure setup.
The benchmark download, FHIR runtime, model download/build/start and first-turn
execution steps were skipped. Shards 1 through 7 were skipped. The aggregate job
succeeded and uploaded all 1463 unattempted rows; the whole workflow failed.
There were zero generation admissions, first-turn generations, physical model
POSTs, duplicate model calls, model retries, tool calls and transformations.
All 341 calibration and 1122 validation rows remain in the denominator.

The retained failure hashes `Attempt-2 claim normal merge/tree mismatch`.
The actual worker log reports checkout depth 1. An isolated local shallow clone
of the unchanged execution main returned no parents from the same Git parent
query, while the full checkout returned the two required normal-merge parents.
This supports a shallow-checkout ancestry failure. The error artifact is hash-only
and has no stack identifying the failing line. The runner is preserved unchanged.
No repair, workflow rerun, redispatch or selective replay is part of this closeout.

Three actual artifact archives and all extracted documents were hash-verified.
The original aggregate is retained byte-for-byte in
`registry/study1_sg000031_attempt2_execution_37653806159.json`; the original failure
is `registry/study1_sg000031_attempt2_claim_failure.json`. The closeout record
binds their hashes, source artifact IDs/digests, exact dispatch, claim, receipt,
population, producer, manifest, immutable Attempt-1 lineage and all job steps.

`registry/study1_sg000031_attempt2_unattempted_rows.json` retains each question
identity, role, input identity and disposition. Combining its four finite columns
with the shared template in `registry/study1_sg000031_attempt2_closeout.json`
reproduces every original aggregate row byte-for-byte under the frozen canonical
JSON serializer. Each of the 1463 reconstructed file hashes was independently
checked against its actual source artifact. The aggregate was also independently
recomputed using the unchanged classifier; every accounting field matches.
The journal contains the original plan and zero row-generation checkpoints.

R2 remains **BLOCKED**: all 1463 rows are unattempted and complete generation
lineage and transformation accounting do not exist. Zero observed behavior-changing
blocker rows means no inference outcome was observed; it does not qualify R2 PASS.
Workflow or aggregate success cannot waive the scientific gate. Failure does not
renew authorization. No Attempt 3 is authorized. A new founder decision is required
before any repair or additional scientific execution.

SG-000028 remains immutable and separate: 1463 rows, 224 PASS, 1239 behavior-changing
blockers, 1623 calls and 248 source-pattern identities. Attempt 1 remains consumed
and immutable. Canonical R1 and all frozen scientific controls remain unchanged.
The final role remains sealed at 40 patients / 173 rows, with zero final materialization
and content access. Founder cost is $0. D4, training, second-turn reasoning,
answer-correctness scoring and final evaluation remain inactive.

This bounded evidence closeout requires genuine TypeSafe Jev exact-diff review
with independently complete coverage, actual Alibaba v1.12.9 artifacts and
inspection, Graft structural verification, full CI and manuscript/arXiv checks,
zero active unresolved review threads, guarded normal merge and post-main
verification. Its canonical receipt is recorded externally after those gates.
