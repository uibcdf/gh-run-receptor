# Product and scope

## Problem

GitHub Actions exposes rich execution evidence, but its default terminal and log views
are optimized for a human browsing interactively. Coding agents often receive repeated
status snapshots or tens of thousands of tokens of logs when the actionable result fits
in a few lines. Generic filtering helps, but it does not understand whether a workflow
is testing code, deploying documentation, publishing Conda packages, or verifying a
release.

`gh-run-receptor` turns that evidence into a compact, truth-preserving report for coding
agents and humans. It groups repeated causes, preserves partial success, identifies the
smallest useful rerun target, and retains a path back to the complete evidence.

## Intended users

- Coding agents operating through GitHub CLI.
- Developers diagnosing matrix workflows from a terminal.
- Maintainers coordinating multi-platform builds and releases.
- Workflow authors who want to publish a compact, machine-readable report directly from
  a run.

## Delivery modes

### External CLI

The universal mode inspects any accessible run without requiring changes to its
workflow. It also captures evidence and replays saved bundles offline.

```text
gh run-receptor inspect RUN_ID
gh run-receptor replay PATH
```

Text rendering selects a receptor: `human` provides a labeled, explanatory inventory;
`llm` provides a much smaller decision-oriented report. The default is inferred from
whether stdout is an interactive terminal. JSON is a structured format rather than a
reader profile. Native GitHub output is still obtained directly with `gh run view`.

### GitHub Action

An optional action publishes a compact per-job or run report. Rules can be supplied as
action inputs, including a multiline declarative rules document. This provides a small
report artifact and job summary but does not remove logs emitted by earlier steps.

### Reusable reporting workflow

An optional final job depends on the primary jobs and aggregates a complete matrix. It
uses the same core as the CLI and action. This is the preferred embedded mode for Conda,
documentation deployment, and release workflows.

## Product principles

1. **Truth before compression.** An incomplete, cancelled, or unsuccessful run is never
   reported as successful.
2. **Evidence before interpretation.** Raw API responses and logs remain available even
   when stdout is compact.
3. **Structured data before log scraping.** Run, job, step, check, and artifact metadata
   take precedence over matching text in logs.
4. **Root cause before occurrence count.** Repeated matrix failures should be grouped
   when their evidence supports a shared cause.
5. **Read-only by default.** Suggested rerun commands are output; they are not executed.
6. **Safe degradation.** An unknown workflow or broken profile falls back to the generic
   report rather than hiding evidence or altering the workflow result.
7. **Bounded output.** Output size is bounded by distinct causes and decisions, not by
   the number of log lines.

## Initial non-goals

- Replacing GitHub Actions or its authoritative conclusions.
- Proving scientific correctness from favorable log text.
- Suppressing output produced by unrelated workflow steps.
- Executing user-supplied code from a rules file.
- Automatically rerunning, cancelling, approving, uploading, or deploying.
- Providing a general-purpose log analytics platform.

## Success criteria

- At least a 90% output-token reduction against an honestly filtered GitHub CLI
  baseline on the selected corpus.
- Exact parity with GitHub run and job conclusions.
- Deterministic replay of a captured evidence bundle.
- Useful generic fallback for every accessible workflow.
- Validated built-in profiles for CI, documentation, Conda, and release workflows.
- No unbounded output, credential disclosure, or forged verdict through untrusted log
  content.
