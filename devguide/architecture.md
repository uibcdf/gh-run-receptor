# Architecture

## Evidence pipeline

The system is divided into five stages:

```text
GitHub API and logs
        |
        v
capture -> normalize -> classify -> render -> publish
   |          |            |          |          |
 bundle    event model   profile    llm/json   stdout,
                                                 summary,
                                                 artifact
```

Capture, normalization, and rendering belong to the shared core. The CLI, GitHub Action,
and reusable workflow are adapters around that core.

## Evidence bundle

GitHub does not expose one complete run document. A full capture therefore stores the
separate resources with a manifest:

```text
run-<id>-attempt-<n>/
├── manifest.json
├── run.json
├── workflow.json
├── jobs.json
├── checks.json
├── artifacts.json
├── logs.zip
└── receptor-report.json
```

The manifest records the repository, run and attempt identifiers, head commit, API
version, capture time, receptor version, and SHA-256 digest of every member. Original
responses are immutable within a bundle. Derived reports are replaceable and identify
the receptor version that produced them.

Raw bundles may contain sensitive data and must be owner-readable, excluded from source
control by default, and subject to an explicit retention policy.

## Capture policies

- `full`: capture all structured resources and the complete log archive.
- `adaptive`: capture all structured resources and fetch logs only for failed or
  otherwise unresolved jobs.
- `metadata`: capture structured resources without logs.

The development default is `full` because it supports differential testing and offline
replay. The intended stable default is `adaptive`. A successful report should normally
require no full-log download.

## Normalized model

The normalized model must represent:

- repository, workflow path and ID;
- run number, run attempt, event, ref, and head SHA;
- run status and conclusion;
- jobs, matrix identities, dependencies, timestamps, and conclusions;
- steps, outcomes, conclusions, and durations;
- checks and annotations;
- artifact names, sizes, digests, expiration, and availability;
- causal evidence extracted from logs with provenance;
- receptor observations, profile interpretations, and confidence kept as distinct
  fields.

The model requires a versioned serialization contract. Source facts must never be
overwritten by profile conclusions.

## Output channels

The same report can be rendered to:

- explanatory stdout for a human receptor;
- compact stdout for an LLM receptor;
- JSON for automation and replay;
- Markdown through `GITHUB_STEP_SUMMARY`;
- a small `gh-run-receptor-report.json` workflow artifact.

The compact renderer prints one verdict, the minimum useful matrix summary, distinct
causes, evidence locations, and suggested read-only follow-up or rerun commands. It does
not stream unchanged polling snapshots.

The human and LLM renderers consume the same report and therefore cannot disagree on
source state. Human output favors labels and a bounded complete job inventory; LLM output
favors distinct failures, decisions, and evidence pointers. JSON is not a third receptor:
it serializes the shared report independently of text presentation.

## Embedded reporting

The composite Action is a publication adapter around the same capture and report services
used by the CLI. It validates Actions inputs, writes bounded scalar outputs and Markdown,
adds publisher provenance, and uploads the canonical JSON report. It does not normalize or
interpret evidence independently.

A reporter inside the source run necessarily observes an active run and remains `PENDING`.
A terminal report uses an explicit completed source run ID, normally from a downstream
`workflow_run` workflow. This avoids circular self-exclusion and invented terminal truth.

The external CLI's `published` adapter reverses the publication path without re-running the
pipeline. It downloads one bounded report artifact, validates it as untrusted input, and
freshly verifies only its GitHub source facts. It reuses the shared renderers but labels the
profile interpretation as published and not independently recomputed.

The embedded reporter is observability rather than a product gate. Failure to render produces a
visible `RECEPTOR_ERROR` but must not convert successful primary work into a false
product failure. Cancellation may prevent the reporting job from running, so the
external CLI remains the universal fallback.

## Trust boundaries

- API metadata is authoritative for status and conclusion.
- Logs and artifact contents are untrusted input.
- Control characters and terminal escapes are neutralized before rendering.
- Recognizable credential shapes are redacted from rendered and derived evidence.
- Rules are data, not executable code.
- Configuration obtained from an untrusted pull-request checkout is not automatically
  granted authority over reporting behavior.
- Network, parser, and profile failures are explicit and never collapse to success.

## Dependency direction

The implementation dependency graph is one-way:

```text
transport adapters -> captured source records -> normalized model
                                              -> profile interpretation -> report
                                                                        -> renderers
entry points ----------------------------------------------------------> shared core
```

Transport-specific objects do not leak into profiles or renderers. Renderers do not
fetch evidence. Profiles cannot mutate normalized source facts. The CLI, Action, and
reusable workflow orchestrate these layers but do not implement a second interpretation
path.

## Architectural decision gates

The initial core is Python 3.11 through 3.13 and uses an installed `gh` command behind a
transport adapter. Distribution of the stable Action, adaptive log-fetch thresholds,
pattern engine, and watch polling policy remain evidence-dependent. Their defaults,
owners, and gates are recorded in
[decisions_and_open_questions.md](decisions_and_open_questions.md).

Check-run annotations are read evidence and do not justify write permissions. Portable
step/log association is treated as incomplete when GitHub cannot prove it. The versioned
`gh-run-receptor.events@1` producer format is an accepted optional contract, not a
requirement for generic reporting.
