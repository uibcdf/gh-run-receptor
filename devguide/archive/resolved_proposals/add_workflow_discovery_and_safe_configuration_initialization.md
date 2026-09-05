---
summary: Add workflow discovery and safe configuration initialization
issue: uibcdf/gh-run-receptor#10
status: resolved
opened: 2026-09-05
closed: 2026-09-05
verification: measured
area: ['cli', 'github', 'profiles']
guard: tests/test_discovery.py
normative:
blocked_by: []
supersedes: []
---

# Add workflow discovery and safe configuration initialization

**Reported:** 2026-09-05, while reviewing the next adoption milestone after the `0.7.0`
release-profile preview.
**Status:** Resolved in 0.8.0; the local, non-overwriting vertical slice passed the full
release gate and client-checkout validation.

## What

Repository adoption currently requires a maintainer to enumerate every workflow path and
choose every profile by hand. Add a top-level `init` command that discovers active local
workflow files and emits a deterministic, reviewable version 1 configuration proposal.

## How

The first slice scans only regular `.yml` and `.yaml` files immediately below
`.github/workflows/`; nested backup files are not active GitHub workflows and are ignored.
It reads a bounded amount of UTF-8 source as untrusted text and assigns `conda`, `docs`,
`release`, or `ci` only from conservative, documented signals. Ambiguous or unsupported
workflows remain `generic` rather than being omitted.

`gh run-receptor init [ROOT]` prints the proposed configuration to stdout. An explicit
`--write` writes `.github/gh-run-receptor.yaml` atomically, but refuses an existing target.
The initial command does not modify workflow YAML, contact GitHub, execute YAML, infer
required platforms, or silently replace human policy.

## Why

Both MolSysMT and MolSysViewer now use repository rules, but their 14-rule and 8-rule
files were assembled manually. Discovery reduces the cost and omission risk of adopting
the receptor in additional repositories while keeping every generated choice visible for
review. It is the largest missing item in the Phase 2 adoption path.

## What is measured and what is assumed

Observed on 2026-09-05 by listing the immediate workflow files and comparing them with
the two checked-in client configurations:

```text
rg --files ../molsysmt/.github/workflows ../molsysviewer/.github/workflows
cat ../molsysmt/.github/gh-run-receptor.yaml
cat ../molsysviewer/.github/gh-run-receptor.yaml
```

MolSysMT has active workflows plus a nested `backups/` directory, demonstrating why
discovery must follow GitHub's immediate-directory workflow rule rather than recurse.
The implementation discovered 15 immediate MolSysMT workflows and 8 immediate
MolSysViewer workflows. It reproduced every manually reviewed profile assignment and
also proposed MolSysMT's unconfigured `benchmarks.yml` as `ci`. Both generated documents
passed `config check`. On this Linux host, each preview took 0.11 seconds; output was 1,213
bytes with peak RSS 23,632 KiB for MolSysMT and 703 bytes with peak RSS 23,432 KiB for
MolSysViewer.

## What was refuted

- Loading workflow YAML with a general YAML dependency is rejected for the first slice:
  discovery needs bounded signals, not complete workflow evaluation, and the package has
  no runtime dependencies.
- Recursive discovery is rejected because nested files are not active GitHub workflows.
- Treating every `release:` trigger as a release profile is rejected: documentation and
  Conda publication workflows also use that trigger.
- Automatic `expected_platforms` generation is rejected because a platform mentioned in
  source is not proof that it is a required matrix member.
- Silent overwrite and generated edits to workflow files are rejected because `init`
  produces policy that maintainers must review.

## Scope and exclusions

This increment does not add remote repository discovery, organization policy, pattern
rules, arbitrary YAML parsing, workflow editing, interactive prompting, platform
requirements, or the embedded Action. It does not claim that a static profile suggestion
fully understands workflow success criteria.

## Acceptance criteria

- Discovery is deterministic, non-recursive, extension-bounded, size-bounded, and rejects
  symlinks and non-regular files.
- Every discovered workflow appears exactly once by exact repository-relative path.
- Known client workflows receive the expected initial profiles; ambiguous input remains
  `generic` with an explicit diagnostic.
- Generated configuration passes the existing strict parser and JSON Schema.
- Default execution writes nothing. `--write` creates the target atomically and refuses
  to replace an existing file.
- Errors and diagnostics are bounded and never include workflow contents.
- CLI help, consumer guidance, normative contracts, roadmap credit, and tests are updated.

## Dependencies and risks

There is no tracked blocker. The principal risk is false confidence in a static guess.
The mitigation is conservative fallback, visible per-workflow evidence in stderr, exact
paths in the generated document, and mandatory human review before commit.

## Provenance

Linux host, Python 3.13.14, gh-run-receptor source after tag `0.7.0`, 2026-09-05.
Measurement commands used `/usr/bin/time -f 'elapsed=%e max_rss_kib=%M'` around
`./gh-run-receptor init ../molsysmt` and `./gh-run-receptor init ../molsysviewer`, followed
by `./gh-run-receptor config check` on each captured stdout document.

The final local gate passed 130 tests, Ruff, developer-report validation, and
`git diff --check`. The release build and clean-wheel smoke test are recorded by the
0.8.0 release procedure.
