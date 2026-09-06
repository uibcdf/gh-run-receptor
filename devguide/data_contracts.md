# Data contracts

## Contract family

The project uses five related, independently versioned documents:

- `gh-run-receptor.bundle@1`: captured source resources and manifest;
- `gh-run-receptor.model@1`: normalized internal/source model serialized for testing;
- `gh-run-receptor.report@1`: profile assessment and rendered-report inputs;
- `gh-run-receptor.config@1`: normalized trusted repository workflow rules;
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
  "receptor_version": "0.2.0",
  "capture_policy": "full",
  "captured_at": "2026-09-04T10:40:00Z",
  "complete": true,
  "members": [
    {
      "path": "run.json",
      "kind": "github.workflow_run",
      "bytes": 12345,
      "sha256": "...",
      "complete": true
    }
  ],
  "warnings": []
}
```

The manifest and structured members use canonical, sorted JSON encoding. Every member has
an exact byte count and SHA-256 digest; both are checked before replay. The manifest is not
self-digested. A member is immutable after capture. Refreshing active evidence creates a
new generation or atomically replaces the bundle only after all new members and the
manifest validate.

New captures retain `id`, `run_attempt`, and `head_sha` in `run.json`. Loading compares
each retained value with the manifest and rejects a contradiction before normalization.
Older reviewed fixtures that predate the additive `id` and `run_attempt` retention remain
readable when those fields are absent; absence never permits a present contradiction.

`config.json` is an optional structured member. When present, it contains
`gh-run-receptor.config-capture@1`: the normalized `config@1` document plus the canonical
repository path, default-branch name, Git blob SHA when supplied, and SHA-256 of the exact
source bytes. Old bundles without this member remain valid and use conservative profile
auto-detection during replay.

The default cache identity includes hostname, repository, run ID, attempt, and capture
policy. A metadata-only bundle is never reused as though it satisfied an adaptive or full
request. An explicit output path is accepted only when its manifest identity exactly
matches the request.

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

Normalization produces `gh-run-receptor.model@1`. Every normalized job, failed step, and
artifact carries a source member and JSON Pointer. Profile interpretation consumes this
model rather than the original GitHub dictionaries.

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

Normalized jobs may include the additive `steps` field. Each step retains number, name,
status, conclusion, and an evidence reference. `failed_steps` remains the bounded
failure-oriented projection for compatibility; profiles that need successful or skipped
phase evidence consume `steps` and never reconstruct it from prose logs.

The normalized subject also carries the additive `event` and `head_ref` fields from the
workflow-run record. `head_ref` is an observed GitHub value, not independently verified
branch or tag identity. Profiles that require a real tag must record that verification
separately rather than infer it from a version-shaped ref.

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
    "evidence_sufficient": true,
    "cause_evidence": "complete"
  },
  "completeness": {},
  "configuration": {
    "matched": true,
    "source": {
      "path": ".github/gh-run-receptor.yaml",
      "ref": "main",
      "blob_sha": "abcdef",
      "sha256": "..."
    },
    "match": {"path": ".github/workflows/build_conda.yaml"},
    "profile": "conda",
    "settings": {"expected_platforms": ["linux-64", "win-64"], "package_kind": "native"}
  },
  "expectations": {
    "satisfied": true,
    "missing_platforms": []
  },
  "jobs": [],
  "job_counts": {},
  "matrix": {},
  "causes": [],
  "artifacts": [],
  "unknowns": [],
  "warnings": [],
  "publisher": {
    "kind": "github_action",
    "repository": "uibcdf/gh-run-receptor",
    "ref": "0.12.0"
  }
}
```

`publisher` is an optional additive report field. The embedded Action sets it from the
Action repository and requested ref rather than inferring a package version from a source
archive without Git metadata. CLI reports omit it.

After the external CLI verifies a published report, it adds an optional
`consumer_verification` object. `source_facts: verified` means a fresh API response agreed
on repository, run, attempt, SHA, terminal status, conclusion, and URL. The separate
`interpretation: published_not_recomputed` value prevents that verification from being
misread as independent profile recomputation. Reporter run, artifact ID, exact name, and
GitHub digest remain visible provenance.

Source-first discovery additionally records `reporter_identity: verified` and the exact
`reporter_workflow` after GitHub agrees on artifact producer run, `workflow_run` event, run
path, workflow ID, and workflow path. These fields are absent from explicit historical
consumption when no canonical reporter identity was requested.

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

The MVP log analyzer records cause kind, normalized message, stable fingerprint, and every
job/member/line occurrence. It chooses the most specific bounded causal candidate rather
than treating a generic final exit-code marker as root cause. Normalization may remove a
volatile temporary script path but retains the original message in each occurrence.

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

The machine-readable Draft 2020-12 schemas ship inside `gh_run_receptor.schemas` as
`bundle-v1.schema.json`, `model-v1.schema.json`, `report-v1.schema.json`, and
`config-v1.schema.json`. They are the
formal spelling of the version 1 boundaries. The runtime validates untrusted bundle JSON,
critical manifest types, member paths, byte counts, digests, source collection shapes,
duplicate keys, and non-finite numbers without adding a validation dependency. The test
gate uses `jsonschema` to prove that real normalized models and reports conform to the
published files; `jsonschema` is a test/development dependency, not a runtime dependency.

Unknown GitHub enum values remain valid strings in normalized facts and also appear in
`unknowns` with their source reference. Additional fields are allowed at contract
boundaries so additive evidence survives older readers. A reader must still reject an
unknown schema identifier rather than guessing compatibility.
