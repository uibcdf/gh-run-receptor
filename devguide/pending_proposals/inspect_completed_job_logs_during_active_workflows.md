---
summary: Inspect one completed job log without waiting for the workflow archive.
issue: uibcdf/gh-run-receptor#68
status: active
opened: 2026-10-24
closed:
verification: inspected
area: [github, cli]
guard:
normative: github_evidence.md
blocked_by: []
supersedes: []
---

# Explicit completed-job log inspection

The user authorizes completing #60, #65 and #68, followed by 1.3.0 only after
all required delivery gates pass. This record accepts the concrete Sabueso
active-workflow diagnostic need in #68 without changing frozen capture defaults.

Provisional design: `inspect RUN --job JOB_ID` and `capture RUN --job JOB_ID`
retain the selected attempt's complete structured run/job facts but request only
that completed job's plain-text log. The attempt-qualified jobs list proves
membership before downloading `/repos/OWNER/REPO/actions/jobs/JOB_ID/logs`.
The selection has a distinct cache identity and an additive manifest/report scope;
it is never presented as a full attempt archive. Metadata-only selection makes
no log request. Existing capture policies, schemas, Action and reusable defaults
remain compatible. The shared report/parser remains the only diagnosis path.

Requirements: reject wrong/missing/duplicate job identity and conflicting run,
attempt or SHA; preserve unknown source fields and native run/job conclusions;
bound bytes and line parsing; retain explicit unavailable/permission/expired
states; redact controls/credentials in derived output; remove aborted staging
without deleting caller evidence. Active workflow status remains active even if
the selected completed job failed. Plain logs preserve their original bytes
separately from safe interpreted text. Replay is deterministic and offline.

The REST job-log endpoint returns plain text through a temporary redirect, unlike
the attempt ZIP endpoint. Reference:
https://docs.github.com/en/rest/actions/workflow-jobs#download-job-logs-for-a-workflow-run
The installed gh transport owns redirects/authentication; signed URLs are never
stored in derived evidence. Source implementation, synthetic guards, authentic
active-window observation and installed release evidence are separate gates.

All new task-only environments, SDK clones and live probes belong to
`/tmp/ghrr-1.3.0-z8LfuC` through final receiving. Existing caller caches,
environments, pins, unrelated work and historical task paths remain preserved.
