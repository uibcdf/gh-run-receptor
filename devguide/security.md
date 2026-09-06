# Security and trust model

## Assets and adversaries

The receptor processes attacker-controlled workflow names, logs, annotations, artifacts,
and pull-request content while holding a token that may read repository metadata. The
security boundary protects credentials, runner and developer machines, trustworthy
classification, local storage, terminal integrity, and bounded resource use.

Relevant threats include secret disclosure, forged verdict text, terminal escape or
bidirectional-text attacks, command injection, malicious archives, catastrophic pattern
matching, decompression bombs, misleading configuration from an untrusted revision, and
confusion between evidence from different attempts or commits.

## Authentication and permissions

Phase 0 and Phase 1 use the installed GitHub CLI authentication and do not copy tokens
into reports or evidence bundles. The minimum read permissions are requested. Tokens,
authorization headers, signed redirect URLs, and environment-variable values are never
serialized. Authentication errors identify the missing capability without echoing secret
material.

The composite Action passes GitHub's ephemeral token only through `GH_TOKEN`; it never
places it in a command argument, output, summary, artifact, or publisher field. Its example
permission set is `actions: read` and `contents: read`. Restricted and fork-token behavior
remains a live release-gate case rather than an assumed capability.

## Configuration trust

The implemented repository loader reads rules only from the target repository's default
branch. Support for another explicitly trusted revision remains future work. Pull-request
head configuration is data, not policy. Reports include the policy path, default-branch
revision, and digest. Inline Action rules are not yet implemented.

The rule language is declarative. The dependency-free parser accepts a narrow YAML subset
and rejects tags, anchors, flow mappings, multiline scalars, patterns, unknown fields, and
oversized input. It has no shell commands, imports, arbitrary templates, network requests,
filesystem paths outside the evidence workspace, or dynamic evaluation. Rules cannot
downgrade official failure, cancellation, or missing evidence to success.

Local `init` treats workflow source as untrusted text and never evaluates YAML. Discovery
is non-recursive and bounded by file count, individual bytes, total bytes, and generated
configuration size. It rejects symlinked discovery directories, symlinked workflow files,
non-regular candidates, invalid UTF-8, and paths the strict configuration parser cannot
represent. A suggested profile gains no authority until a maintainer reviews and commits
the generated default-branch policy.

## Log and text handling

All remote text is untrusted. Renderers strip or visibly escape terminal control codes,
normalize newlines, make bidirectional controls visible, and bound individual lines and
excerpts. Secret-like values are redacted before output or fixture creation. Text claiming
`PASS` or imitating receptor syntax remains quoted source evidence and never becomes a
verdict without a trusted rule and source state.

GitHub CLI failure text crosses the same boundary before it is wrapped in an
`AcquisitionError`. Only one bounded diagnostic line is retained. GitHub-token shapes,
authorization values, and common token assignments are redacted; control and bidirectional
characters become visible escapes. Classification uses HTTP status first and narrow
missing-authentication/rate-limit signals second. Unknown prose never becomes a guessed
permission state.

The Action HTML-escapes untrusted report text before writing the Markdown summary, rejects
multiline scalar outputs and unsafe report names, bounds the summary to 32 KiB and report
to 8 MiB, and reuses the same credential-redacted error boundary as the CLI.

## Archives and artifacts

Downloads are streamed with limits on compressed bytes, expanded bytes, member count,
member size, and elapsed time. Archive members are rejected if they use absolute paths,
parent traversal, unsafe links, duplicate-confusion paths, or unsupported types. Parsing
occurs in a dedicated evidence directory without executing contents. Digests are checked
when GitHub supplies them and recorded otherwise.

The MVP enforces fixed limits on API output, binary download size, ZIP members, expanded
bytes, individual members, and individual log lines. It reads ZIP members in place without
extracting them. Configurable limits, elapsed-time enforcement, and broader archive-format
coverage remain release work and must not be claimed as implemented.

Published report consumption narrows the generic binary limit to 10 MiB at the transport
call itself, before hashing or ZIP parsing. It accepts one regular, unencrypted, basename-
only JSON member of at most 8 MiB and rejects links, traversal, extra members, malformed or
duplicate-key JSON, invalid provenance, and digest mismatch. Fresh source-run metadata must
agree with the artifact. This verifies source facts, not arbitrary profile claims; output
states that distinction explicitly and rejects any derived `PASS` over official non-success.

## Pattern safety

Exact matching is the default. User patterns have length and count limits, are compiled
before evidence processing, and use an implementation with predictable runtime or an
enforced timeout. Pattern failures are configuration errors, never silent non-matches.
Unbounded multiline matching over an entire log is prohibited.

## Resource bounds and retention

Every acquisition and rendering path has configurable caps for API pages, jobs, steps,
annotations, artifacts, bytes, lines, excerpts, and wall time. Truncation is explicit and
causes an incomplete assessment where omitted evidence could change the result.

Raw bundles may contain sensitive repository data. They are private by default, excluded
from version control, created with restrictive permissions where supported, and governed
by an explicit retention or deletion policy. Sanitized fixtures must be reviewed before
commit. Sharing a bundle requires deliberate user action.

## Supply chain and releases

Dependencies are minimized and pinned through reproducible metadata. Releases publish
checksums or provenance appropriate to each distribution. Examples pin the Action to a
stable major only after that update policy exists; high-assurance users may pin a full
commit SHA. Third-party parsers never receive executable hooks.

## Adversarial release gate

Before a stable release, tests must cover ANSI and bidirectional controls, fake verdicts,
credential-shaped text, huge lines, malformed JSON, archive traversal, unsafe links,
decompression limits, pathological patterns, pagination exhaustion, mixed attempts, and
untrusted pull-request configuration. Security failures must be distinguishable from a
workflow's own failure.
