---
summary: Identify the failed GitHub request without losing its actionable diagnostic.
issue: uibcdf/gh-run-receptor#67
status: resolved
opened: 2026-10-24
closed: 2026-10-24
severity: medium
verification: reproduced
area: [github, cli, security]
guard: tests/test_github.py
normative: github_evidence.md
blocked_by: []
supersedes: []
---

# Failed acquisition loses request context

## Original evidence and reproduction

The incoming public MOLI run `39513025386`, source
`946d0ffea7918afdb28886b1c23217d034bdc4df`, was inspected with provider
`d2551b272541bafe54f784f2d1ace38af5490d83` and GitHub CLI 2.100.0.
Both native gh and the receptor intermittently failed to connect. This does not
establish a receptor-only connectivity failure or a failed source workflow.
The old transport selected the final generic network footer and did not name the
failed command/resource. Controlled process fixtures reproduce that observability
loss without manufacturing a live network outage.

## Source correction and scope

The existing GitHub adapter now attaches `api.json`, `api.download`,
`cli.version` or `repository` identity and a bounded relative request path.
Query strings, fragments, absolute/unsafe endpoints, raw headers and command
arguments are not exposed. Error details redact URLs (including signed redirects),
credentials and controls. Removing the known generic network footer preserves
its preceding useful diagnostic. HTTP categories/status, optional 404 absence,
response limits, interrupted child cleanup and partial-download removal remain.
Malformed JSON/UTF-8 and local execution errors receive the same context.

The exception's additive internal `operation` and `request_path` fields do not
change any serialized schema. Request paths are limited to 240 characters,
transport detail to 500 and the whole contextual message to 800. Paginated CLI
calls identify their collection; a failing internal HTTP page is not guessed.

## Retry decision

No new transport retry loop is introduced in this patch. One adapter request
remains one CLI invocation; gh may implement its own transport behavior.
Watch retains its existing two degraded polls and abort on the third consecutive
failure. Stacking another retry would change the frozen API budget without a
measured transient-error distribution. Any later retry change requires its own
explicit policy/evidence; users can rerun an inspect operation independently.

## Guard and acceptance

`test_cli_request_failure_keeps_exit_five_and_one_safe_line` checks the actual
CLI pipeline, request path, useful diagnostic, single safe stderr line and exit 5.
Parameterized JSON/download failures cover categories, statuses, no added retries,
secret/URL/control redaction and removal of partial files. Malformed output,
CLI-version provenance and exact path-size boundaries have independent guards.
The existing failed/successful/cancelled/incomplete truth tables remain mandatory.
Source and installed release qualification is recorded separately; a passing
request later does not reproduce or retrospectively fix the earlier outage.

## Local source resolution

The clean task-owned Python 3.14.7 environment passes the full source suite:
729 tests and one explicit Conda-installed-only skip, using the committed
pytest-receptor 1.1.0 pin. Dependency closure is clean; Ruff and all nine frozen
contracts pass. The source fix is complete; exact release-candidate native,
installed-file and public delivery evidence remain in the release checkpoint.
No production connectivity recovery is inferred from these controlled cases.
