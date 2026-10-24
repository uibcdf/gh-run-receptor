# GitHub evidence sources

## Acquisition boundary

The client delegates authentication and HTTP transport to the installed GitHub CLI.
The acquisition adapter invokes `gh api` with arguments, never through a shell command
assembled from untrusted values. Tokens remain under GitHub CLI control and are never
printed, placed in URLs, or stored in evidence bundles.

The adapter records the requested GitHub API version. It must not silently switch to an
implicit latest schema. GitHub.com is the initial target; GitHub Enterprise Server
support is unclaimed until hostname, API-version, and endpoint compatibility tests
exist.

Network acquisition requires GitHub CLI 2.48.0 or newer. That release is the first to
contain the `--paginate --slurp` interface used to turn every response page into one valid
outer JSON array. The adapter checks the stable `gh --version` first line once per remote
client and rejects an older or unrecognizable version with `unsupported_gh_cli` before an
API request. This is a functional floor; users should install the latest patched stable
CLI. Offline paths do not perform the check.

## Structured resources

A full capture obtains these resources independently because GitHub has no single total
run JSON document:

| Bundle member | REST resource | Purpose |
| --- | --- | --- |
| `run.json` | workflow run and selected attempt | Authoritative run identity, status, conclusion, ref, SHA, event, actors, and resource URLs |
| `workflow.json` | workflow by numeric ID | Stable repository-local ID, display name, file path, and state |
| `jobs.json` | jobs for the selected run attempt | Jobs, runner labels, timestamps, conclusions, and step metadata |
| `checks.json` | check runs for the run's exact check-suite ID | Check output and annotations not represented in job logs without mixing runs for the same commit |
| `artifacts.json` | artifacts for the workflow run | Names, sizes, digests, expiry, and download availability |
| `config.json` | configuration content from the repository default branch | Trusted normalized workflow rules plus branch and digest provenance; optional |
| `logs.zip` | log archive for the run attempt | Full textual evidence and step fragments when structured facts are insufficient |

The exact request URL, response status, pagination state, ETag when available, content
type, byte length, and SHA-256 digest belong in the manifest. Acquisition follows
pagination until completion or records the capture as incomplete.

For completed cancelled/timed-out jobs, bounded job-linked check annotations are
now stored inside `checks.json`. This requires at most 50 additional read requests,
one page of 100 annotations and 2 MiB per check. Other jobs incur no annotation
requests. Identity, truncation and uncertainty follow
[timeout diagnosis](timeout_diagnosis.md); textual hints never rewrite native conclusions.

Official references:

