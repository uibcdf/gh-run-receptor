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
| Stable capture direction | Adaptive by default, plus full and metadata modes | Avoid needless log transfer after reliability is proven |
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

## Open decision gates

### OD-001: Stable Action distribution

- **Question:** bundled JavaScript, packaged Python, or thin composite Action?
- **Needed evidence:** cold-start benchmarks on Linux, macOS, and Windows; artifact size;
  dependency and provenance review; release-maintenance cost.
- **Gate:** before publishing the first stable Action.
- **Current default:** develop the Python CLI and keep the Action boundary transport-neutral.

### OD-002: Stable adaptive-capture threshold

- **Question:** exactly when are full logs fetched automatically?
- **Needed evidence:** miss rate and request/byte cost across the initial corpus, including
  incomplete and unknown states.
- **Gate:** before changing the default from `full` to `adaptive`.
- **Current default:** `full` during alpha; never claim complete diagnosis without the
  evidence needed to support it.

### OD-003: Pattern engine

- **Question:** glob-only, a safe regular-expression engine, or bounded host regex?
- **Needed evidence:** real configuration needs, cross-platform packaging, worst-case
  behavior, and usability.
- **Gate:** before accepting regex syntax in schema version 1.
- **Current default:** exact names and anchored globs only.

### OD-004: Organization-level configuration

- **Question:** how should shared rules be discovered, authenticated, and versioned?
- **Needed evidence:** GitHub storage options, permission behavior in forks, precedence
  examples, and administrative usability.
- **Gate:** before implementing organization configuration.
- **Current default:** built-ins plus trusted repository and explicit inline/CLI settings.

### OD-005: Watch behavior

- **Question:** polling intervals, event deltas, terminal refresh, and API budget?
- **Needed evidence:** rate-limit measurements and comparison with `gh run watch --compact`.
- **Gate:** before declaring `watch` stable.
- **Current default:** emit only state changes and a final report; no repeated unchanged tree.

### OD-006: Exit-code stability

- **Question:** whether all provisional codes in the CLI contract are needed by automation.
- **Needed evidence:** shell and CI consumer scenarios, especially incomplete evidence versus
  receptor failure.
- **Gate:** before CLI 1.0.
- **Current default:** use the provisional mapping and reject collisions silently coerced to
  generic failure.

### OD-007: Fixture repository and publication policy

- **Question:** which repository owns live fixtures and which captured evidence may be public?
- **Needed evidence:** retention, license, privacy review, maintenance owner, and cost.
- **Gate:** before enabling scheduled live integration tests.
- **Current default:** synthetic and explicitly sanitized local fixtures only.

### OD-008: Version and support policy

- **Question:** release cadence, pre-1.0 compatibility, operating-system matrix, and minimum
  supported GitHub CLI version.
- **Needed evidence:** first vertical-slice compatibility runs and packaging choice.
- **Gate:** before the first public package release.
- **Current default:** Python 3.11–3.13; no OS support claim until verified.

## Deferred, not forgotten

The following are deliberately outside the initial read-only product: automatic reruns,
cancellation, approvals, deployment, package upload, workflow rewriting, organization-wide
service operation, and a general log-query language. They require a new scope and security
decision rather than opportunistic implementation.
