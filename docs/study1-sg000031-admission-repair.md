# SG-000031-A1: admission repair only

The founder authorized a bounded engineering repair from canonical failure main
`3ebf58ef10a42db6ee31d96451ea80fe98432b4c`. The separate verbatim authorization
and repair contract are in `registry/study1_sg000031_admission_repair_*.json`.
No new model call, R2 attempt or row replay is authorized. R2 remains BLOCKED.

The retained attempt `37320473498`, attempt 1, failed during repository metadata
lookup: the native helper built `https://api.github.com/repos/TheHalfMoon/DAL/`,
which returned HTTP 404. CLI-based checks accepted that path and missed the native
failure. The deterministic regression fixture returns 404 for the original native
path and verifies that its exception hash matches the retained failure. The same
native request/opener path now constructs the repository root without the trailing
slash, uses the unchanged bearer authentication headers and succeeds on the fixture.

The URL constructor gives the empty repository suffix and the exact absolute root
with or without one trailing slash a single canonical identity. It rejects foreign
repositories/authorities, userinfo, explicit ports, non-HTTPS schemes, protocol-relative
paths, dot segments, repeated/trailing child slashes, percent escapes, backslashes,
fragments, whitespace/control/non-ASCII characters and ambiguous queries before
credentials or HTTP transport. Existing job, artifact, ref and checkpoint paths
remain supported. Returned repository metadata and receipt issue URLs must match
the exact repository identity. Redirects reject unsafe schemes, userinfo and scope
drift; cross-host artifact downloads still strip bearer authentication.

The real admission entry and native preflight share `qualify_canonical_receipt`,
`repository_url`, `authenticated_request` and `native_http`. Existing receipt,
normal-merge lineage, intended tree, actual workflow jobs, full genuine Jev coverage,
Alibaba artifacts/rules, SDK reports and review-thread checks remain in that shared
path. Real admission still requires the live canonical main, main-only dispatch,
first run attempt and the permanent single-attempt claim. No execution gate is waived.

The new native preflight workflow uses the same `github.token` in `GH_TOKEN`, job
permission set, headers, request construction, opener and response parsing as real
admission. It performs actual authenticated native HTTP reads of the immutable
historical runner receipt and its qualification artifacts. This historical receipt
validation deliberately observes current main separately and cannot admit execution
on the repair checkout. A context guard rejects every REST mutation before transport;
GraphQL permits only the fixed read-only review-thread query. The tool never invokes
`admit`, `plan`, a model worker, the benchmark custodian or the model SDK. Reports retain
canonical request paths, status codes, payload hashes and source hashes without bearer
values, signed artifact-download URLs or scientific content. The regression suite
proves the real entry uses the shared validator and retains its mandatory live-main guard.

This preflight replaces the CLI-only admission qualification for this repair; CLI
tools remain useful for retrieving review evidence and managing the normal PR merge.
The existing synthetic SDK workflow remains unchanged and independently qualifies the
same frozen producer transport using HTTP fixtures, with no model inference.

Graft structural analysis is performed without a model pass. Its graph identifies
the helper's impact on admission, artifact reads, claim verification, checkpoint
writing and aggregation. Deterministic tests, returned Alibaba rules plus inspection,
genuine Jev exact-diff coverage, GAXBench 4/4, manuscript/standalone arXiv, actual SDK
and native preflight artifacts, zero active unresolved threads, normal expected-head
merge, intended-tree equality and post-main checks must all qualify the final repair.
The external canonical receipt retains the actual run, artifact and report hashes.

The repair contract protects 43 files, including all 26 original R1 controls, the
original failed attempt evidence and every unchanged R2 worker, scientific wrapper,
producer constraint, SDK qualification and execution workflow. The failed first
attempt remains immutable with zero generations and all 1463 development identities
unattempted. SG-000028 retains its original 224 PASS / 1239 blockers result. Founder
cost remains zero; the 40-patient / 173-row final role stays sealed. D4, training,
scoring and final evaluation stay inactive. After qualification, normal merge and
post-main verification, stop before any model call and present the canonical repair
evidence for a separate founder decision.

## Native qualification blocker retained

The first actual workflow-token preflight, run `37327235548` on `7bab1c9`, passed
the repaired repository lookup and then failed at the unchanged receipt parser.
The historical receipt comment was originally stored with CRLF line endings;
the parser expects literal LF. Its JSON exactly matches the immutable canonical
record after CRLF-to-LF normalization. The verified failure artifact and proof are
retained in `registry/study1_sg000031_admission_repair_preflight_failure.json`.
This is an engineering qualification trial, not a new R2 execution attempt.

The founder separately authorized the CRLF extension in PR #161. Its verbatim
statement and hash are retained in
`registry/study1_sg000031_admission_repair_crlf_authorization.json`; the original
URL-only authorization and failed qualification evidence remain unchanged.

At the receipt parsing boundary, `qualify_canonical_receipt` now applies exactly
`comment["body"].replace("\r\n", "\n")` to a local string before the existing marker,
JSON and semantic checks. Only CRLF pairs become LF; lone CR characters, JSON escape
sequences, fields, structures and semantic bindings are not changed. The source
comment is never rewritten. LF and CRLF fixtures produce the same parsed receipt,
tree and review-unit count. Negative fixtures exercise both representations and
retain rejection of malformed markers/fences/JSON, incomplete or invalid structures,
invalid bindings, foreign issue/author sources, lone CR, changed live main and
unmerged PRs. External engineering I/O is synthetic in these deterministic tests;
the workflow separately exercises actual native authenticated admission validation.

The changed head requires fresh genuine Jev, approved Alibaba, full CI,
manuscript/arXiv, SDK and native preflight evidence, followed by zero active review
threads, guarded normal merge and full post-main verification. Earlier-head evidence
does not qualify this candidate. No model call or new experiment attempt is authorized.
