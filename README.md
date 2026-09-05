# gh-run-receptor

`gh-run-receptor` is a read-only GitHub Actions evidence receptor. It turns large,
repetitive run output into a compact, truth-preserving report while retaining a replayable
path to the captured evidence.

The project is in pre-1.0 development; no package has been published to a package index and
the public contract may still evolve. The `0.6.1` source release can inspect, watch, and
replay structured run evidence. Install the GitHub CLI extension at the exact preview tag:

```text
gh extension install uibcdf/gh-run-receptor --pin 0.6.1
gh run-receptor --version
```

A pinned script extension intentionally stays on that revision. To move an existing pinned
installation to a later tag, remove it and install again with the new `--pin` value.

Then inspect a run:

```text
gh run-receptor --repo OWNER/REPO \
  --receptor=llm inspect RUN_ID --capture metadata
```

Use `--receptor=human` for an explanatory terminal report. When omitted, the command
selects `human` for an interactive terminal and `llm` when stdout is redirected. Use
`--format=json` for the versioned structured report; JSON is a format, not a receptor.
The ordinary native GitHub presentation remains available through `gh run view`.

The current MVP recognizes clear Conda matrices automatically. When failure logs were
captured, it reports independently reusable platform artifacts and groups repeated causes
with member-and-line provenance. The `ci` profile groups jobs into presentation roles and
collapses repeated failed-step signatures without removing any job from JSON. The `docs`
profile distinguishes setup, content, notebooks, links, artifacts, and deployment while
keeping combined source evidence combined. Use `--profile=generic`, `--profile=ci`,
`--profile=conda`, or `--profile=docs` to select explicitly.

A client repository can assign those profiles, declare required native Conda platforms,
or identify a noarch package in a trusted `.github/gh-run-receptor.yaml` file:

```yaml
schema_version: 1
workflows:
  - match:
      path: .github/workflows/build_conda.yaml
    profile: conda
    settings:
      expected_platforms: [linux-64, osx-arm64, win-64]

  - match:
      path: .github/workflows/build_noarch_conda.yaml
    profile: conda
    settings:
      package_kind: noarch

  - match:
      path: .github/workflows/docs-notebooks.yaml
    profile: docs
```

Validate and explain the rule locally before committing it:

```text
gh run-receptor config check
gh run-receptor config explain .github/workflows/build_conda.yaml
```

Live capture reads policy only from the repository's default branch, stores its revision
and digest in the evidence bundle, and fails if required platforms are absent. Version
`0.6.1` accepts exact path, numeric ID, or display-name matches; it deliberately rejects
patterns and unknown settings rather than silently ignoring them.

## Measured token reduction

The first benchmark uses public MolSysMT Conda runs and compares against a competent
filtered native workflow, not against deliberately dumping every log line:

| Question | Native baseline | Receptor | Reduction (`cl100k_base`) |
| --- | ---: | ---: | ---: |
| Diagnose a partial five-platform failure | 5,138 tokens | 296 tokens | 94.2% |
| Verify a successful five-platform matrix | 143 tokens | 39 tokens | 72.7% |
| Diagnose seven failed MolSysViewer CI jobs | 223 tokens | 198 tokens | 11.2% |
| Verify a successful MolSysViewer noarch workflow | 101 tokens | 45 tokens | 55.4% |
| Diagnose a failed MolSysViewer notebook workflow | 136 tokens | 113 tokens | 16.9% |
| Verify a successful MolSysMT documentation workflow | 254 tokens | 48 tokens | 81.1% |

For the failed run, the receptor retained the official failure, identified both failed
macOS jobs, and reported the Linux, Linux ARM, and Windows artifacts as reusable. These are
case measurements, not a general savings rate; see the
[commands, tokenizer comparison, and limitations](devguide/benchmark_2026-09-04.md).

If the only question is whether one completed run succeeded, native GitHub JSON is already
smaller in the measured green case: 10 tokens versus the receptor's 39. Use the receptor
when job, platform, artifact, failure, or evidence completeness matters—not to replace an
already minimal status query.

The CI measurement uses an already filtered native JSON baseline and therefore shows a
modest saving. The receptor additionally retains CI role counts, artifact state, run URL,
and a replayable bundle. Its first ungrouped implementation was larger than the baseline
and was rejected before release.

The noarch measurement combines a filtered native run/jobs query with the current GitHub
artifact inventory. `not_observed` describes that inventory only; it does not claim that
an artifact never existed or that the Conda channel was or was not updated.

Long-running workflows can be observed without redrawing their complete job tree:

```text
gh-run-receptor watch RUN_ID --repo OWNER/REPO --receptor=llm
```

`watch` sends one initial progress line and only subsequent job/run transitions to stderr.
When the run completes, stdout receives exactly one ordinary adaptive report. Calling it
on an already completed successful run produces only the one-line final report.

The root `gh-run-receptor` launcher satisfies the GitHub CLI script-extension naming
contract. A local checkout can also be installed with `gh extension install .` or exercised
directly with `./gh-run-receptor --help`. The tag installs source; Python-index and binary
artifacts remain future distribution modes.

Product contracts, contributor onboarding, security boundaries, open decisions, and the
implementation route are maintained in the
[developer guide](devguide/README.md). See [CONTRIBUTING.md](CONTRIBUTING.md) before
starting a change. Libraries and workflow repositories adopting the tool should use the
[canonical consumer guide](standards/GH_RUN_RECEPTOR_GUIDE.md). Release behavior is
summarized in [CHANGELOG.md](CHANGELOG.md).
