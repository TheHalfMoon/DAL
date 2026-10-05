# SG-000031-E1: sole R2 attempt failed before admission

The separate R2 contract and runner were fully qualified, normally merged in
PR #159 at `73e98360863aaa1cd039ffaa5cef2e4311dcfafa`, and verified post-main.
The exact pre/post workflow, artifact and report identities are retained in
`registry/study1_sg000031_attempt1_closeout.json`. The engineering receipt is
Issue #158 comment `5995901646`. Engineering qualification did not establish
scientific PASS.

The sole authorized dispatch was run `37320473498`, attempt 1. Admission failed
with HTTP 404 before the permanent attempt tag or row ledger was created. The
failure artifact was successfully retained. All eight model workers, population
planning, and aggregation were skipped. There were zero model calls, zero
generations, zero transformations and zero founder cost. No retry, rerun,
redispatch, or new model-call attempt was performed.

The native HTTP repository metadata lookup constructs
`https://api.github.com/repos/TheHalfMoon/DAL/` for `api("")`. A read-only public
GET reproduced HTTP 404 with the exact retained error hash; the same URL without
the trailing slash returned 200. The local qualification verifier used the GitHub
CLI, which accepted this repository path, so it did not reproduce the native HTTP
failure. This closeout records that engineering defect and preserves the executed
runner unchanged. The error record hashes the exception text; it does not retain
a stack identifying the failing line. The source order, native reproduction and
matching error hash support the diagnosis.

The absence of a permanent tag does not release or renew the authorization.
The failed dispatch remains the sole retained attempt. A new founder decision is
required before any new model-call attempt, including after an engineering repair.

All 1,463 exposed-development identities remain in the denominator: 341 calibration
and 1,122 validation rows. The finite records in
`registry/study1_sg000031_attempt1_unattempted_rows.json` retain each original
question hash, role and `not-attempted` disposition. Their population hash matches
the frozen historical identity. They were reconstructed read-only from all eight
original development artifacts after verifying both archive and row-file hashes.
This is denominator retention, not a completed R2 admission plan. No benchmark CSV
was downloaded in this attempt or closeout. Unavailable R2 input, request, response,
pattern and call-disposition identities are explicitly unavailable, not invented.
No model-output semantics or per-row correctness result can be claimed.

R2 is **BLOCKED** because admission failed, all rows are unattempted, and complete
generation lineage and transformation accounting do not exist. The successfully
qualified runner and retained upload do not waive these scientific blockers.
This evidence closeout itself requires exact-head review, CI and manuscript
qualification, guarded normal merge and post-main verification; the external
canonical receipt records completion of those gates.

The original SG-000028 result remains immutable and separate: 1,463 rows, 224 PASS,
1,239 behavior-changing blockers, 1,623 observed calls and 248 source patterns.
Canonical R1 manifest, implementation, protocol, producer and all 26 protected
control files remain unchanged. The final role remains sealed at 40 patients and
173 rows, with zero materialization and zero content access. D4, training,
second-turn reasoning, answer-correctness scoring and final evaluation remain
inactive. This closeout authorizes no future execution.
