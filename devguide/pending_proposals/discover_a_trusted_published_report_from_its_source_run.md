---
summary: Discover a trusted published report from its source run
issue: uibcdf/gh-run-receptor#21
status: open
opened: 2026-09-06
closed:
verification: asserted
area: ['github', 'cli', 'security']
guard:
normative:
blocked_by: []
supersedes: []
---

# Discovering a trusted published report from its source run

**Reported:** 2026-09-06, while exercising the first external published-report consumer.
**Status:** Open; the API contract and fail-closed selection rules are defined below.

## What

The `published` command requires the downstream reporter run ID even though users normally
start with the source workflow run ID shown by GitHub. Add a one-command path that discovers
and consumes the trusted compact report from the source identity.

## How

The embedded Action will treat `report-name` as a safe prefix and publish an artifact named
`<prefix>-<source_run_id>-<source_run_attempt>`. Including the attempt is necessary because
GitHub preserves a run ID across reruns.

`published-source SOURCE_RUN` will:

1. fetch the current source run and derive its authoritative attempt;
2. query repository artifacts by the exact deterministic name;
3. require exactly one non-expired candidate with a valid publishing run ID;
4. require that publishing run to be completed, triggered by `workflow_run`, and owned by
   the expected canonical reporter workflow path;
5. pass the discovered publishing run and exact artifact to the existing bounded consumer,
   which verifies the archive digest, JSON contract, publisher provenance, report subject,
   current source facts, assessment compatibility, and renderability.

The expected workflow defaults to
`.github/workflows/gh-run-receptor-report.yml` and remains explicitly overridable. The old
`published REPORTER_RUN --artifact NAME` path remains available as the diagnostic fallback.

## Why

Without discovery, the compact artifact path needs a native `gh run list` or web lookup to
find the reporter before it can save tokens. Source-first discovery makes compact consumption
a practical replacement for routine native inspection while retaining a visible trust
boundary.

## What is measured and what is assumed

Observed from the official GitHub REST contract on 2026-09-06:

- repository artifact listing accepts a name filter and returns the publishing
  `workflow_run.id` with artifact identity and digest;
- workflow run records expose `event`, `workflow_id`, `path`, `head_sha`, and attempt.

The reduction benefit is not estimated here. Existing measurements compare explicit
published consumption with fresh metadata capture; a live source-first run will be measured
after deployment.

## What was refuted

- A name containing only the source run ID was rejected because reruns share that ID and
  would create permanent discovery ambiguity.
- Scanning arbitrary artifacts or downloading candidates before checking their producer was
  rejected because it increases requests and processes attacker-controlled data too early.
- Silently selecting the newest duplicate was rejected because repository artifact order is
  not a trust rule.
- Replacing the explicit `published` command was rejected because it remains the bounded
  recovery path for non-canonical reporter workflows and historical artifacts.

## Scope and exclusions

This increment does not deploy recurring reporter workflows to client repositories, define
cross-repository reporters, trust profile interpretation as independently recomputed, or
solve restricted-token and fork permission validation. Client deployment remains a separate
decision because every `workflow_run` reporter consumes runner resources.

## Acceptance criteria

- Action output and uploaded artifact names contain source run and attempt identity.
- `published-source` accepts numeric IDs and run URLs consistently with other run commands.
- Candidate selection, expiry, producer event, workflow identity, and ambiguity fail closed.
- The discovered path retains all explicit-consumer archive and source-fact checks.
- Unit tests prove that neither source jobs nor logs are fetched.
- The full pytest, Ruff, build, and developer-guide gates pass.
- A hosted canonical reporter publishes and is consumed from only the source run ID.

## Dependencies and risks

The API exposes producer run identity on repository artifact records but not the full
producer workflow identity, so discovery needs one additional run lookup and workflow
lookup. Artifact retention can make discovery unavailable; this is expected and must be
reported as absence rather than reconstructed. No tracked dependency blocks implementation.

## Provenance

API fields were checked against GitHub's official REST documentation on 2026-09-06. Live
validation provenance will be recorded before closure.
