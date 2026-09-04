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

The first implemented slice recognizes the canonical Conda subdirectories from job and
artifact names, requires at least two observed platforms plus a workflow path containing
`conda` or `rattler` for auto-detection, preserves failed platforms, and marks a platform
reusable only when it has both a successful job and an artifact. ABI validation, upload,
channel verification, configuration-driven expectations, and rerun targeting remain open.

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

Repository configuration is trusted only when read from the repository's default branch
or from an explicitly trusted revision. A pull request must not be allowed to supply its
own receptor rules and then use those rules to classify the same pull request. The report
records the configuration source, revision, schema version, and digest.

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

## Matching and precedence

Workflow matching proceeds from most to least specific:

1. an explicit CLI selection and profile;
2. inline Action inputs in the workflow that invokes the reporter;
3. an exact workflow path;
4. a numeric workflow ID;
5. a workflow-path pattern;
6. an exact display name;
7. a display-name pattern;
8. conservative auto-detection;
9. the generic profile.

Settings are layered in this order: built-in defaults, explicitly enabled organization
configuration, trusted repository configuration, inline Action settings, and explicit
CLI flags. Later layers may refine interpretation but cannot alter GitHub's authoritative
states. Two rules at equal specificity that assign incompatible values are a configuration
error; list order is not an implicit tie-breaker.

Exact matching is preferred. Patterns are anchored, length-bounded, validated before use,
and never interpreted as code. `config explain` must show the winning match, overridden
values, ignored candidates, and trust source.

## Roles and profile contracts

Rules assign semantic roles to jobs, steps, artifacts, and structured events. Roles do
not replace their source identity. Reports preserve both the original name and the role.

The initial profile contracts are:

- `generic`: complete job and step inventory, authoritative conclusions, durations,
  failed excerpts, artifacts, and missing evidence;
- `ci`: test, lint, type-check, coverage, optional-dependency, and matrix dimensions,
  including collection errors and the distinction between skipped and not executed;
- `docs`: content build, warnings, link checks, notebook execution, publication artifact,
  and deployment, with build and deployment reported independently;
- `conda`: platform/subdirectory, Python version, build, package inspection, installation
  test, upload, and channel verification, retaining successful platform artifacts when
  another platform fails;
- `release`: exact commit and tag, required gates, package identities and digests,
  registry publication, GitHub Release, citation metadata, and archive verification.

Each profile defines its required, optional, and repeatable evidence. Missing required
evidence produces `INCOMPLETE` or `UNKNOWN`; it never silently passes. Unknown jobs,
dimensions, and artifacts remain visible in the generic remainder.

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

## Auto-detection and evolution

Auto-detection may propose a profile from workflow path, job names, and known producer
events. It must expose its confidence and fall back to `generic` when ambiguous. It must
not infer success criteria merely from the absence of failure text.

Configuration documents carry `schema_version`. Unknown major versions fail validation;
unknown fields in a supported version are errors by default so misspellings cannot weaken
a gate. Migrations are explicit and testable. Stable releases document supported schema
versions and a deprecation window.
