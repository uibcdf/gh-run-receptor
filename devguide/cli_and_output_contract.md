# CLI and output contract

## Invocation

The repository is intended to provide both a normal console command and a GitHub CLI
extension entry point:

```text
gh-run-receptor COMMAND ...
gh run-receptor COMMAND ...
```

Both entry points call the same application and produce identical output. The Phase 1
prototype requires Python 3.11--3.13 and an authenticated GitHub CLI for networked
commands. `replay`, config validation, normalization, and rendering do not require
network access.

## Global options

The preliminary global interface is:

```text
--repo OWNER/REPO       repository when it cannot be inferred
--hostname HOST         GitHub hostname, initially github.com
--receptor human|llm    intended text reader; inferred from stdout when omitted
--format text|json      output encoding; default text
--profile NAME          explicit profile, bypassing profile autodetection
--config PATH           explicit trusted configuration path
--cache-dir PATH        evidence-cache location
--no-color              disable presentation color
--debug                 diagnostics to stderr; never credentials or raw headers
```

Environment variables may provide non-secret defaults. Command arguments take
precedence. Authentication tokens are not accepted as ordinary command-line options;
GitHub CLI owns authentication.

Common options are accepted before or after the subcommand. This makes both
`--receptor=llm inspect RUN_ID` and `inspect RUN_ID --receptor=llm` valid without changing
precedence.

For text output, the inferred receptor is `human` when stdout is a terminal and `llm`
otherwise. An explicit `--receptor` always wins. `--format=json` serializes the shared
report and does not change facts according to the selected receptor. `human` is a receptor
report, not passthrough output; users who want GitHub CLI's native presentation invoke
`gh run view` directly.

## Commands

### `inspect`

```text
gh run-receptor inspect RUN_OR_URL [--attempt N]
    [--capture full|adaptive|metadata]
```

Resolves the run, captures or reuses evidence, normalizes it, applies one profile, and
renders the report. The development capture default is `full`; the intended stable
default is `adaptive`.

### `capture`

```text
gh run-receptor capture RUN_OR_URL [--attempt N]
    [--capture full|adaptive|metadata] [--output PATH]
```

Creates or refreshes an evidence bundle without requiring profile interpretation. It
prints only the bundle identity, completeness, size, and path.

### `replay`

```text
gh run-receptor replay BUNDLE [--profile NAME]
```

Validates the manifest and digests, then renders without network access. Replay never
silently fills missing evidence from GitHub. A separate explicit recapture is required.

### `list`

```text
gh run-receptor list [--workflow ID_OR_FILE] [--branch REF]
    [--commit SHA] [--event EVENT] [--status STATUS]
    [--actor LOGIN] [--since TIME] [--limit N]
```

Pushes supported filters to GitHub and returns a bounded run table. It does not fetch
logs or artifact contents.

### `watch`

```text
gh run-receptor watch RUN_OR_URL [--interval SECONDS]
```

Prints the initial compact state, then only transitions: job started, job completed,
new failure, run completed, or evidence acquisition degraded. It never redraws the
whole status tree. Polling backs off for long unchanged intervals. A final report is
rendered once.

### `compare`

```text
gh run-receptor compare LEFT RIGHT
gh run-receptor compare RUN_ID --attempt LEFT --attempt RIGHT
```

Compares conclusions, matrix coverage, durations, artifact inventory and size, and
profile metrics. It never treats runs from different commits as equivalent without
showing the commit difference.

### Configuration commands

```text
gh run-receptor init
gh run-receptor config check [PATH]
gh run-receptor config explain RUN_OR_WORKFLOW
```

`init` proposes but does not silently write configuration. `check` validates schema,
overlaps, unused values, patterns, and trust policy. `explain` shows profile selection,
configuration sources, precedence, and every applied override.

## Output channels

- **stdout** contains one bounded report and is the machine/agent-facing channel.
- **stderr** contains transition-only liveness, warnings about degraded evidence, and
  debug diagnostics when requested.
- **exit status** communicates command execution and authoritative run outcome.
- **bundle/report files** retain detail not printed to stdout.

Raw logs are never printed automatically. `--debug` does not change this rule.