- [Workflow runs](https://docs.github.com/en/rest/actions/workflow-runs)
- [Workflows](https://docs.github.com/en/rest/actions/workflows)
- [Artifacts](https://docs.github.com/en/rest/actions/artifacts)
- [Check runs](https://docs.github.com/en/rest/checks/runs)
- [GitHub CLI run view](https://cli.github.com/manual/gh_run_view)

## Workflow and run selection

The list endpoint for a workflow accepts either a numeric workflow ID or its file name.
The receptor pushes supported filters to GitHub instead of downloading all runs first:

- workflow ID or file name;
- branch;
- head SHA;
- event;
- status;
- actor;
- creation interval.

The CLI validates repository, workflow, and run identifiers before interpolation into
API paths. A run URL is normalized to hostname, owner, repository, and numeric run ID.

## Attempts

Run ID alone is not a complete evidence identity. Every bundle and report includes
`run_attempt`. `inspect` defaults to the current attempt returned by GitHub; an explicit
`--attempt` selects a historical attempt. For a historical selection, the run response,
jobs, and logs are fetched from attempt-specific endpoints and their identity is validated
before use. Evidence from different attempts is never merged implicitly. Artifact listing
remains a run-level GitHub endpoint and therefore is not treated as proof that an artifact
belongs to one particular attempt.

`compare RUN_ID --attempt A --attempt B` may compare attempts, but preserves each source
fact independently.

## Status and conclusion

GitHub status and conclusion values are open enums. Known values include queued,
pending, in progress, waiting, requested, action required, completed, success, failure,
cancelled, skipped, neutral, stale, startup failure, and timed out. Unknown future
values are preserved verbatim and produce a conservative assessment.

The run response is authoritative for run status and conclusion. Job responses are
authoritative for jobs. Step metadata is authoritative for step outcome and conclusion
when present. Log text never overrides these fields.

`timed_out` remains a valid open-enum conclusion, but it must not be inferred from elapsed
time or a configured job timeout. In measured run `34027741137`, GitHub applied
`timeout-minutes: 1` by reporting the run, job, and interrupted step as `cancelled`.
GitHub's workflow syntax likewise describes job timeout as automatic cancellation. A
`timed_out` assessment therefore requires that exact source conclusion; synthetic coverage
is retained until an authentic workflow-run example is observed. Under the conjunctive
non-generatable-outcome rule in [Testing strategy](testing_strategy.md), that absent
example is an explicit corpus limitation rather than an indefinite 1.0 blocker. The
upstream distinctions are documented in GitHub's
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[workflow-run REST API](https://docs.github.com/en/rest/actions/workflow-runs), and
[Checks API guide](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks).

## Logs

The run-log endpoint returns a redirect to an archive; the redirect URL is temporary and
is not stored as durable evidence. The downloaded archive is hashed and retained under
the configured capture policy.

Known limitations must remain visible:

- GitHub CLI may fail to associate archive members with jobs and fall back to fetching
  job logs individually.
- Lines may be attributed to `UNKNOWN STEP`.
- GitHub CLI documents a failure when more than 25 job logs remain missing in that
  fallback.
- Logs can be unavailable while a job is still running or after retention expiry.
- Timestamps, runner prefixes, ANSI sequences, repeated job names, and progress updates
  can dominate textual output.

Missing or unassociated logs lower evidence completeness; they do not manufacture a
successful or generic diagnosis.

## Artifacts

Artifact inventory is metadata and is always captured when permitted. Large artifact
archives are not downloaded merely to list them. A profile may request a small,
versioned receptor evidence artifact by exact name. Package archives require an
explicit request or profile rule with size bounds.

Expired and unavailable artifacts remain represented with their metadata. The digest
reported by GitHub and the digest of any downloaded archive are recorded separately.

The explicit `published` path is the first bounded artifact-content consumer. It selects
one exact report name, rejects inventory or downloaded ZIPs over 10 MiB, accepts one regular
JSON member expanded to at most 8 MiB, and verifies a supplied GitHub SHA-256 digest. It
then performs a fresh source-run lookup. A digest proves the downloaded bytes; it does not
prove the producer's interpretation.

The source-first `published-source` path first retrieves the completed source run to derive
its current attempt, then queries the repository artifact endpoint by the exact deterministic
`<prefix>-<run>-<attempt>` name. GitHub's artifact record supplies the publishing
`workflow_run.id`; the consumer retrieves that run and its workflow record and requires a
completed `workflow_run` event at the configured exact workflow path before downloading any
artifact bytes. Exactly one result is required. This identifies the trusted publication
route but still does not make its profile interpretation an authoritative GitHub fact.

## Authentication and permissions

Public metadata may be available anonymously, but supported operation assumes an
authenticated `gh` session. Private repositories require appropriate repository and
Actions read access. Embedded reporting declares the minimum `actions: read` and
`contents: read` permissions. Checks are read-only in the initial product.

Authentication failure, insufficient scope, SSO requirements, and inaccessible private
resources are distinct acquisition errors. They are redacted and reported without
printing headers or tokens.

The implemented transport categories are `authentication_required` when GitHub CLI has no
session, `authentication_failed` for HTTP 401, `permission_denied` for HTTP 403,
`not_found_or_inaccessible` for HTTP 404, `rate_limited` for HTTP 429 or an explicit
rate-limit diagnostic, `unsupported_gh_cli` for an incompatible local CLI interface, and
`acquisition_failed` otherwise. The HTTP status is retained when observed.
Optional-resource lookup suppresses only a structured 404; it does not
generalize string matching to other errors. Because GitHub may hide inaccessible private
resources behind 404, the user-facing category preserves that ambiguity.

## Rate limits and caching

- Cache immutable completed-attempt responses by repository, run ID, attempt, URL, and
  ETag.
- Refresh an active run with deterministic bounded backoff: 1.5 after unchanged state,
  reset after a transition, and 2 after an acquisition failure.
- Render only state transitions in watch mode.
- In adaptive mode, do not fetch logs for any active or completed successful run.
- In adaptive mode, request one complete attempt archive after GitHub confirms completion
  with any conclusion other than `success`, including absent or unrecognized values.
- Do not download the same content digest twice within a cache.
- Surface rate-limit exhaustion and the next available reset time when GitHub provides
  it.

Conditional requests and cached completed evidence reduce both API use and latency.
Cache reuse never changes the requested repository, attempt, or API-version identity.

## Retention and incompleteness

GitHub.com commonly retains logs and artifacts for a bounded repository-configured
period; 90 days is a common default, not a receptor guarantee. A bundle records expiry
metadata when provided. Missing historical logs or artifacts yield a valid but
explicitly incomplete bundle.

## Failed acquisition request identity

Transport failures retain the existing error category and HTTP status and add
internal exception fields `operation` and `request_path`. Known operations are
`api.json`, `api.download`, `cli.version` and `repository`. CLI/Action diagnostics
name that operation and a bounded relative API path. Paths omit all query and
fragment data and reject absolute/unsafe endpoints; paginated calls identify the
collection, not an inferred failing internal page. No raw command/header/token
or temporary redirect URL is printed.

The known generic network footer no longer hides its preceding diagnostic.
Transport details redact credential shapes, all URLs and control characters.
Path/detail/context bounds are 240/500/800 characters respectively. Structured
output decoding, size limits, optional HTTP-404 behavior, child cleanup and the
source conclusion/process-status contracts are unchanged. No new retry loop is
added: watch retains its documented consecutive-failure budget. This resolves
observability in uibcdf/gh-run-receptor#67; it does not claim a network outage was
fixed or that a later successful request reproduces the original incident.

## Explicit completed-job logs (1.3.0 candidate)

`inspect RUN --job JOB_ID` and `capture RUN --job JOB_ID` select one completed
job's plain-text log while retaining all structured facts for the selected run
attempt. This additive capability is provisional until native/installed receiving
is recorded under uibcdf/gh-run-receptor#68. It does not change the default
full/adaptive/metadata truth table or the Action/reusable workflow defaults.

The attempt-qualified jobs collection must contain exactly one matching numeric
job ID, with matching run ID and any supplied attempt/SHA. Missing, duplicate,
conflicting or active jobs are refused before download. Missing optional job
`run_attempt` is accepted only because collection membership was obtained through
the selected attempt endpoint. The repository is bound by that request, not an
untrusted log URL. Historical jobs are never looked up in the latest-attempt list.
The selected workflow status and conclusion remain unchanged, including an absent
active conclusion. Logs cannot invent a terminal workflow outcome.

The independently reusable `job_logs.completed_job`, `capture_job_log` and
`validate_job_log_scope` operations own selection, bounded acquisition and replay
validation. The existing gh adapter follows the job-log redirect with credentials
kept under gh control. At most one additional log request is made, with a 32 MiB
byte limit. No attempt ZIP is requested, even for explicit full capture.
Metadata-only selection downloads no logs. Raw bytes remain private bundle
members; the shared bounded stream analyzer handles plain and archived logs.
Timestamp removal preserves traceback indentation. A plain job log provides
job/line provenance, without fabricating archive members or step attribution.

`log_scope: {kind: job, job_id: N}` marks this subset in the manifest/report.
Members use `job-N.log`, kind `github.job_log`, exact job/run/attempt IDs, byte
count and SHA-256. Replay rejects conflicting or ambiguous scope, an accompanying
attempt ZIP, oversized logs and logs in metadata-only captures. Cache identity
adds `job-N` before the existing policy directory; ordinary attempt caches and
other selected jobs cannot satisfy this request. Active run snapshots still
refresh atomically and rollback on failure.

Run-log completeness is `partial` when the selected log is available, never
`complete`. Cause evidence is likewise partial even if this is the only failed
job. A fully acquired requested subset may have `evidence_sufficient: true`;
that does not assert complete workflow logs or terminal execution. Selected
successful/unknown-conclusion jobs retain their logs without inferring a failed
cause from text. Acquisition errors retain structured category/HTTP status in
`job_log_error`; 403 maps to `not_permitted`, 410 to `expired`, and ambiguous
404 remains `unavailable`. An unavailable requested log produces incomplete
capture and exit 4, with native source facts preserved. Available logs on an
active workflow retain PENDING/exit 3; terminal source exit rules are unchanged.
All text renderers label the job-only scope and JSON retains it explicitly.

Regression guard: `tests/test_job_logs.py`; diagnostic ranking and the nine
published schema resources remain shared and byte-frozen.

### Raw-to-file gh compatibility

Native #68 receiving at source 54afb4c reproduced modern gh refusing a plain job
log containing ANSI escapes. Since gh 2.97.0, `gh api` implements that explicit
raw-output guard. The adapter records its already checked CLI version and passes
`--allow-escape-sequences` only for bounded binary/plain downloads into its
private stdout pipe and destination file. It never streams these bytes to the
user terminal. JSON acquisition and rendered text retain their safety controls.
Older supported gh 2.48.0--2.96.x do not receive an unknown flag. This adds no
request/retry or authentication route and does not raise the functional floor.
Tests cover both sides of the version boundary, exact ANSI byte preservation,
no terminal output and the existing byte-limit/child/partial-file cleanup rules.

Primary sources: [gh 2.97 API implementation](https://github.com/cli/cli/blob/v2.97.0/pkg/cmd/api/api.go)
and [upstream terminal-output advisory](https://github.com/cli/cli/security/advisories/GHSA-3m3g-3wcr-px46).
