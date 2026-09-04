# Reporting protocol

This document is normative for reports in `pending_bugs/`, `pending_proposals/`,
their archives, and the corresponding GitHub issues.

## Core rule

**If a concern deserves a document in `devguide/`, it deserves a GitHub issue.**
Typos, lint-only fixes, and similarly small maintenance do not need either record.

The two records have different purposes:

| Record | Contents | Update cadence |
| --- | --- | --- |
| Developer report | Analysis, evidence, rejected alternatives, and progress | Continuously |
| GitHub issue | State and settled facts useful outside the checkout | At opening and closing |

Use one issue per coherent theme. A theme may have several evidence documents, but every
pending document must name its issue. Cross-repository references use stable identifiers
such as `uibcdf/molsysmt#198`, never paths into another repository's `devguide/`.

## Front matter

Every report, including an archived report, starts with YAML front matter:

```yaml
---
summary: Supporting declarative workflow-specific filtering.
issue: uibcdf/gh-run-receptor#12
status: open
opened: 2026-09-04
closed:
severity: medium
verification: asserted
area: [profiles]
guard:
normative:
blocked_by: []
supersedes: []
---
```

`severity` is required only for bugs and is one of `critical`, `high`, `medium`, or
`low`. `verification` is one of `reproduced`, `measured`, `inspected`, `upstream`, or
`asserted`. `area` contains one or more repository labels. `README.md` files are generated
indexes and have no front matter.

Statuses in the open set are `open`, `active`, `blocked`, and `partial`. A blocked report
must name at least one issue in `blocked_by`. Statuses in the closed set are `resolved`,
`withdrawn`, and `superseded`; their reports belong under `archive/` and require a closing
date. A resolved report must identify either a regression `guard` or the `normative`
document that absorbed its durable rule. A superseded report names its replacement.

## Opening and working

1. Open the issue first, so its number becomes the stable identity of the theme.
2. Create the report from [the report template](templates/report.md) in the appropriate
   pending queue and fill in the issue reference.
3. Commit and push the issue-backed report promptly; do not leave an issue pointing to a
   path absent from `main` across sessions.
4. Update analysis and progress in the report, not through a stream of issue comments.

The issue body is intentionally concise:

```text
What   — what is wrong or proposed.
How    — how it occurs or how the proposal would work.
Why    — its user or development impact.
Record — devguide/pending_proposals/example.md
```

An incoming issue need not have a developer report until it is accepted for investigation.
This asymmetry is deliberate: every pending report has an issue, but not every issue has a
report.

Use `python devtools/scripts/devguide_issue.py open` for project-originated work. It checks
that the required labels exist before creating the issue and report. The kind labels are
`bug` and `proposal`; state labels are `in-progress`, `blocked`, and `partial`; area labels
match the values in `area`.

After changing a pending report's state or areas, run
`python devtools/scripts/devguide_issue.py sync <report>` to synchronize managed labels.
The helper preserves unrelated labels.

## Closing

1. Record a closed status and date, plus `guard` or `normative` for resolved work.
2. Move the report to its matching archive directory.
3. Regenerate the queue indexes.
4. Commit and push the implementation and record.
5. Close the issue with the commit, user-visible outcome, guard or normative rule, and
   archived record path.

Run `python devtools/scripts/devguide_issue.py close <report> --commit <sha>` to check the
record and close its issue. A proposal closing comment states the decision and reason. A
bug closing comment states what users experience after the fix.

Archived reports are historical evidence. Do not read them during routine onboarding and
do not silently rewrite them. The archive index is sufficient unless a current question or
document gives a concrete reason to inspect a particular report. If an archived factual
claim was never true, append a dated correction instead of rewriting the original account.

## Local gate

Run these commands after changing reports:

```text
python devtools/scripts/devguide_index.py
python devtools/scripts/validate_devguide.py
```

The validator enforces identity, lifecycle, required evidence, archive placement, and
generated-index consistency. The issue helper additionally checks GitHub state when used;
the local validator intentionally remains offline.
