# Timeout and cancellation diagnosis

This contract records the reader improvement and measured assessment for
uibcdf/gh-run-receptor#46, handed back to uibcdf/molsyssuite#25. It describes
source changes after published 1.1.1; no new release or producer contract is claimed.

## Source authority and available evidence

| Source | Captured capability | Authority and limitation |
| --- | --- | --- |
| Run and selected-attempt REST record | Status, conclusion, SHA, attempt, check-suite identity | Authoritative run outcome; cancellation does not identify its trigger |
| Selected-attempt job and step records | Outcome, timing, interrupted step, job-to-check URL | Authoritative job/step outcomes; duration does not establish a deadline |
| Exact-suite check runs | Check outcome, output metadata, annotation count | Already captured; check output does not certify an operation supervisor |
| Job-linked check annotations | Newly acquired bounded diagnostic page | Untrusted textual hints with source pointer, never verified cancellation causality |
| Attempt logs | Full capture or adaptive non-success capture | Supplementary diagnostics; printed markers and exit 124 are not verified deadlines |
| Artifact inventory and selected `events@1` documents | Existing bounded digest/ZIP/JSON validation and offline replay | Current events describe `conda.package`; no generic operation-timeout contract exists |
| Workflow configuration | Reviewed exact-SHA experiment configuration; ordinary trusted configuration remains default-branch receptor rules | `timeout-minutes` is configuration intent, not proof that it caused this outcome; workflow content is not executed |

The public recheck on 2026-10-02 of run `34027741137`, attempt 1, SHA
`a87e5b9748ceaf1d6c5277a34dd2d533eca11865`, found:

- Run, job `101471629872`, and step `Wait beyond the job timeout` are `cancelled`.
- The exact source workflow configured `timeout-minutes: 1` around `sleep 90`.
- Check suite `92196732709` contains job-linked check `101471629872`, with two
  failure annotations. The first states that the job exceeded `1m0s`; the second
  states that the operation was canceled. Check output title, summary and text are null.
- The artifact inventory is empty. Logs preserve runner cancellation text and
  the interrupted command, without an operation-supervisor record.

These independently inspected experiment facts support a useful execution-limit
hint. They do not establish that arbitrary matching annotations are emitted by a
trusted supervisor. GitHub workflow commands can create error annotations, so even
an exact message and the GitHub Actions app identity cannot authenticate its author.
No manual/concurrency/fail-fast/runner-loss distinction is claimed from absent text.
No new authentic native `timed_out` run was obtained; historical bounded-search
results remain historical, and exact native `timed_out` coverage remains synthetic.

