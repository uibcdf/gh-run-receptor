# Embedded reporting

## Purpose and limitation

The GitHub Action is an additional compact reporting channel. It cannot suppress or
rewrite output already produced by earlier steps. Its value is to leave a bounded final
summary that humans, agents, and the external CLI can inspect without replaying the full
run log.

The external CLI remains the universal interface. Embedded reporting is optional and
must not be required to interpret an ordinary GitHub Actions run.

## Integration forms

A step inside one job can summarize only evidence visible to that job. It is suitable
for a self-contained producer:

```yaml
- name: Compact receptor report
  if: always()
  uses: uibcdf/gh-run-receptor@v1
  with:
    profile: ci
```

A run-wide report belongs in a final job or reusable workflow. GitHub Actions has no
wildcard for `needs`, so every primary job must be listed explicitly:

```yaml
receptor-report:
  if: always()
  needs: [lint, test, build]
  permissions:
    actions: read
    checks: read
    contents: read
  uses: uibcdf/gh-run-receptor/.github/workflows/report.yaml@v1
  with:
    profile: ci
```

The reporter excludes its own job from evaluation. Cancellation may prevent the final
job from running; the external CLI is the fallback for cancelled or interrupted runs.

## Action contract

The first stable Action should accept these concepts, whether their final input names are
identical or not:

- `profile`: built-in or repository-defined interpretation profile;
- `rules`: optional small inline YAML document;
- `config-path`: repository configuration path;
- `capture`: `adaptive`, `full`, or `metadata`;
- `report-name`: artifact and summary label;
- `strict-reporter`: opt-in development behavior for treating reporter faults as errors.

It emits:

- a short, bounded step log;
- Markdown in `GITHUB_STEP_SUMMARY`;
- a small `gh-run-receptor.report@1` JSON artifact;
- scalar outputs for assessment, failed groups, incomplete groups, and report artifact.

The summary must stay well below GitHub's 1 MiB per-step summary limit. Large evidence is
stored in an artifact and referenced by identity; it is not pasted into the summary.

## Failure semantics

By default the reporter is fail-open with respect to the product workflow: an internal
receptor error is shown as `RECEPTOR_ERROR`, but does not convert successful primary work
into a product failure. Source job failures remain failures. `strict-reporter` is for the
receptor's own tests and controlled adoption gates, not the default for downstream users.

The Action is read-only. It does not rerun, cancel, approve, upload, publish, or deploy.
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

## Distribution decision gate

The CLI prototype targets Python 3.11 through 3.13 and delegates authentication and HTTP
transport to the installed `gh` command. Before the first stable Action, the project must
choose and record one reproducible distribution strategy: bundled JavaScript, a packaged
Python runtime, or a thin composite Action around an installed executable. The decision
must account for cold-start time, supply-chain surface, cross-platform support, release
automation, and version pinning. It is intentionally not guessed during Phase 0.
