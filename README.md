# gh-run-receptor

`gh-run-receptor` is a read-only GitHub Actions evidence receptor. It turns large,
repetitive run output into a compact, truth-preserving report while retaining a replayable
path to the captured evidence.

The project is in pre-1.0 development; no package has been published to a package index and
the public contract may still evolve. The `0.2.1` source release can inspect, watch, and
replay structured run evidence. Install the GitHub CLI extension at the exact preview tag:

```text
gh extension install uibcdf/gh-run-receptor --pin 0.2.1
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
with member-and-line provenance. `--profile=generic` disables auto-detection; an explicit
`--profile=conda` enables the Conda interpretation.

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
starting a change. Release behavior is summarized in [CHANGELOG.md](CHANGELOG.md).
