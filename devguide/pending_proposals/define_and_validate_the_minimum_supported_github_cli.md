---
summary: Define and validate the minimum supported GitHub CLI
issue: uibcdf/gh-run-receptor#25
status: active
opened: 2026-09-06
closed:
verification: asserted
area: ['github', 'cli', 'packaging']
guard:
normative:
blocked_by: []
supersedes: []
---

# Defining and validating the minimum supported GitHub CLI

**Reported:** 2026-09-06, while closing the remaining cross-cutting 1.0 distribution gate.
**Status:** Active; implementation and local gates pass, while the checksum-pinned hosted
minimum-version run remains pending.

## What

The runtime delegates authentication and transport to `gh`, but it neither declares nor
checks a minimum version. An older installation can therefore reach acquisition and fail
with an opaque unknown-option error when the client requests paginated JSON with
`gh api --paginate --slurp`.

## How

Define GitHub CLI 2.48.0 as the minimum functional transport. Before its first remote
request, each `GitHubClient` checks `gh --version` once, parses the stable first-line
semantic version, and rejects older or unrecognizable output with acquisition category
`unsupported_gh_cli`. Offline `replay`, local configuration commands, and other paths that
do not instantiate a remote request remain usable without `gh`.

Add a manual hosted workflow that downloads the official 2.48.0 archive, verifies the
published SHA-256 checksum, places only that binary first on `PATH`, installs the exact
gh-run-receptor tag as a GitHub CLI extension, and performs a real metadata inspection
that exercises pagination. A second synthetic boundary test uses 2.47.0 version output and
must fail before an API command is spawned.

The minimum means "the oldest version whose required interface we test", not "a currently
secure version recommended by GitHub". User documentation recommends the latest patched
stable GitHub CLI while guaranteeing a clear failure below 2.48.0.

## Why

The current unbounded dependency prevents users and release automation from knowing
whether a failure belongs to authentication, GitHub, or an incompatible transport. A
tested floor makes installation requirements actionable and closes a named 1.0 release
gap without adding an HTTP or credential dependency to the Python package.

## What is measured and what is assumed

Observed from official GitHub CLI sources on 2026-09-06:

- pull request `cli/cli#8620` introduced `--slurp` and merged at
  `2024-04-17T09:45:14Z` as `fd4f2c9c1f76cd66a26322ce640894a4f2deaff7`;
- release `v2.48.0` was published at `2024-04-17T10:04:56Z` and targets that exact commit;
- the current manual defines `--slurp` as the outer-array form used with `--paginate`;
- official 2.48.0 checksums identify the Linux amd64 archive as
  `1c477e2562aca8679b0219569f0482f1975de76daca8ba307892c1787338a28d`.

The development host runs Python 3.13.14 and GitHub CLI 2.93.0. No claim that 2.48.0 works
with the current receptor is made until the checksum-pinned hosted run completes.

## What was refuted

- "Any GitHub CLI 2.x" was rejected because `--slurp` did not exist throughout that line.
- Parsing unknown-option stderr after an API request was rejected because it misclassifies
  a deterministic local incompatibility as a remote acquisition failure.
- Reimplementing pagination in Python was rejected for this increment because it expands
  authentication, Link-header, retry, and enterprise-host responsibilities.
- Calling the minimum "recommended" was rejected because old functional releases may lack
  later GitHub CLI security fixes.

## Scope and exclusions

This work does not support GitHub CLI 1.x, declare GitHub Enterprise Server API
compatibility, vendor the `gh` binary, automatically upgrade user software, or promise
that GitHub upstream supports an old CLI. It validates the Linux amd64 minimum binary;
the existing hosted matrix continues to validate current runner-provided CLI behavior on
Ubuntu, macOS, and Windows.

## Acceptance criteria

- Version 2.47.0 and malformed output yield `unsupported_gh_cli` before any API command.
- Versions 2.48.0 and newer proceed and are checked only once per client.
- Missing `gh` retains a distinct executable/acquisition failure.
- Offline commands do not require or inspect GitHub CLI.
- The installed exact-tag extension completes a real metadata inspection through the
  checksum-pinned official 2.48.0 Linux amd64 binary.
- README, consumer guide, CLI help/error behavior, release contract, and checkpoint agree
  on the functional minimum and latest-patched recommendation.
- Ruff lint/format, full receptor-formatted pytest, build, devguide, and hosted gates pass.

## Dependencies and risks

No tracked dependency blocks the implementation. GitHub may eventually remove API
compatibility independently of the CLI interface; the hosted minimum gate detects that
external change and must not be silently weakened.

## Provenance

Official evidence is GitHub CLI pull request `cli/cli#8620`, release `v2.48.0`, its checksum
manifest, and the current `gh api` manual, inspected 2026-09-06. Local evidence comes from
Linux x86_64, Python 3.13.14, gh 2.93.0. Hosted run provenance will be appended.

The first implementation checks the CLI once per remote client, preserves missing-binary
failures separately, exposes the minimum in `--help`, and adds the hosted official-binary
workflow. Fifty focused receptor-formatted tests pass across the transport, CLI, and
workflow contracts; Ruff lint/format and developer-report validation also pass.
