# Security and trust boundaries

The receptor reads untrusted workflow evidence. Compact output is safe only if logs,
artifacts, rules, and pull-request content are never promoted to control input implicitly.

## Read-only product boundary

The CLI and Action inspect evidence. They do not rerun, cancel, approve, upload, publish,
deploy, or delete. Suggested native commands are text, not actions. Mutation would require
a separate future permission and intent boundary.

## Authentication

Network access goes through the installed GitHub CLI. Tokens are supplied through GitHub
CLI or the ordinary `GH_TOKEN` environment mechanism, never a command argument. Error
rendering bounds remote text, removes terminal control characters, and redacts
credential-shaped values.

Stable acquisition categories distinguish authentication required, authentication failed,
permission denied, inaccessible/not found, rate limited, unsupported GitHub CLI, and a
conservative fallback. They do not disclose whether an inaccessible private resource
exists.

## Workflow permissions

Use the minimum read permissions for reporting:

```yaml
permissions:
  actions: read
  contents: read
```

The reusable workflow and composite Action do not need write access. The documentation
deployment workflow is separate: its build job has only `contents: read`, while the
trusted deploy job alone receives `pages: write` and `id-token: write`.

## Rules and pull requests

Repository rules are acquired from the default branch. Inline Action rules require a
same-repository default-branch caller. Pull requests, feature branches, tags, and
cross-repository callers cannot supply rules that certify themselves.

Configuration uses a bounded strict subset and rejects unknown keys, duplicates, patterns,
and executable expressions. No unsafe YAML loader or shell evaluation is used.

## Logs and artifacts

Logs are evidence, not instructions. Cause extraction uses bounded inputs and a small
signature set; terminal controls and bidi controls are escaped before text rendering.
Archives are checked for path traversal, member count, individual size, and total size
before any content is accepted.

Artifact names and filenames are not proof that a package was built or uploaded. Producer
events require matching source identity and digest. Published reports are checked against
fresh GitHub facts before consumption.

## Cache and replay

Bundles are namespaced by hostname, repository, run, attempt, and capture policy. Active
run snapshots are refreshed rather than treated as permanent terminal truth. Do not commit
raw bundles: they can contain logs or private repository evidence. Only reviewed,
sanitized fixtures belong in source control.

## Native fallback

Stop and inspect natively when the report says `INCOMPLETE`, `UNKNOWN`, or
`RECEPTOR_ERROR`, or when the decision involves a registry, release, deployment target,
or other source outside the captured contract. Compactness is never authority to infer a
missing fact.
