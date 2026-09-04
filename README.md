# gh-run-receptor

`gh-run-receptor` is a planned read-only GitHub Actions evidence receptor. It will turn
large, repetitive run output into a compact, truth-preserving report while retaining a
replayable path to the complete evidence.

The project is currently in design and feasibility work; no usable implementation has
been released. An initial source-tree MVP can already inspect and replay structured run
evidence:

```text
PYTHONPATH=src python -m gh_run_receptor --repo OWNER/REPO \
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

The root `gh-run-receptor` launcher also satisfies the GitHub CLI extension naming
contract. Until a release is published, a local checkout can be exercised directly with
`./gh-run-receptor --help`; installation instructions will be finalized with the first
published artifact.

Product contracts, contributor onboarding, security boundaries, open decisions, and the
implementation route are maintained in the
[developer guide](devguide/README.md). See [CONTRIBUTING.md](CONTRIBUTING.md) before
starting a change. Unreleased behavior is summarized in [CHANGELOG.md](CHANGELOG.md).
