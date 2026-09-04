# Rules and profiles

## Two separate operations

Run selection and run interpretation are different concerns.

Selection narrows which executions are fetched. It can use workflow path or ID, branch,
commit, event, actor, status, and creation interval where GitHub supports server-side
filtering. Interpretation applies a profile after a run has been selected.

```text
gh run-receptor list --workflow CI.yaml --branch main --status failure
gh run-receptor inspect RUN_ID --profile ci
```

## Workflow identity

An exact workflow path is the preferred portable identity:

```text
.github/workflows/build_and_upload_conda_packages.yaml
```

Numeric workflow IDs are stable within a repository but not portable. Display names may
be duplicated or changed. Name and path globs are supported as lower-priority matching
mechanisms.

## Built-in profiles

### Generic

Reports authoritative run, job, and step state; durations; failed-step excerpts; and
artifact inventory without workflow-specific assumptions.

### CI

Understands test, lint, coverage, optional-dependency, and matrix roles. It groups shared
causes and preserves skipped, blocked, cancelled, and incomplete work.

### Documentation

Separates content build, warnings, link checking, notebook execution, artifact creation,
and deployment. A successful build with a failed deployment is partial, not a generic
failure with lost progress.

### Conda

Separates native platform build, package contract validation, Python compatibility,
artifact identity, upload, and channel verification. It reports independently reusable
platform successes and identifies the smallest rerun target.

### Release

Relates the exact commit, tag, gates, built artifacts, registries, GitHub Release, and
citation/archive verification without treating a tag alone as publication.

## Repository configuration

The default configuration path is `.github/gh-run-receptor.yaml`:

```yaml
schema_version: 1

workflows:
  - match:
      path: .github/workflows/CI.yaml
    profile: ci

  - match:
      path: .github/workflows/build_and_upload_conda_packages.yaml
    profile: conda
    settings:
      expected_platforms:
        - linux-64
        - linux-aarch64
        - osx-64
        - osx-arm64
        - win-64
      expected_python: ["3.11", "3.12", "3.13"]
      artifact_pattern: "*.conda"
```

The CLI should provide `init`, `config check`, and `config explain` commands. `init`
discovers workflows and proposes profiles; `explain` identifies the matching rule and
each applied override.

## Inline Action rules

GitHub Action inputs can carry a small multiline rules document:

```yaml
- if: always()
  uses: uibcdf/gh-run-receptor@v1
  with:
    profile: conda
    rules: |
      expected_platforms: [linux-64, osx-64, win-64]
      artifact_pattern: "*.conda"
```

Inline rules avoid an extra file for simple workflows. Repository configuration is
preferred when rules are shared, extensive, or need independent validation. Inline
settings override built-in defaults but cannot rewrite source conclusions.

## Rule capabilities

The declarative language may define:

- workflow matching;
- job and step roles through exact names or bounded patterns;
- expected matrix members;
- artifact names and counts;
- structured evidence artifact names;
- metric extraction and comparison tolerances;
- known failure signatures and their presentation;
- accepted blocked states with explicit reasons.

It must not provide shell execution, arbitrary imports, general template evaluation, or
a way to turn failure, cancellation, or incompleteness into success. Unknown jobs and
unmatched errors remain visible in the generic section.

## Preferred structured evidence

Profiles should consume a versioned evidence artifact when a workflow emits one. Log
patterns are a compatibility fallback rather than the preferred contract. A Conda
producer, for example, can report platform, artifact digest, build duration, ABI
validation versions, and upload result directly as structured fields.

