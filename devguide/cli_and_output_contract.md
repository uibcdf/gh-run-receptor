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

The MVP accepts `--interval`, `--max-interval`, `--attempt`, and the final capture policy.
It polls only run and paginated job metadata until terminal state, emits transitions to
stderr, retries at most two consecutive transient acquisition failures, and performs one
ordinary capture/report operation after completion. An already completed run skips the
initial snapshot and transitions. Cancellation by the user returns 130. Live active-run
behavior remains unclaimed until observed outside the simulated clock suite.

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

The current interface implements `init [ROOT] [--write]`, `config check [PATH]`, and
`config explain WORKFLOW_PATH [--config PATH]`. `init` discovers only immediate local
workflow files and prints a deterministic proposal by default. `--write` atomically
creates the default configuration and refuses an existing target. `check` validates the
strict version 1 subset, duplicate identities, and bounds. `explain` shows the winning
exact rule and active settings. Pattern analysis, remote discovery, and a full override
trace remain future work.

## Output channels

- **stdout** contains one bounded report and is the machine/agent-facing channel.
- **stderr** contains transition-only liveness, warnings about degraded evidence, and
  debug diagnostics when requested.
- **exit status** communicates command execution and authoritative run outcome.
- **bundle/report files** retain detail not printed to stdout.

Raw logs are never printed automatically. `--debug` does not change this rule.

Human text includes explanatory labels, all jobs up to a documented bound, failed steps,
and artifact details. LLM text includes the verdict, compact job counts, non-success jobs and
steps, a bounded artifact inventory, warnings, and the run link. Both are projections of
the same report and return the same exit status.

A collection is labelled `failed jobs` only when every selected job has GitHub conclusion
`failure`; cancelled or mixed collections use `non-success jobs`. The heading never
rewrites cancellation, timeout, or an unknown future conclusion as failure.

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
| `FAIL` | GitHub reports failure or a required expectation failed without a separately evidenced completed phase that the selected profile defines as partial progress |
| `PARTIAL` | GitHub is unsuccessful, but the profile identifies a meaningful completed phase separately from the failed or skipped phase; a profile may impose stronger reuse requirements |
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

Acquisition failures use one bounded stderr line while keeping exit status 5:

```text
RECEPTOR_ERROR category=permission_denied: GitHub CLI request failed: ... (HTTP 403)
```

Stable acquisition categories are `authentication_required`, `authentication_failed`,
`permission_denied`, `not_found_or_inaccessible`, `rate_limited`, and
`acquisition_failed`. The last category is the conservative fallback. A 404 category does
not distinguish a nonexistent public resource from a private resource hidden by GitHub.
Configuration, bundle, normalization, and rendering errors retain the uncategorized
`RECEPTOR_ERROR: ...` form.

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
