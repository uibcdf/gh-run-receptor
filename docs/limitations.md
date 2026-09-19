# Limitations

The receptor is deliberately conservative. These limits are part of using it safely, not
small print to discover after a release decision.

## Distribution and lifecycle

- The project is pre-1.0 and is currently distributed as a GitHub CLI script extension and
  verified GitHub Release artifacts, not through PyPI or Conda.
- The public Python support window is 3.11 through 3.13. A standalone binary is not
  published.
- GitHub CLI 2.48.0 is the tested network floor; alternate GitHub Enterprise Server and
  older runner behavior is not broadly claimed.

## Evidence outside GitHub Actions

An observed command or successful step does not independently verify:

- package presence in PyPI, Conda, npm, or another registry;
- Git tag identity or a public GitHub Release unless queried separately;
- deployment contents at a Pages or application URL;
- Zenodo ingestion, DOI assignment, or archival integrity.

Use the external service as the source of truth for those claims.

## Retention and permissions

GitHub can expire logs and artifacts. A later metadata query may preserve the official run
conclusion while lacking evidence needed for diagnosis, in which case the receptor reports
`INCOMPLETE`. Private-repository and fork token behavior has not completed a broad hosted
validation matrix and remains an explicitly narrower claim.

Adaptive capture avoids the complete log request for active and successful runs, but a
terminal non-success can still have a large archive. Acquisition is bounded at 512 MiB.
The current GitHub attempt endpoint is consumed as one archive; gh-run-receptor does not
claim selective failed-job transfer. Raw bundles can contain sensitive output and remain
local unless explicitly reviewed and sanitized.

## Interpretation coverage

- Built-in profiles are initial vertical slices, not general CI semantics for every tool.
- Generic log diagnosis recognizes a deliberately small bounded signature set.
- Automatic discovery uses conservative signals and falls back to `generic` rather than
  guessing a specialized profile.
- Workflow rules support exact path, numeric ID, or exact display name. Patterns and
  organization-level configuration are not implemented.
- Action-internal work needs structured producer events; Action inputs and artifact
  filenames alone are not proof.

## Watch and active runs

`watch` polls GitHub, prints only transitions, and emits one final report. Its stable
request formula depends on jobs pagination, historical-attempt selection, final evidence,
and transient failures; it is not a fixed number for every workflow. Calling the embedded
Action from the source run itself reports `PENDING`, because that run cannot be complete
while the reporting step executes.

## Outcome corpus

Success, failure, cancellation, action-required/stale semantics, incomplete evidence, and
rerun attempts have deterministic coverage. Authentic GitHub `timed_out` evidence remains
opportunistic: a normal job timeout has been observed as cancellation, so the receptor
does not infer `TIMED_OUT` merely from elapsed time or a workflow timeout setting.

## No mutation

The product does not rerun jobs, cancel workflows, approve environments, publish packages,
or deploy documentation. This is intentional. The initial stable contract is read-only;
future mutation would require explicit user intent and separate permissions.

## When native output is better

If the only question is whether one completed run succeeded, a minimal native GitHub JSON
query can be smaller than a receptor report. Use the receptor when job, matrix, artifact,
failure, completeness, comparison, or replay evidence matters. Use native inspection when
the report explicitly tells you its model is insufficient.
