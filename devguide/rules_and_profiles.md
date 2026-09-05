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
be duplicated or changed. Version 1 configuration supports only exact path, ID, or name
matches. Patterns remain a future capability.

## Built-in profiles

### Generic

Reports authoritative run, job, and step state; durations; failed-step excerpts; and
artifact inventory without workflow-specific assumptions.

### CI

The first implemented slice assigns every job exactly one presentation role: `publish`,
`docs`, `lint`, `coverage`, `test`, `build`, or `other`. Keywords match normalized whole
words, and `other` preserves names the profile does not understand. LLM output groups
failed jobs only when their official conclusion and ordered failed-step names agree. JSON
retains every job. Required jobs, coverage thresholds, annotations, optional-dependency
semantics, and structured matrix dimensions remain future work.

### Documentation

Separates content build, warnings, link checking, notebook execution, artifact creation,
and deployment. A successful build with a failed deployment is partial, not a generic
failure with lost progress.

The first implemented slice assigns every retained step exactly one presentation phase:
`build_deploy`, `notebooks`, `links`, `warnings`, `artifact`, `deploy`, `build`, `setup`,
or `other`. Jobs whose retained API record has no steps become one fallback unit. A
composite Sphinx-to-Pages step remains `build_deploy`; it is not duplicated into two
independently successful claims. Only separate successful build and failed deployment
evidence derives `PARTIAL`. JSON retains all steps and phase evidence, while compact
failure output omits successful setup/other counts. Required phases, warning parsing,
rendered-page validation, and deployment probing remain future work.

### Conda

Separates native platform build, package contract validation, Python compatibility,
artifact identity, upload, and channel verification. It reports independently reusable
platform successes and identifies the smallest rerun target.

The implemented slice recognizes the canonical Conda subdirectories from job and
artifact names, requires at least two observed platforms plus a workflow path containing
`conda` or `rattler` for auto-detection, preserves failed platforms, and marks a platform
reusable only when it has both a successful job and an artifact. ABI validation, upload,
channel verification, and rerun targeting remain open. Repository rules can assign the
profile explicitly and require named native platforms.

A repository rule can instead declare `package_kind: noarch`. This explicit setting is
required because zero recognized platforms is also a valid targeted native retry and is
not evidence of a noarch recipe. A noarch report retains all job and artifact identities,
does not render `platforms=0/0`, and classifies current GitHub artifact evidence as
`available`, `expired`, `observed` with unknown expiry, or `not_observed`. The last state
means only that the complete current inventory is empty; it does not prove that an
artifact never existed or that channel publication did or did not occur.

### Release

Relates the exact commit, tag, gates, built artifacts, registries, GitHub Release, and
citation/archive verification without treating a tag alone as publication.

The first implemented slice preserves the observed event, head ref, and exact SHA, while
marking tag verification as not observed. Every retained step becomes one evidence unit
with bounded `identity`, `gate`, `package`, `publish`, `archive`, `artifact`, `setup`, or
`other` facets. A step matching several material facets remains one combined unit. Only a
separate successful package unit followed by failed or skipped publication may derive
`PARTIAL`; the official failure and exit code remain unchanged.

A successful publish or archive-verification step is reported as `step_success`, not as
an independent registry or archive query. External npm, Anaconda, GitHub Release, Git-ref,
and Zenodo verification; required gates; cross-workflow correlation; and package digest
inspection remain future work.

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
```

The CLI provides local `init [ROOT] [--write]`, `config check [PATH]`, and
`config explain WORKFLOW_PATH`. `init` scans only regular immediate workflow files,
proposes profiles from bounded filename and source signals, exposes confidence and reasons
on stderr, and retains ambiguous workflows as `generic`. Preview is the default;
`--write` refuses to replace existing policy. Version 1 accepts `generic`, `ci`, `conda`,
`docs`, and `release` profiles and the Conda `expected_platforms` and `package_kind`
settings. Package kind is `native` or `noarch`; a noarch rule cannot require native
platforms. Unknown fields fail validation instead of being ignored.

Repository configuration is trusted only when read from the repository's default branch.
A pull request cannot supply its own receptor rules and then use those rules to classify
the same pull request. The report records the configuration source, revision, schema
version, and digest. Explicit alternative trusted revisions remain future work.

## Future inline Action rules

A future GitHub Action may carry a small multiline rules document:

```yaml
- if: always()
  uses: uibcdf/gh-run-receptor@v1
  with:
    profile: conda
    rules: |
      expected_platforms: [linux-64, osx-64, win-64]
      artifact_pattern: "*.conda"
```

This syntax is design intent, not an implemented interface. If delivered, inline rules
will avoid an extra file for simple workflows. Repository configuration is preferred when
rules are shared, extensive, or need independent validation. Inline settings will never
be allowed to rewrite source conclusions.

## Matching and precedence

The implemented workflow matching order is:

1. an explicit CLI selection and profile;
2. an exact workflow path from trusted repository configuration;
3. a numeric workflow ID from trusted repository configuration;
4. an exact display name from trusted repository configuration;
5. conservative auto-detection;
6. the generic profile.

Future organization configuration and inline Action settings require their own explicit
trust and precedence gate. Later layers may refine interpretation but cannot alter
GitHub's authoritative states. Duplicate identities are a configuration error; list
order is not an implicit tie-breaker.

`config explain` shows the winning exact match and active values. A captured report shows
the trusted source path and revision. More detailed explanations of ignored candidates
remain future work.

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
