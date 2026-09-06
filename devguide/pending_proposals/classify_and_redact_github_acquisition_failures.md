---
summary: Classify and redact GitHub acquisition failures
issue: uibcdf/gh-run-receptor#15
status: active
opened: 2026-09-06
closed:
verification: measured
area: ['github', 'security', 'cli', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Classify and redact GitHub acquisition failures

**Reported:** 2026-09-06, while closing the restricted-permission evidence gap.
**Status:** Active; four transport outcomes have been measured or bounded.

## What

Give every `AcquisitionError` a stable category and optional HTTP status. Render that
category in the CLI error line while retaining exit status 5. Redact and bound untrusted
GitHub CLI stderr before it becomes user-facing output.

## How

The transport boundary maps missing GitHub CLI authentication, HTTP 401, HTTP 403, HTTP
404, HTTP 429/rate-limit text, and other failures to conservative categories. It preserves
the safe final diagnostic line but strips terminal controls, credential-shaped tokens, and
excess length. `optional_json` uses structured status 404 rather than matching prose.

The classification is diagnostic only. It does not retry, authenticate, request new
scopes, reinterpret a private 404, or turn acquisition failure into incomplete evidence.

## Why

The current implementation exposes one free-form `RECEPTOR_ERROR` and recognizes optional
404 by searching `str(error)`. This makes control flow depend on presentation, prevents an
agent from choosing the correct recovery, and does not enforce the documented output bound
or redaction rule at the acquisition boundary.

## What is measured and what is assumed

On 2026-09-06, isolated read-only `gh api` probes produced:

- no configured session: exit 4 and instructions to authenticate, without HTTP status;
- invalid probe credential: exit 1 and `Bad credentials (HTTP 401)`;
- non-admin read of `actions/checkout` Actions permissions: exit 1 and HTTP 403;
- nonexistent gh-run-receptor run: exit 1 and `Not Found (HTTP 404)`.

The first probe used an empty temporary `GH_CONFIG_DIR`; the second added a deliberately
invalid non-secret `GH_TOKEN`. The configured developer credential was neither replaced
nor printed. HTTP 429 and hostile stderr remain synthetic cases because deliberately
exhausting a real rate limit or inducing secret reflection is unsafe.

## What was refuted

- Keeping raw free-form prose as the only contract is rejected because callers cannot
  distinguish recovery paths reliably.
- Treating every 404 as confirmed absence is rejected because GitHub deliberately uses
  404 for some inaccessible private resources.
- Returning workflow exit codes 1--4 is rejected because no workflow evidence was
  acquired; receptor failure remains 5.
- Echoing all stderr is rejected because it is untrusted, unbounded, and may contain
  environment- or credential-shaped text.

## Scope and exclusions

This increment covers GitHub CLI acquisition errors. It does not add authentication,
refresh tokens, inspect scopes, mutate permissions, implement automatic retry, or change
bundle incompleteness semantics. Download failures use the same safe classifier where
their stderr surface permits it.

## Acceptance criteria

- Missing authentication, 401, 403, 404, rate limiting, and generic transport failure have
  stable machine-readable categories.
- Optional resource lookup suppresses only structured 404.
- CLI stderr exposes the category in one bounded line and returns 5.
- Credential-shaped and terminal-control input is redacted or escaped before display.
- Unknown future errors remain conservative and preserve a bounded diagnostic.
- Unit tests use the measured stderr shapes plus adversarial synthetic cases.
- User and developer contracts explain recovery and the 404 ambiguity.

## Dependencies and risks

There is no blocker. GitHub CLI prose may evolve, so HTTP status is primary when present
and missing-authentication recognition is intentionally narrow. Unknown text falls back
to a generic category rather than a guessed permission diagnosis.

## Provenance

Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.9.0, 2026-09-06.
Authenticated probes were read-only; the unauthenticated probes used an isolated temporary
configuration directory.
