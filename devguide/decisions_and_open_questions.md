# Decisions and open questions

## How to use this record

This page distinguishes settled product decisions from choices that require evidence.
Open questions are not undocumented gaps: each has a decision gate and a conservative
default that permits earlier work. When a choice is settled, update the relevant normative
page and retain only a concise decision record here.

## Settled decisions

| Topic | Decision | Consequence |
| --- | --- | --- |
| Product shape | External CLI first; optional Action and reusable reporter | Ordinary workflows remain inspectable without adoption |
| GitHub CLI integration | Repository `gh-run-receptor`, executable `gh-run-receptor` | Invocation is `gh run-receptor` |
| Phase 0 capture | Full API JSON records and log archive on disk | Early parsing is replayable and debuggable |
| Stable capture policy | `inspect`/`watch` default to adaptive, explicit archival `capture` to full, and remote `compare`/`aggregate` to metadata; adaptive requests the complete attempt archive only for a GitHub-confirmed completed conclusion other than `success` | The 0.22.0 truth table and paired benchmark avoid logs for active/successful runs without losing terminal non-success diagnosis |
| Source authority | GitHub states are authoritative | Derived labels never erase source failure or uncertainty |
| Mutation | Initial product is read-only | Rerun, cancel, approve, upload, and deploy are out of scope |
| Configuration | Declarative repository rules plus compact inline Action rules | No arbitrary executable configuration |
| Workflow identity | Exact path preferred | Names are secondary; numeric IDs are repository-local |
| Structured evidence | Versioned producer events preferred; logs are fallback | Producers can expose semantics without prose parsing |
| Reporter semantics | Bounded output and fail-open reporter errors | Receptor faults do not rewrite product status |
| Policy trust | Default-branch or explicitly trusted revision | A PR cannot self-certify with changed rules |
| Implementation start | Python 3.11–3.13, installed `gh` transport adapter | Fast prototype without coupling the data model to transport |
| Reader selection | `human` and `llm`; automatic TTY selection | JSON remains an orthogonal output format |
| Project license | MIT, aligned with MolSysMT and MolSysViewer | Source and distributed artifacts include `LICENSE` |
| Live fixture ownership | Use reviewed public UIBCDF captures and manual gh-run-receptor experiments; add a separate fixture repository only when repeated live coverage justifies it | No scheduled or push-triggered failure generators; synthetic cases remain where GitHub cannot safely produce the source state |
| Initial Action distribution | Thin composite Action around the dependency-free shared Python core and hosted `gh` command | Preserve one interpretation path across operating systems; pin runtime/artifact Actions and record publisher provenance |
| Runtime support | Python 3.11--3.13; GitHub CLI 2.48.0 minimum for networked commands; latest patched stable CLI recommended | The floor matches the first required `--paginate --slurp` release and is tested independently of current runner images |
| Product portability | Runtime core and profiles are repository-agnostic; MolSysSuite identities remain fixtures, hosted evidence, or explicit client configuration | External public workflows must join the pre-1.0 corpus; UIBCDF-specific release/guide tooling is not product behavior |
| Serialized contract evolution | Published major-schema resources are immutable; incompatible changes use a new integer version with explicit forward-only migration or documented retirement | Readers reject malformed, wrong-kind, retired, and future contracts; 0.18.0 freezes the first four v1 resources and 0.19.0 freezes the remaining three current v1 resources |
| CLI process status | Freeze 0 success, 1 known failure, 2 other terminal non-success, 3 active, 4 incomplete, 5 receptor error, 64 usage error, and 130 interruption | Shell and agent callers can distinguish source truth from invocation and receptor failures without parsing text; command-specific semantics remain normative |
| Watch behavior | Deterministic 10-to-60-second polling, 1.5 unchanged backoff, transition reset, 2 error backoff, abort on the third consecutive failure, transition-only progress, and identity-checked terminal run/jobs handoff | The request budget is calculable per jobs page and final evidence source; active-run output is measured against native compact watch without claiming savings for minimal completed status |
| 1.0 workflow matching | Exact path, positive numeric ID, or exact display name only | Glob and regular-expression selectors are post-1.0 work and cannot be added to frozen `config@1` |
| 1.0 configuration scope | Built-ins plus trusted default-branch repository and trusted inline/CLI configuration | Organization-level discovery and precedence are post-1.0 work |

## Open decision gates

No open decision gate applies at or before 1.0. The stable scope and evidence map are
normative in `release_readiness_1_0.md`.

The following questions are retained for post-1.0 proposals. They do not block the stable
release and their current answer is “not implemented.”

### OD-003: Post-1.0 pattern engine

- **Question:** glob-only, a safe regular-expression engine, or bounded host regex?
- **Needed evidence:** real configuration needs, cross-platform packaging, worst-case
  behavior, and usability.
- **Gate:** before accepting any pattern syntax in a new configuration contract.
- **1.0 decision:** exact path, positive numeric ID, and exact name only; globs and regular
  expressions are rejected.

### OD-004: Post-1.0 organization-level configuration

- **Question:** how should shared rules be discovered, authenticated, and versioned?
- **Needed evidence:** GitHub storage options, permission behavior in forks, precedence
  examples, and administrative usability.
- **Gate:** before implementing organization discovery or precedence.
- **1.0 decision:** built-ins plus trusted repository and explicit inline/CLI settings.

## Deferred, not forgotten

The following are deliberately outside the initial read-only product: automatic reruns,
cancellation, approvals, deployment, package upload, workflow rewriting, organization-wide
service operation, and a general log-query language. They require a new scope and security
decision rather than opportunistic implementation.
