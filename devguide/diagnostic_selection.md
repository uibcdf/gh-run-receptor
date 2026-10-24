# Bounded diagnostic selection

The reusable `gh_run_receptor.logs.extract_causes(archive, failed_jobs)` operation
selects one diagnostic per GitHub-failed job, groups equal normalized messages
and returns bounded warnings when evidence is unavailable. Profiles, CLI,
Action and reusable workflow share it through the report builder. This is a
heuristic over untrusted logs, never proof of an underlying root cause or a
replacement for API run/job/step status, conclusion, completeness or exit rules.

## Recognition and precedence

- A failed pytest-receptor verdict can introduce a typed group within 128 physical
  lines. A group requires its header, Python source location and matching terminal
  exception type. It outranks generic stderr and earlier tolerated installation
  warnings. A summary frame-chain line cannot replace its primary source location.
  The diagnostic retains the existing 500-character redacted message bound. Its
  primary frame is also kept separately, so compact text clipping cannot hide
  that location or shorten the grouping signature to the display prefix. An incomplete/unrecognized group
  falls back to existing failed-test/rerun, traceback or generic diagnostics.
- Printed `rerun: pytest`, `rerun: uv run pytest` and `rerun: python -m pytest`
  node identifiers are read as text only. A multi-module rerun is not invented
  into an individual test. Explicit `tests:` entries retain at most two original
  failed-test identifiers and their separate source locators, beside the primary
  frame and its own original log line.
- A bounded libmamba failure block accepts both direct `does not exist` and
  `, which does not exist` constraint forms. Its existing four-package/128-line
  bounds remain. This is selected-channel evidence, not global package absence.
- An anchored nonzero `curl: (N)` diagnostic outranks a later missing-file error.
  Its actual message is preserved; no TLS alert is converted into a certificate,
  server-side or signature diagnosis.
- An explicit `<tool> rejected: ...` or existing structured non-success verdict
  can precede a generic nonzero runner exit across at most two empty lines.
  Ordinary output, positive PASS text, or a more distant diagnostic does not
  acquire that association.

Only the best candidate per recognized kind is retained during streaming;
candidate storage is bounded independently of log line count. Existing ZIP,
expanded-byte, member and line limits remain unchanged. Unknown diagnostics
remain in the original archive and cannot make unsuccessful work pass.

## Additive report context

A cause occurrence may carry `context`, using the existing open occurrence
extension point in `report@1`. There are at most three entries, each with
`member`, positive `line`, `kind` and redacted/bounded `message`. Known kinds are
`frame`, `test` and `later diagnostic`. At most one primary frame accompanies a typed pytest failure. One later missing-file diagnostic within
128 lines accompanies a download/solver primary; chronological context does not
assert a verified causal relationship. Every occurrence keeps its own locators
in JSON. Human/LLM output shows only the first occurrence's bounded sample; other
jobs and raw diagnostics remain available in JSON and the captured archive.

All text renderers use the same terminal-safe context projection. Optional
malformed/unknown published context is not interpreted; valid entries and fields
remain bounded. Context is not another root-cause group and does not change
counts or source conclusions. All nine frozen schema resources remain byte-for-
byte unchanged; old readers can ignore the optional occurrence extension.

## Evidence and delivery scope

`tests/test_diagnostic_ranking.py` replays six sanitized original run projections
for uibcdf/gh-run-receptor#59/#61/#62/#64/#66, including two distinct #66 cases.
It independently checks original source locators, API parity, diagnostic content,
bounded deterministic rendering and reviewed human/LLM goldens. Parser controls
cover incomplete and unmatched groups, exact 128-line and adjacent-blank bounds,
ANSI Windows output, redaction, genuine standalone GPG failure and missing solver
context. Earlier #50/#53/#56 guards remain active. These are unreleased source
corrections until a separate publication qualifies an exact candidate/artifact.