Official references are [job records](https://docs.github.com/en/rest/actions/workflow-jobs),
[check annotations](https://docs.github.com/en/rest/checks/runs#list-check-run-annotations),
[job timeout syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes),
and [workflow error annotations](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#setting-an-error-message).

## Bounded acquisition and identity

All capture policies may obtain annotations for completed `cancelled` or `timed_out`
jobs. Active, successful and ordinary failed jobs incur no annotation requests.
Link only through the job's exact same-repository `check_run_url`, reconstructed
as an adapter endpoint rather than following supplied URLs. Require unique job/check
linkage, matching SHA, exact run check-suite ID, terminal status and conclusion,
and matching run/attempt/SHA fields whenever the job supplies them. Check IDs are
not assumed to equal job IDs. Another attempt, suite, host or repository cannot
provide a hint. Replay repeats the identity validation over normalized facts.

Acquire at most 50 checks, one `per_page=100` request per check, with a 2 MiB
response limit enforced by the existing transport. Replay validates the same 2 MiB
compact-JSON page budget, at most 100 annotation objects, 4,096 message characters
and 64 level characters. Unknown fields remain in captured evidence within that
budget. Derived messages are redacted and bounded to 500 characters. Text output
uses the existing control escaping and 300-character display limit.

The check record's additive `annotations_state` is `complete`, `partial`,
`unavailable`, `invalid` or `not_requested`. A zero advertised count is complete
without a request. Missing/invalid count metadata requests nothing and remains
`not_requested`. Missing linkage in old captures also remains `not_requested`.
Do not fetch another page: an advertised count larger than the returned page,
an inconsistent count, or an exceeded check budget is explicitly partial.
Requested permission/transport/JSON acquisition failure is unavailable; malformed collections or
conflicting identity are invalid. Warnings retain the existing incomplete-bundle
behavior: replay becomes `INCOMPLETE` with exit 4 while GitHub's conclusion stays
unchanged. Capture completeness never promises exhaustive annotations.
The additive `completeness.check_annotations` aggregates explicit states with
precedence invalid, unavailable, partial, complete, then not-requested. Replay
does not accept a complete-manifest claim over explicitly incomplete annotations.

Checks read permission is sufficient; no token scope or write permission is added.
The public acquisition was measured. Private/fork token portability and Enterprise
compatibility remain unclaimed. Cached older bundles are not augmented during replay;
a fresh capture is needed for annotations. Watch adds these requests only at its
ordinary final capture, not on each poll.

## Additive normalized and report fields

Frozen `model@1` and `report@1` schemas already permit these additive properties;
their bytes and integer versions remain unchanged.

- Model subject: `check_suite_id`; linked job: `check_run_id`; root: `checks`.
- Normalized checks retain ID, SHA, suite ID, status, conclusion,
  `annotation_evidence`, and bounded annotations with level and source pointer.
- Report root `checks` retains those normalized facts, including unknown check
  conclusions and unmatched annotations, separately from termination interpretation.
- Report root: optional `termination`, containing source run conclusion, cause
  and termination job records. Each job retains native conclusion, source job
  pointer, annotation evidence state and at most one execution-limit hint.

`cause=native_timeout` means that the relevant run or job has the exact native
`timed_out` conclusion. It does not identify an internally supervised operation.
For cancellation, `cause=unknown` remains explicit even when a hint exists.
An exact failure-level execution-limit annotation contributes only
`verification=diagnostic_hint`, kind `job_execution_limit`, a bounded summary
and `checks.json` JSON Pointer. Other annotations remain normalized evidence.
No annotation changes assessment, exit code, or grouped log root causes.
Run success with a tolerated cancelled job retains source success and exit 0.

Human and LLM reports show `hint (unverified)`, native state, unknown cause and
source pointer. They show at most ten termination jobs and one hint each, with
an omitted-record count; JSON retains every termination record. All profiles
use the same interpretation and rendering helper.

## Residual requirement for MolSysSuite

For long tests or Conda operations inside one composite Action, a maintainer may
need to know which operation exceeded which enforced limit and whether sibling
work completed before the job was interrupted. Native job cancellation and
untrusted annotation text cannot establish that operation boundary or trigger.
If that verified distinction is required, cooperating execution must emit:

1. Repository, run ID, attempt, SHA, job/invocation and matrix identity.
2. Stable operation ID and scope, distinguishing operation, step and job deadlines.
3. Supervisor implementation/revision and an explicit observation of the deadline
   trigger, separate from a child exit code or printed verdict.
4. Enforced limit with units, elapsed measurement and observed terminal result,
   including independent child exit/signal state and any completed sibling work.
5. Bounded durable evidence available after interruption; a job-level hard kill may
   prevent an artifact upload, so missing evidence must remain unknown.

This is a provisional evidence requirement, not an accepted schema or producer
selection. A supervisor-authored record is still a cooperating producer claim,
not independently authenticated execution truth. MolSysSuite must decide the
required trust and compatibility contract before the reader promotes that claim.
Existing acquisition, integrity validation, invocation identity and replay helpers
are reusable. An existing Action, workflow wrapper or other established producer
may supply the evidence; no new Action is required by this assessment.
The frozen `events@1` kind cannot silently acquire incompatible semantics.

## Verification

The reviewed public fixture `tests/fixtures/bundles/gh_run_receptor_job_limit_cancelled`
retains only relevant structured fields and two reviewed annotations. Raw captures
and logs stay outside the repository. `tests/test_termination.py` protects all five
profiles, native-outcome truth tables, spoofed markers, cancellation ambiguity,
availability, cross-attempt identity, capture-to-replay behavior, deterministic
goldens and bounded matrices. `tests/test_checks.py` protects malformed, truncated,
unknown-field and exact count/byte/character boundaries and the 50-request budget.
The relevant closure guard is the termination module: removing linked hints or
promoting them to verified timeout fails its original-run and truth-table assertions.
