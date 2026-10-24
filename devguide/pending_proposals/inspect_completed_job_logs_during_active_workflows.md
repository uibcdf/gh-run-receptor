---
summary: Inspect one completed job log without waiting for the workflow archive.
issue: uibcdf/gh-run-receptor#68
status: active
opened: 2026-10-24
closed:
verification: inspected
area: [github, cli]
guard: tests/test_job_logs.py
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

## Source implementation and initial guards

The selection, original-byte acquisition and replay validator live in
`gh_run_receptor/job_logs.py`; archive and plain logs call the same stream
analyzer and cause grouping. Timestamp stripping now removes only its one
separator, preserving Python traceback indentation. Existing diagnostic/log/report
regressions and new truth/identity/privacy/schema guards pass together (196
focused tests). This is source evidence, not a completed release/native receipt.
The clean task environment uses Python 3.14.7, Ruff 0.16.5 and the committed
pytest-receptor 1.1.0; no caller environment is replaced. Conda secret availability
remains unconfirmed: the repository has no repository secrets and the authenticated
account cannot list organization secrets. A maintainer clarification is pending;
no secret values were read or requested in chat.

## Qualification checkpoint — 2026-10-24

Full clean local source suite: 805 passed/one installed-Conda-only skip. Ruff
lint/format, 29-route input preflight, all nine frozen contracts and strict
Sphinx pass. The known published pytest renderer warning remains visible. New
native `validate-job-logs.yml` deliberately creates a Windows typed failure and
a Linux success; its observer must pass while the overall workflow is still
active. The expected producer failure remains a failed native workflow, never a
green product gate. No waiting/keepalive runner is needed: the observer is active.
Native receiving and installed delivery remain pending.

The maintainer confirms organizational ANACONDA_UIBCDF_TOKEN availability for
this repository (2026-10-24); actual authorized upload is still independently
verified by #60. Cross-component advance notice: uibcdf/molsyssuite#141. Read-only
comparison with SMonitor, ArgDigest, DepDigest and Pytest Receptor confirms the
same committed-plan/source/staged/exact-file installed/promotion contract; their
provider pins and custom versus shared wrappers differ. GHR uses its existing
shared callers. No PyPI route is added.

The first native dispatch at source 28cd0af was refused by GitHub: the success
producer's inline YAML scalar contained an unquoted colon-space. No probe run
executed and no active-window success is credited. Both producer commands now
use literal block scalars; a safe-loader/manual-only/read-permission guard covers
the actual workflow. Its route hash is refreshed after this source-only review.

Native run `40142196406` at 54afb4c executed the intended Windows failure and
Linux success, but the observer failed: modern gh rejected an ANSI-bearing plain
log. Independent new-command diagnosis reproduces that bounded acquisition
failure; no active-window receiving success is credited. The adapter now opts
into original raw bytes only for private file downloads on gh >=2.97.0, where
the upstream API flag exists. JSON/terminal safety, the 2.48.0 floor, no-retry
budget and incomplete-file cleanup remain unchanged; boundary and real receiving
checks are separate. The failed observer remains visible historical evidence.

## Authentic receiving — 2026-10-24

Native run `40142448058`, attempt 1, source
`cc5ad3c437763b1783535c93b088d2d8dbb2a505` passed observer job `121016868087`
and all its acquisition/replay/artifact steps. The producer Windows job failed
intentionally and the Linux producer succeeded; the workflow conclusion remains
failure. The digest-checked sanitized artifact `12579605432` confirms both actual
job-only captures during status in_progress/conclusion null, exit 3, deterministic
three-renderer replay and disposal of managed raw temporary captures. The typed
Windows failure is selected; successful failed-looking text produces no cause.
`devguide/evidence/job_log_receiving_2026-10-24.json` records that exact scope.

An independent terminal reread of original Sabueso run 40013378053/attempt 1/job
120619139357 retains all fifteen structured jobs, native failure/exit 1 and the
NotADirectoryError/WinError 267 cause plus both failed test nodes. It does not
reconstruct the original active window. Its sanitized receipt is
`devguide/evidence/job_log_original_sabueso_2026-10-24.json`. Native twelve-cell
candidate compatibility and installed release qualification remain under #72.
