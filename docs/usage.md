# Command-line usage

## Inspect one run

Use a numeric ID with `--repo`, or pass a complete run URL:

```bash
gh run-receptor --repo OWNER/REPO inspect RUN_ID --receptor=llm

gh run-receptor inspect \
  https://github.com/OWNER/REPO/actions/runs/RUN_ID \
  --receptor=human
```

Text selects a reader independently from the data format:

| Option | Result |
| :--- | :--- |
| `--receptor=human` | Explanatory inventory for a terminal reader |
| `--receptor=llm` | Smaller decision-oriented report |
| `--format=json` | Versioned structured report, regardless of receptor |

When `--receptor` is absent, an interactive terminal selects `human`; redirected stdout
selects `llm`.

## Choose how much evidence to acquire

| Capture | Acquires | Typical use |
| :--- | :--- | :--- |
| `metadata` | Run, workflow, jobs, checks, artifacts, and eligible producer events | Fast status, coverage, artifact, and matrix questions |
| `adaptive` | Structured evidence; the complete attempt log archive only after GitHub confirms a completed conclusion other than `success` | Default for `inspect` and `watch` |
| `full` | Structured evidence and all retained job logs | Default for explicit `capture`; audit and parser development |

Capture controls evidence on disk, not terminal verbosity. A full bundle can still render
one compact line. Adaptive capture does not request logs for active or successful runs. A
completed run with an absent or unrecognized conclusion does request them because the
terminal result is unresolved. The decision is run-level; it does not claim that GitHub's
complete attempt archive contains only unsuccessful jobs.

## Watch without redrawing the tree

```bash
gh run-receptor --repo OWNER/REPO watch RUN_ID --receptor=llm
```

Transitions go to stderr. Unchanged snapshots are not printed. When the run becomes
terminal, stdout receives exactly one ordinary report.

## Capture and replay

```bash
gh run-receptor --repo OWNER/REPO capture RUN_ID \
  --capture full --output evidence

gh run-receptor replay evidence --profile=ci --receptor=llm
```

Bundles contain source identity, member digests, capture completeness, and warnings.
Replay validates the bundle before interpreting it; contradictory identity or a digest
mismatch is a receptor error.

## Compare two runs or attempts

```bash
gh run-receptor compare LEFT_BUNDLE RIGHT_BUNDLE --receptor=llm

gh run-receptor --repo OWNER/REPO compare LEFT_RUN RIGHT_RUN \
  --capture metadata --receptor=llm
```

Comparison preserves both source identities and describes job, duration, artifact, and
matrix changes. It does not adopt either run's conclusion. An optional strict
`comparison-policy@1` file can turn a specified regression into exit status 1.

## Aggregate several independent runs

```bash
gh run-receptor aggregate CI_BUNDLE DOCS_BUNDLE CONDA_BUNDLE --receptor=llm

gh run-receptor aggregate \
  https://github.com/OWNER/REPO/actions/runs/RUN_ID \
  https://github.com/OTHER/REPO/actions/runs/RUN_ID \
  --capture metadata --receptor=llm
```

An aggregate accepts two to fifty homogeneous sources: all local bundles or all remote
runs. It keeps each repository, workflow, attempt, commit, status, and conclusion separate.
A known failure wins over uncertainty; no collection-level GitHub conclusion is invented.

## Stable process statuses

| Code | Meaning |
| ---: | :--- |
| 0 | Complete success, or a complete descriptive operation such as comparison |
| 1 | Known GitHub failure or required policy/profile violation |
| 2 | Another terminal non-success such as cancelled, timed out, stale, or action required |
| 3 | Run still active |
| 4 | Evidence insufficient for the requested assertion |
| 5 | Acquisition, configuration, validation, normalization, or rendering error |
| 64 | Invalid command-line usage |
| 130 | User interruption |

`capture` returns 0 when the requested evidence policy was satisfied even if the captured
GitHub run failed. Automation that needs the run outcome should use `inspect` or `replay`.
Do not coerce statuses 2 through 5 into success.

## Native fallback

Use `gh run view` when the receptor returns `INCOMPLETE`, `UNKNOWN`, or `RECEPTOR_ERROR`,
or when the decision requires evidence outside the documented dimensions:

```bash
gh run view RUN_ID --repo OWNER/REPO \
  --json status,conclusion,jobs,artifacts,headSha,url
```
