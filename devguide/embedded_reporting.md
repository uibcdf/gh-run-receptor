# Embedded reporting

## Purpose and limitation

The GitHub Action is an additional compact reporting channel. It cannot suppress or
rewrite output already produced by earlier steps. Its value is to leave a bounded final
summary that humans, agents, and the external CLI can inspect without replaying the full
run log.

The external CLI remains the universal interface. Embedded reporting is optional and
must not be required to interpret an ordinary GitHub Actions run.

## Integration forms

A step inside the run can inspect that run, but the authoritative run remains active
while the reporter executes. This convenience form therefore publishes `PENDING`; it is
useful for checking the integration, not for claiming a terminal run result:

```yaml
- name: Compact receptor report
  if: always()
  uses: uibcdf/gh-run-receptor@<full-commit-sha>
  with:
    profile: ci
```

A terminal run-wide report belongs in a downstream `workflow_run` workflow, where the
source run has already completed. The first composite Action accepts that completed run's
ID explicitly:

```yaml
on:
  workflow_run:
    workflows: [CI]
    types: [completed]

jobs:
  receptor-report:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
    steps:
      - uses: uibcdf/gh-run-receptor@<full-commit-sha>
        with:
          run-id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          profile: ci
```

The source workflow and reporter workflow are separate runs. The external CLI remains the
fallback when a downstream workflow is absent, skipped, cancelled, or lacks permission.
This exact pattern is live-tested by `gh-run-receptor-report.yml`: it grants only
`actions: read` and `contents: read`, checks out no source content, and verifies source ID
and conclusion parity independently of the Action.

## Action contract

The implemented preview Action accepts:

- `run-id`: explicit source run, defaulting to the active current run;
- `repository`: explicit source repository, defaulting to the current repository;
- `profile`: built-in or automatic interpretation profile;
- `capture`: `adaptive`, `full`, or `metadata`;
- `report-name`: safe artifact prefix, limited to 48 characters;
- `strict-reporter`: opt-in development behavior for treating reporter faults as errors.

Repository default-branch rules remain active through the shared capture path. Inline
rules and alternate configuration revisions are deferred until precedence and pull-request
trust behavior are specified and tested.

It emits:

- a short, bounded step log;
- Markdown in `GITHUB_STEP_SUMMARY`;
- a small `gh-run-receptor.report@1` JSON artifact;
- scalar outputs for assessment, failed groups, incomplete groups, and report artifact.

The Action appends the authoritative source run ID and attempt to `report-name`. The
default artifact for source run `123`, attempt `2`, is therefore
`gh-run-receptor-report-123-2`. This deterministic identity enables bounded repository
lookup and prevents a rerun from being confused with an older attempt.

The source-first CLI trusts only a configured exact reporter workflow path; the conventional
default is `.github/workflows/gh-run-receptor-report.yml`. Renaming that workflow requires
passing the same explicit path to `published-source`.

The implementation caps its JSON report at 8 MiB and its summary at 32 KiB, well below
GitHub's 1 MiB per-step summary limit. Large evidence remains in the private runner cache;
only the canonical report is uploaded.

## Failure semantics

By default the reporter is fail-open with respect to the product workflow: an internal
receptor error is shown as `RECEPTOR_ERROR`, but does not convert successful primary work
into a product failure. Source job failures remain failures. `strict-reporter` is for the
receptor's own tests and controlled adoption gates, not the default for downstream users.

The Action is read-only with respect to the source run. It does not rerun, cancel, approve,
publish, or deploy. Uploading its own report artifact is its explicit output contract.
Suggested commands are inert text and always identify their exact target.

## Permissions and untrusted input

The reusable reporter requests only read permissions needed for the selected evidence.
It must work with the caller's GitHub context and document limitations for forked pull
requests and restricted tokens. Inline rules and workflow logs are untrusted data; the
security constraints in [security.md](security.md) apply.

## Structured producer events

Workflows may upload `gh-run-receptor.events@1` JSON rather than forcing the receptor to
recover semantics from prose logs. Producer events are additive evidence. They retain a
source job, step, attempt, and artifact digest, and they cannot override official GitHub
conclusions.

## Cost model

The Action itself consumes runner time and artifact storage. The initial implementation
must measure this overhead and keep it bounded. A compact report is worthwhile only when
its generation and retrieval cost is materially lower than repeated full-log inspection.

## Distribution decision

The preview is a thin composite Action around the shared dependency-free Python source and
the hosted runner's `gh` command. A commit-pinned `setup-python` provides Python 3.13 and a
commit-pinned artifact action uploads the report. This avoids a second JavaScript model and
the Linux-only boundary of a container Action. The report records Action repository and ref
provenance, including an explicit `local` fallback for checkout-local validation. Stable
support still requires measured hosted-runner startup, artifact, and permission evidence.
