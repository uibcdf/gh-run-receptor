---
summary: Deliver the first embedded GitHub Action vertical slice
issue: uibcdf/gh-run-receptor#17
status: active
opened: 2026-09-06
closed:
verification: inspected
area: ['github']
guard:
normative:
blocked_by: []
supersedes: []
---

# Deliver the first embedded GitHub Action vertical slice

**Reported:** 2026-09-06, after the external CLI reached a measured cross-platform package
gate while the embedded-Action roadmap phase still had no implementation credit.
**Status:** Active; the composite vertical slice passes its offline gate and awaits the
manual hosted-runner matrix.

## What

Ship a commit-pinnable root `action.yml` that invokes the existing Python capture,
normalization, profile, report, and rendering path. The Action publishes a bounded log and
job summary, scalar outputs, and a `gh-run-receptor.report@1` JSON artifact. It accepts an
explicit run ID so a `workflow_run` consumer can report a completed source run; the current
run ID is the convenience default and remains `PENDING` while the reporter itself runs.

## How

Use a thin composite Action for the measured first slice. A pinned `setup-python` action
provides Python 3.13, then an action-specific Python adapter imports the source at
`GITHUB_ACTION_PATH` and calls the shared core. The adapter writes files through Python so
the behavior is independent of Bash versus PowerShell syntax. It receives the automatically
created token only through `GH_TOKEN`, never as a command argument or report field.

The adapter owns only publication concerns: environment/input validation, summary
Markdown, `GITHUB_OUTPUT`, report destination, error presentation, and fail-open/strict
selection. It does not implement capture or profile logic. The composite action uploads
only the bounded JSON report through a commit-pinned `actions/upload-artifact` step.

Initial inputs are `run-id`, `repository`, `profile`, `capture`, `report-name`, and
`strict-reporter`. Repository default-branch configuration remains the trusted rules
source. Inline `rules` and alternate `config-path` stay outside this first slice until their
precedence and pull-request trust behavior have dedicated tests.

## Why

Phase 3 carries 15% of the 1.0 roadmap and currently contributes zero implementation
credit. A reusable publisher lets workflows leave a compact, structured result for later
agents without repeated log retrieval. Keeping it as an adapter around the tested core
prevents divergence between external and embedded truth.

## What is measured and what is assumed

GitHub's current metadata contract permits composite `runs.steps` to contain both `run`
and `uses` steps and maps composite outputs from step outputs. `github.action_path`,
`github.action_ref`, and `github.action_repository` are available in composite actions
when passed through `env`. Job summaries accept GitHub-flavored Markdown through the
per-step `GITHUB_STEP_SUMMARY` file and are bounded by GitHub at 1 MiB.

GitHub documents `workflow_run` conclusion as available to a downstream workflow after
the source workflow completes. By contrast, a reporting job inside its own source run is
necessarily still executing when it reads that run. Therefore terminal same-run reporting
is rejected as an unsupported truth claim; the Action must preserve the API's active state.

Cold start, artifact bytes, runtime, runner availability of GitHub CLI, and exact behavior
on the three hosted operating systems remain unmeasured until the live matrix runs.

## Implementation progress

The root `action.yml` now wraps a factored capture/report service instead of invoking the
CLI or duplicating its interpretation path. The Python adapter validates bounded inputs,
keeps the token in the environment, escapes summaries, publishes scalar outputs, writes an
8 MiB-capped report and records Action-source provenance. All external Actions are pinned
to full commit SHAs. Offline tests cover success, source failure, active state, reporter
failure, hostile diagnostics, unsafe names, oversize output, local provenance fallback,
metadata syntax, and the manual validation workflow contract.

The manual workflow will next validate the checkout-local Action and script extension on
Ubuntu, macOS, and Windows against retained successful and failed runs and its own active
run. No cross-platform or timing claim is made until that run completes.

## What was refuted

- A separately implemented JavaScript reporter is rejected for the first slice because it
  would duplicate the Python model and renderer before a shared generated contract exists.
- A Docker Action is rejected as the universal form because container actions do not
  provide the required native macOS and Windows path.
- Calling a current-run final job `PASS` is rejected because the authoritative run is still
  active while that job executes.
- Swallowing all reporter failures inside Python is rejected because it makes
  `strict-reporter` impossible to test. The composite step chooses fail-open versus strict.
- Inline executable rules and pull-request-head configuration are rejected by the existing
  trust model.

## Scope and exclusions

This slice does not yet publish a stable `v1` major tag, an Action Marketplace listing,
inline rules, alternate trusted revisions, the reusable `workflow_run` template, standalone
binaries, or a JavaScript rewrite. Artifact upload is an explicit report emission; rerun,
cancel, approval, deployment, and product artifact mutation remain out of scope.

## Acceptance criteria

- `action.yml` has bounded documented inputs and outputs and pins every external action to
  a full commit SHA.
- The adapter emits the existing canonical report JSON and derives every scalar and summary
  from that same report.
- Reporter errors write one bounded `RECEPTOR_ERROR` summary and succeed by default; strict
  mode returns a nonzero step result.
- Tokens and untrusted controls never enter outputs, summaries, or command arguments.
- A completed-run invocation preserves exact GitHub conclusion and receptor exit semantics.
- A current-run invocation remains `PENDING` rather than inventing a terminal conclusion.
- Linux, macOS, and Windows live jobs measure startup duration and report artifact size.
- The external CLI continues to pass its full local and cross-platform gates unchanged.

## Dependencies and risks

There is no tracked blocker. The composite approach depends on hosted-runner Python setup,
an installed GitHub CLI transport, package-index access for setup-python itself, and Actions
artifact service availability. The first live run must distinguish source incompatibility
from runner or service failure. Source-action version provenance also needs an explicit
fallback when a downloaded action directory has no Git metadata.

## Provenance

Design inspection on Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.11.0,
2026-09-06. Upstream behavior was checked against GitHub's official metadata syntax,
contexts, workflow commands, and workflow event documentation.
