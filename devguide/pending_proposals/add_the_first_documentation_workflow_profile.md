---
summary: Add the first documentation workflow profile
issue: uibcdf/gh-run-receptor#8
status: open
opened: 2026-09-05
closed:
verification: asserted
area: ['profiles', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Adding the first documentation workflow profile

**Reported:** 2026-09-05, after the native/noarch Conda profile checkpoint.
**Status:** Open; implementation and client validation are in progress.

Remove `severity` for proposals. The directory identifies the report kind.

## What

Add `docs` as a truth-preserving profile for documentation builds, notebook execution,
link checks, warnings, diagnostic artifacts, and deployment. Validate it first against a
successful MolSysMT Sphinx/GitHub Pages run and a failing MolSysViewer notebook run.

## How

Preserve every normalized step, including successful and skipped steps, as an additive
optional `model@1` field with source references. Classify each step into exactly one bounded
presentation phase: `build_deploy`, `notebooks`, `links`, `warnings`, `artifact`, `deploy`,
`build`, `setup`, or `other`. A job without retained steps is classified as one fallback
unit, so expired step detail does not make the job disappear.

`build_deploy` is deliberate: when one GitHub step runs a composite Sphinx-to-GitHub-Pages
action, the source evidence cannot prove build and deployment independently. Only a
separate successful build unit plus a separate failed deployment unit derives `PARTIAL`;
the GitHub conclusion and exit code remain failures.

LLM failure output retains failed job and failed-step names, shows documentation-relevant
phase states, hides only successful `setup`/`other` counts, and keeps every unit in JSON.

## Why

Documentation is a release surface in MolSysMT and MolSysViewer. Generic failure output
does not state whether notebooks were executed, skipped, or preserved through a diagnostic
artifact; generic success cannot establish which combined action supplied build/deploy
evidence without exposing all setup steps.

## What is measured and what is assumed

Public MolSysViewer run `33930667142` has official conclusion `failure`. Environment setup
failed twice, notebook execution was skipped, and `notebook-failure-logs` remained as an
available artifact. Public MolSysMT run `31781220979` has official conclusion `success` and
one Sphinx-to-GitHub-Pages step that combines build and deployment.

Metadata was captured with `gh run-receptor ... inspect RUN_ID --capture metadata`; native
baselines combine a filtered `gh run view --json ... --jq ...` result with the run artifact
inventory. With tiktoken 0.13.0 `cl100k_base`:

| Case | Native baseline | First draft | Revised receptor | Reduction |
| --- | ---: | ---: | ---: | ---: |
| MolSysViewer notebook failure | 136 tokens | 149 tokens | 113 tokens | 16.9% |
| MolSysMT documentation success | 254 tokens | 48 tokens | 48 tokens | 81.1% |

The failed baseline retains every non-successful step, run URL, job state, and artifact
inventory. The successful baseline retains all steps because phase completion is the
question being verified.

## What was refuted

- Keeping only `failed_steps` is rejected because skipped notebooks and successful
  diagnostic-artifact collection are material to the failure interpretation.
- Assigning a combined Sphinx/Pages action independently to both build and deployment is
  rejected because one source conclusion cannot prove two independently reusable phases.
- Matching the bare word `build` is rejected after it classified `Additional info about
  the build` as content construction. Build matching now requires Sphinx, MkDocs, or an
  explicit content-generation phrase.
- The first failed renderer is rejected because its 149 tokens exceeded a competent
  136-token native baseline. Successful setup/other counts remain in JSON but leave the
  compact failure projection.

## Scope and exclusions

This slice does not parse Sphinx warnings or notebook logs, validate rendered pages, check
links itself, verify a deployed URL, define required phases, or implement release-profile
semantics. It does not split a composite action beyond the distinctions GitHub exposes.

## Acceptance criteria

- `docs` is accepted by CLI and trusted exact repository rules.
- Every retained step appears once in a phase; unknown steps remain under `other`.
- Complete step state and source references remain in JSON and validate against `model@1`.
- Unknown step statuses and conclusions remain visible in `unknowns`.
- Skipped notebooks and successful diagnostic-artifact collection survive failure
  compression.
- Combined build/deploy evidence remains combined.
- Only independently successful build plus failed deployment derives `PARTIAL`.
- Both real fixtures cross bundle, model, report, deterministic replay, and conclusion
  parity gates.
- Both measured LLM projections are shorter than their competent native baselines.
- MolSysMT and MolSysViewer adopt exact rules only after the implementing tag exists.

## Dependencies and risks

No external dependency blocks this slice. Step-name roles are presentation metadata and
therefore cannot rewrite official conclusions. Future required-phase enforcement needs
explicit repository settings and is excluded here.

## Provenance

Measured on 2026-09-05 on the local Linux development host with Python 3.13, GitHub CLI
2.93.0, and tiktoken 0.13.0. Source evidence is from public run attempt 1 of MolSysViewer
`33930667142` and MolSysMT `31781220979`; committed fixtures are reviewed metadata-only
reductions and remain replayable after GitHub retention expires.