Human text includes explanatory labels, all jobs up to a documented bound, failed steps,
and artifact details. LLM text includes the verdict, compact job counts, failed jobs and
steps, a bounded artifact inventory, warnings, and the run link. Both are projections of
the same report and return the same exit status.

A complete successful LLM report collapses to one line containing conclusion, profile,
job and platform coverage where available, artifact count, repository, and run ID. Human
and JSON output retain the full inventory. If requested evidence is incomplete, the
assessment is `INCOMPLETE`, never `PASS`, even though the separate GitHub conclusion may
be `success`.

## Official facts and receptor assessment

Every report carries two distinct layers:

```text
GitHub: status=completed conclusion=failure
Receptor: assessment=PARTIAL evidence=complete
```

The first layer is copied from GitHub. The assessment adds workflow meaning but cannot
replace or soften the official conclusion.

## Assessments

| Assessment | Meaning |
| --- | --- |
| `PASS` | GitHub reports successful completion and every configured required expectation is satisfied |
| `FAIL` | GitHub reports failure or a required expectation failed without independently reusable successes worth elevating |
| `PARTIAL` | GitHub is unsuccessful, but the profile identifies completed, independently reusable work alongside the failure |
| `PENDING` | The run or required jobs have not reached a terminal state |
| `CANCELLED` | GitHub reports cancellation |
| `TIMED_OUT` | GitHub reports timeout |
| `ACTION_REQUIRED` | GitHub requires approval or another external action |
| `STALE` | GitHub reports stale work |
| `INCOMPLETE` | The run or capture lacks evidence required for the requested assertion |
| `UNKNOWN` | A source value or workflow shape is unsupported and cannot be classified conservatively |
| `RECEPTOR_ERROR` | Acquisition, normalization, profile, or rendering failed |

`PARTIAL` is not success. The header always retains `conclusion=failure` or the relevant
official conclusion.

## Exit codes

The preliminary exit-code contract separates run outcome from receptor failure:

| Code | Meaning |
| ---: | --- |
| 0 | Completed GitHub success and successful receptor processing |
| 1 | Completed GitHub failure or required profile expectation failure |
| 2 | Cancelled, timed out, stale, action required, or otherwise non-success terminal run |
| 3 | Run still pending or in progress |
| 4 | Evidence incomplete for the requested operation |
| 5 | Receptor acquisition, configuration, normalization, or rendering error |
| 64 | CLI usage error |

`capture` returns zero when the requested capture policy is satisfied even if the
captured GitHub run failed; its purpose is evidence acquisition. `replay` and `inspect`
follow the table. Final numeric values remain provisional until Phase 1 truth-table
tests validate composition with shell and agent workflows.

## Compact rendering

A successful matrix example:

```text
PASS conclusion=success | Conda | 5/5 platforms | 5 artifacts | 15 ABI checks
slowest: osx-64 8m42s | artifacts: 263.1 MiB
evidence: ~/.cache/gh-run-receptor/github.com/uibcdf/molsysmt/33863426589/1/adaptive
```

A partial example:

```text
PARTIAL conclusion=failure | Conda | 4/5 platforms reusable | 1 root cause

[1] win-64 | publication | duplicate package
    build: passed | ABI3: 3/3 passed | upload: failed
    job: 987654 | evidence: logs/win-64.txt:418
    rerun: gh run rerun 123456 --job 987654
```

The report includes at most ten fully expanded distinct causes by default. Remaining
causes are counted and remain available in the JSON report and bundle. Occurrence lists
show a small deterministic sample plus the remaining count. Exact initial limits are
validated by the corpus benchmark before becoming stable API.

## Determinism

- Sort jobs by a stable matrix/job identity, not completion order.
- Sort cause groups by severity, earliest causal source, and stable identity.
- Normalize path separators in portable output.
- Do not place capture time, temporary directory names, or signed URLs in deterministic
  report content unless explicitly requested.
- JSON uses a canonical key order and documented timestamp representation.

## Suggested commands

Suggested commands are inert text. They include the repository when the current working
directory may not resolve it and use the database job ID required by GitHub CLI. A
suggestion is emitted only when evidence identifies a valid target. The receptor never
executes it in the read-only product.
