# Configuration

Repository configuration selects a profile and bounded settings for an exact workflow
identity. It is declarative data, never executable code.

## Discover a starting configuration

From a repository checkout:

```bash
gh run-receptor init .
```

The command prints a proposal and discovery reasons. It does not overwrite anything. Write
the standard path only when you have reviewed the proposal:

```bash
gh run-receptor init . --write
```

The result lives at `.github/gh-run-receptor.yaml`.

## Minimal schema

```yaml
schema_version: 1
workflows:
  - match:
      path: .github/workflows/ci.yml
    profile: ci

  - match:
      path: .github/workflows/build-conda.yml
    profile: conda
    settings:
      package_kind: native
      expected_platforms:
        - linux-64
        - osx-arm64
        - win-64

  - match:
      path: .github/workflows/build-noarch.yml
    profile: conda
    settings:
      package_kind: noarch
```

Each rule has exactly one identity: exact `path`, positive numeric `id`, or exact display
`name`. Path has precedence over ID, and ID over name, when several distinct rules match.
Patterns, regular expressions, arbitrary settings, and executable expressions are
rejected rather than ignored. Pattern selectors and organization-level discovery are not
part of the stable 1.0 scope; adding either later requires a new explicit contract.

## Validate and explain

```bash
gh run-receptor config check .github/gh-run-receptor.yaml

gh run-receptor config explain .github/workflows/build-conda.yml
```

Validation is local and deterministic. `explain` shows the selected exact rule, profile,
package kind, and expected platforms without acquiring a run.

## Trust and provenance

Live acquisition reads repository configuration only from the target repository's default
branch. The evidence bundle records configuration source, revision, and digest. A pull
request cannot change its own rules and then use them to certify its run.

The Action accepts the same complete `config@1` document through its `rules` input for a
small dedicated reporter, but only when default-branch caller provenance is verified:

```yaml
      - uses: uibcdf/gh-run-receptor@1.1.0
        with:
          run-id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          rules: |
            schema_version: 1
            workflows:
              - match:
                  path: .github/workflows/ci.yml
                profile: ci
```

An explicit CLI `--profile` overrides the repository profile. Matched rule provenance
remains visible, but settings that do not apply to the explicit profile cannot silently
alter its assessment.

## When not to configure

The generic report is the safe fallback. Add a rule only when the workflow has a stable
identity and a specialized profile expresses evidence that GitHub actually exposes. Do not
encode project-specific success claims in filenames, job labels, or expected inputs.
