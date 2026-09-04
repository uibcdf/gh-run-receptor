# Data contracts

## Contract family

The project uses four related, independently versioned documents:

- `gh-run-receptor.bundle@1`: captured source resources and manifest;
- `gh-run-receptor.model@1`: normalized internal/source model serialized for testing;
- `gh-run-receptor.report@1`: profile assessment and rendered-report inputs;
- `gh-run-receptor.events@1`: optional evidence emitted by an instrumented workflow.

Version identifiers are explicit strings, not inferred from package version. Additive
optional fields do not require a major schema change. Removing fields, changing meaning,
or tightening a value contract requires a new schema version and a migration reader.

## Source, normalized, and interpreted layers

The model keeps these layers distinct:

1. **Source facts:** values and provenance from GitHub responses or captured files.
2. **Normalized facts:** stable identities, durations, matrix keys, and relationships
   derived without workflow-specific judgment.
3. **Interpretations:** roles, cause groups, partial successes, and expectations applied
   by a named profile and rule set.
4. **Presentation:** bounded text or Markdown derived from the report.

No later layer mutates an earlier one. Every interpretation identifies its contributing
source references.

## Bundle manifest

The first manifest shape is:

```json
{
  "schema": "gh-run-receptor.bundle@1",
  "repository": "uibcdf/molsysmt",
  "hostname": "github.com",
  "run_id": 33863426589,
  "run_attempt": 1,
  "head_sha": "0123456789abcdef",
  "api_version": "explicit-version-string",
  "capture_policy": "full",
  "captured_at": "2026-09-04T10:40:00Z",
  "complete": true,
  "members": [
    {
      "path": "run.json",
      "kind": "github.workflow_run",
      "source_url": "https://api.github.com/...",
      "status": 200,
      "bytes": 12345,
      "sha256": "...",
      "complete": true
    }
  ],
  "warnings": []
}
```

The manifest itself has a canonical digest calculated without a self-referential digest
field. A member is immutable after capture. Refreshing active evidence creates a new
generation or atomically replaces the bundle only after all new members and the
manifest validate.

## Evidence references

Every normalized or interpreted fact can cite an evidence reference:

```json
{
  "member": "jobs.json",
  "json_pointer": "/jobs/2/steps/5/conclusion"
}
```

Log evidence adds archive member, normalized line range, and original line range. A
reference never relies solely on a temporary local absolute path.

## Normalized identities

- Repository: normalized hostname plus case-preserving `owner/name` display and a
  comparison-safe form.
- Run: repository plus numeric run ID plus attempt.
- Workflow: repository plus numeric ID and path stripped of its execution ref suffix.
- Job: run identity plus GitHub database job ID.
- Step: job identity plus GitHub step number; missing numbers receive a documented
  synthetic identity and cannot be rerun independently.
- Matrix member: sorted key/value pairs extracted from structured names or producer
  evidence; inferred matrix values carry provenance and confidence.
- Artifact: run identity plus artifact ID, with name treated as display/configuration
  data rather than a unique identity.

## Time and duration

Source timestamps are retained in UTC ISO 8601 form. Durations are integer milliseconds
derived only when both endpoints are present and ordered. Queue, setup, build, test,
publish, and total duration remain separate profile metrics. Missing or inconsistent
timestamps produce warnings, not negative or invented durations.

## Completeness

Completeness is dimensional rather than one boolean:

```json
{
  "metadata": "complete",
  "jobs": "complete",
  "checks": "unavailable",
  "artifact_inventory": "complete",
  "artifact_content": "not_requested",
  "logs": "partial"
}
```

Allowed values include `complete`, `partial`, `unavailable`, `expired`,
`not_permitted`, `not_requested`, and `invalid`. A requested assertion declares which
dimensions it requires.

## Report

The report preserves official and derived state:

```json
{
  "schema": "gh-run-receptor.report@1",
  "subject": {
    "repository": "uibcdf/molsysmt",
    "run_id": 33863426589,
    "run_attempt": 1,
    "head_sha": "0123456789abcdef"
  },
  "github": {
    "status": "completed",
    "conclusion": "failure"
  },
  "receptor": {
    "assessment": "PARTIAL",
    "profile": "conda",
    "profile_version": 1,
    "evidence_sufficient": true
  },
  "matrix": {},
  "causes": [],
  "artifacts": [],
  "metrics": {},
  "unknowns": [],
  "suggestions": []
}
```

Unknown GitHub enum values and unrecognized fields are preserved in source evidence and
listed in `unknowns` when they affect interpretation.

## Cause groups

A cause group contains a stable fingerprint derived from normalized failure class,
phase/role, causal location, and normalized cause chain. Volatile timestamps, temporary
paths, runner IDs, and matrix values are removed only by reviewed normalizers. Similar
messages are not grouped merely because they share generic words such as `error`.

Every group stores all occurrence identities even when rendering only a sample. Profile
rules may label a known signature but cannot replace the original normalized message or
evidence reference.

## Producer events

Instrumented workflows may emit newline-delimited events or a final document. A minimal
event contains:

```json
{
  "schema": "gh-run-receptor.events@1",
  "producer": "uibcdf/action-build-and-upload-conda-packages",
  "producer_version": "2.0.3",
  "run_id": 33863426589,
  "job_id": 987654,
  "kind": "conda.artifact_validated",
  "platform": "osx-64",
  "artifact": "molsysmt-0.22.0-pyabi3h123_2.conda",
  "python_versions": ["3.11", "3.12", "3.13"],
  "result": "success"
}
```

Producer evidence is untrusted corroborating evidence. Run and job IDs must match the
captured subject. Events cannot override official conclusions. Limits apply to event
count, line size, total bytes, nesting, and string lengths.

## Serialization and validation

- Decode JSON strictly as UTF-8 and reject duplicate object keys in security-sensitive
  documents where the parser supports detection.
- Reject non-finite numbers.
- Preserve integers without floating-point conversion.
- Validate maximum depth, collection length, and string size before profile processing.
- Write bundles and reports atomically.
- Never deserialize executable Python objects or unsafe YAML tags.
- Readers support every non-retired schema version and produce an explicit incompatibility
  error for future major versions.

Formal JSON Schemas are a Phase 1 deliverable. The examples in this document define the
minimum semantic boundary, not yet the final property spelling.

