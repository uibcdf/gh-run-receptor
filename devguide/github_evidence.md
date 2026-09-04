# GitHub evidence sources

## Acquisition boundary

The prototype delegates authentication and HTTP transport to the installed GitHub CLI.
The acquisition adapter invokes `gh api` with arguments, never through a shell command
assembled from untrusted values. Tokens remain under GitHub CLI control and are never
printed, placed in URLs, or stored in evidence bundles.

The adapter records the requested GitHub API version. It must not silently switch to an
implicit latest schema. GitHub.com is the initial target; GitHub Enterprise Server
support is unclaimed until hostname, API-version, and endpoint compatibility tests
exist.

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
`--attempt` selects a historical attempt. Jobs and logs must be fetched from the same
attempt endpoint. Evidence from different attempts is never merged implicitly.

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

## Authentication and permissions

Public metadata may be available anonymously, but supported operation assumes an
authenticated `gh` session. Private repositories require appropriate repository and
Actions read access. Embedded reporting declares the minimum `actions: read` and
`contents: read` permissions. Checks are read-only in the initial product.

Authentication failure, insufficient scope, SSO requirements, and inaccessible private
resources are distinct acquisition errors. They are redacted and reported without
printing headers or tokens.

## Rate limits and caching

- Cache immutable completed-attempt responses by repository, run ID, attempt, URL, and
  ETag.
- Refresh an active run with bounded exponential polling and jitter.
- Render only state transitions in watch mode.
- Do not fetch logs for healthy active jobs.
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
