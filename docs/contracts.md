# Compatibility and contracts

`gh-run-receptor` is pre-1.0, but published serialized contracts are already immutable at
their integer schema version. Incompatible changes use a new integer version and an
explicit migration or retirement decision.

List the installed reader inventory without network access:

```bash
gh run-receptor contracts
gh run-receptor contracts --format=json
```

## Published resources

| Resource | Purpose | First frozen release |
| :--- | :--- | :--- |
| `bundle@1` | Replayable capture manifest and member integrity | 0.18.0 |
| `model@1` | Normalized run, job, step, check, and artifact facts | 0.18.0 |
| `report@1` | Source facts, interpretation, completeness, and warnings | 0.18.0 |
| `config@1` | Strict workflow-specific profile rules | 0.18.0 |
| `config-capture@1` | Trusted configuration source, revision, and digest | 0.19.0 |
| `comparison@1` | Two-source identities and descriptive deltas | 0.19.0 |
| `comparison-policy@1` | Opt-in regression requirements | 0.19.0 |
| `events@1` | Bounded producer evidence hidden inside one visible job | 0.20.0 |
| `aggregate@1` | Independent truth from two to fifty runs | 0.21.0 |

Readers reject malformed, wrong-kind, retired, or unsupported future contracts. Additive
unknown fields are preserved only where the relevant schema and reader contract allow
them; do not infer forward compatibility from JSON alone.

## Source facts and interpretation

JSON keeps these layers separate:

1. **subject identity:** repository, workflow, run, attempt, commit, and URL;
2. **GitHub facts:** status, conclusion, jobs, steps, checks, and artifacts;
3. **completeness:** which evidence dimensions were actually acquired;
4. **receptor interpretation:** profile, assessment, grouped causes, and expectations;
5. **warnings:** explicit uncertainty and bounded degradation.

Consumers must not replace GitHub's conclusion with the assessment. A report can validly
contain `assessment=PARTIAL` and `conclusion=failure`.

## Exit-status compatibility

The process-status map is stable for CLI 1.0 as of 0.21.1. Codes 0 through 5, 64, and 130
are defined in [Command-line usage](usage.md#stable-process-statuses). New meanings cannot
reuse those values silently.

## Capture integrity

Every bundle member has a byte length, SHA-256 digest, completion flag, and semantic kind.
The loader validates the manifest and cross-resource source identity before replay. A
complete manifest means the requested capture policy completed, not that every possible
GitHub or external fact exists forever.

## Producer and published artifacts

`events@1` records observed work performed inside a composite Action. A canonical Action
`report@1` artifact records an interpretation from one reporter revision. Consumers verify
both artifact integrity and fresh source identity; they do not treat either artifact as an
independent registry, tag, release, or archive check.
