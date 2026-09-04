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

## Configuration trust

Repository rules are loaded from the default branch or an explicitly trusted revision.
Pull-request head configuration is data, not policy, unless a user deliberately opts in
outside an automated gate. Reports include the policy revision and digest. Inline Action
rules are trusted only as part of the already trusted workflow definition that invokes
the reporter.

The rule language is declarative. It has no shell commands, imports, arbitrary templates,
network requests, filesystem paths outside the evidence workspace, or dynamic evaluation.
Rules cannot downgrade official failure, cancellation, or missing evidence to success.

## Log and text handling

All remote text is untrusted. Renderers strip or visibly escape terminal control codes,
normalize newlines, make bidirectional controls visible, and bound individual lines and
excerpts. Secret-like values are redacted before output or fixture creation. Text claiming
`PASS` or imitating receptor syntax remains quoted source evidence and never becomes a
verdict without a trusted rule and source state.

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
