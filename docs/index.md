# gh-run-receptor

A GitHub Actions evidence receptor for coding agents: compact reports without hiding
failures or uncertainty.

GitHub Actions already has the source facts. `gh-run-receptor` acquires those facts through
GitHub CLI, keeps a replayable evidence bundle, and renders only the bounded result needed
by a human, an agent, or another tool. It never changes the workflow run.

```{note}
Version 1.0 is the stable read-only evidence contract, with exact workflow identities and
no pattern or organization-level configuration. Pin the exact `1.1.0` release and read
[Compatibility and contracts](contracts.md) before depending on a serialized boundary.
```

```{toctree}
---
maxdepth: 1
hidden:
---
installation
usage
profiles
embedded-reporting
configuration
contracts
security
limitations
benchmarks
```

## Where to go

| If you want to… | Read |
| :--- | :--- |
| Install the exact release | [Installation](installation.md) |
| Inspect, watch, capture, replay, compare, or aggregate runs | [Command-line usage](usage.md) |
| Choose `generic`, `ci`, `conda`, `docs`, or `release` | [Profiles](profiles.md) |
| Add the Action or reusable reporter to a repository | [Embedded reporting](embedded-reporting.md) |
| Define trusted workflow-specific rules | [Configuration](configuration.md) |
| Consume JSON, bundles, producer events, or exit statuses | [Compatibility and contracts](contracts.md) |
| Review permissions and trust boundaries | [Security](security.md) |
| Know what is not claimed | [Limitations](limitations.md) |
| See measured token costs | [Benchmarks](benchmarks.md) |

## In thirty seconds

Install the exact GitHub CLI extension release:

```console
$ gh extension install uibcdf/gh-run-receptor --pin 1.1.0
$ gh run-receptor --version
1.1.0
```

Then inspect a completed run:

```console
$ gh run-receptor --repo OWNER/REPO --receptor=llm inspect RUN_ID --capture metadata
PASS conclusion=success | profile=ci | roles=test:3 | jobs=3/3 | artifacts=1 | OWNER/REPO run=RUN_ID
```

`PASS` is the receptor assessment. `conclusion=success` is GitHub's authoritative source
fact. Both remain visible. If required evidence is missing, the receptor reports
`INCOMPLETE`; it does not turn uncertainty into success.

## What makes it different

- **Truth before compression:** GitHub status and conclusion are never rewritten.
- **Evidence before interpretation:** structured API evidence remains replayable on disk.
- **Bounded output:** job matrices and repeated causes cannot expand stdout without limit.
- **Read-only operation:** inspection never reruns, cancels, approves, uploads, or deploys.
- **One core:** CLI, composite Action, and reusable workflow share the same model and
  renderers.

Use native `gh run view` whenever a minimal GitHub query already answers the question or
when the receptor reports evidence outside its current scope.
