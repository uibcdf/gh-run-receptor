---
summary: Secure inline Action rules and permission boundaries
issue: uibcdf/gh-run-receptor#23
status: open
opened: 2026-09-06
closed:
verification: asserted
area: ['github', 'security', 'profiles']
guard:
normative:
blocked_by: []
supersedes: []
---

# Securing inline Action rules and permission boundaries

**Reported:** 2026-09-06, after source-first report discovery closed the reporter identity
boundary but left Action-local customization and restricted-token behavior unverified.
**Status:** Open; the local implementation and focused regression suite pass, while the
hosted permission and caller-context evidence remains to be recorded.

## What

Complete the embedded Action vertical slice by accepting convenient workflow-local rules
without allowing pull-request content to choose the policy that evaluates itself. Make
reporter failure state machine-readable so minimum permissions can be tested without
rewriting the source workflow's conclusion.

## How

Add a multiline `rules` Action input containing exactly the existing bounded
`gh-run-receptor.config@1` document. Parse it with the current dependency-free parser and
feed it into the shared `build_report` rule-selection path; do not add another rule grammar
or interpretation implementation.

Inline rules are accepted only when GitHub-owned caller context proves all of these:

- the evaluated repository equals the workflow repository;
- `GITHUB_WORKFLOW_REF` identifies an immediate `.github/workflows/*.yml|yaml` file in that
  repository at `refs/heads/<default_branch>`;
- the current `GITHUB_REF` is that same default-branch ref;
- the default branch and event are present in GitHub context.

The composite Action passes these values from `${{ github.* }}` into private environment
names, preventing caller `env` from supplying the trust evidence. Pull-request merge refs,
tags, branches other than the default, cross-repository targets, missing context, malformed
rules, and oversized rules fail before evidence acquisition. Trusted inline configuration
records its kind, workflow path/ref, event, and SHA-256 digest in the ordinary report
configuration source.

Add scalar `report-ready` and `error-category` outputs. The former reflects whether a
canonical report exists; the latter is empty on success and contains a stable bounded
category such as `permission_denied`, `not_found_or_inaccessible`,
`untrusted_inline_rules`, or `invalid_configuration` on reporter failure. Default
fail-open behavior remains unchanged.

## Why

The repository-level configuration is secure but inconvenient for a small dedicated
reporter. Conversely, unrestricted inline input would let modified workflow content appear
to select its own assessment policy. Trusted caller provenance provides the compact YAML
mode requested by users while preserving the default-branch policy boundary.

Machine-readable failure outputs allow a hosted gate to remove `actions: read` or
`contents: read` deliberately and verify the observed result without scraping logs or
making a receptor failure fail the primary workflow.

## What is measured and what is assumed

Observed in GitHub's official documentation on 2026-09-06:

- `workflow_run` definitions must exist on the default branch and their jobs may receive
  secrets or write tokens even when the source workflow did not;
- fork pull-request workflows normally receive a read-only token without secrets;
- declaring any explicit `permissions` makes unspecified permissions `none`;
- `GITHUB_TOKEN` is repository-scoped and job-lifetime bounded.

No hosted permission or pull-request result is claimed until its run is recorded here.

## What was refuted

- A second compact JSON-only rule language was rejected because it would fork validation
  and user documentation from `config@1`.
- Trusting `rules` on every event was rejected because a pull request could change the
  workflow input used to evaluate itself.
- Trusting only the event name was rejected because `pull_request_target` and privileged
  `workflow_run` are safe only when the actual workflow definition and ref are checked.
- Accepting inline rules for another repository was rejected because the caller's trusted
  default branch has no authority over that repository's policy.
- Parsing Action logs to validate permission failure was rejected in favor of bounded
  scalar outputs.

## Scope and exclusions

This increment does not send secrets or write tokens to fork workflows, execute source
artifacts or code, mutate GitHub, define organization-wide policy, add arbitrary rule keys,
or claim private-fork behavior from a public same-repository test. Any live fork creation
is a separate external-state decision.

## Acceptance criteria

- Valid default-branch inline `config@1` selects the same profile and settings as an
  equivalent repository configuration.
- Inline source provenance is present in JSON and human output.
- PR, non-default ref, cross-repository, missing-context, malformed, and oversized cases
  fail before the report factory is called.
- Success outputs `report-ready=true` and an empty error category; failure outputs false
  and one bounded stable category.
- The canonical reporter demonstrates trusted inline rules with only `actions: read` and
  `contents: read`.
- A hosted restricted-permission gate records the actual category when required access is
  removed.
- Pull-request context is covered synthetically and, where safe, by a same-repository live
  PR; no fork claim is made without a fork run.
- Ruff lint, Ruff format, full receptor-formatted pytest, build, and devguide gates pass.

## Dependencies and risks

No tracked issue blocks the local implementation. Hosted permission responses can differ
between public and private repositories, so the release claim must name the tested
repository visibility and may remain narrower than the parser/trust contract.

## Provenance

Design sources are GitHub's official `workflow_run`, workflow syntax, repository Actions
settings, and `GITHUB_TOKEN` documentation as checked on 2026-09-06. Local and hosted
provenance will be appended during implementation.

The first local implementation reuses `parse_config`, `select_rule`, and `build_report`,
adds provenance to the ordinary configuration source, rejects untrusted or invalid input
before constructing the runner, and exposes stable Action outputs. Focused validation on
2026-09-06 passed Ruff lint and format plus 61 receptor-formatted tests covering embedded
execution, Action metadata, service delegation, and report equivalence. The same checkout
then passed the full 235-test receptor-formatted suite, Ruff lint and format, developer
report validation, and isolated wheel and source-distribution construction. Hosted gates
remain pending.
