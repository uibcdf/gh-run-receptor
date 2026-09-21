# Embedded reporting

Embedded reporting publishes a compact report beside GitHub's ordinary logs. It does not
suppress output from other steps and does not change the source workflow conclusion.

## Recommended downstream Action

Run the reporter only after the source workflow is terminal:

```yaml
name: Compact CI report

on:
  workflow_run:
    workflows: [CI]
    types: [completed]

permissions:
  actions: read
  contents: read

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: uibcdf/gh-run-receptor@1.1.1
        with:
          run-id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          profile: ci
```

The Action prints bounded text, appends an escaped job summary, exposes scalar outputs,
and uploads a canonical JSON report artifact. The artifact name contains the source run ID
and attempt so reruns cannot overwrite historical identity.

Reporter faults are fail-open by default: the reporting step records its own error without
rewriting the product result. Set `strict-reporter: "true"` only in a controlled gate whose
purpose is validating the reporter itself.

## Reusable terminal reporter

The repository also provides a same-revision reusable workflow:

```yaml
name: Compact CI report

on:
  workflow_run:
    workflows: [CI]
    types: [completed]

permissions:
  actions: read
  contents: read

jobs:
  report:
    uses: uibcdf/gh-run-receptor/.github/workflows/reusable-report.yml@1.1.1
    with:
      run-id: ${{ github.event.workflow_run.id }}
      repository: ${{ github.repository }}
      profile: ci
```

Its typed outputs include assessment, GitHub conclusion, selected profile, failure and
incomplete counts, artifact name, ready state, and reporter error category. Runner versions
without GitHub's `$/` same-repository Action reference are not claimed.

## Consume the published report

When the canonical downstream workflow is named
`.github/workflows/gh-run-receptor-report.yml`, discover its report from the original run:

```bash
gh run-receptor --repo OWNER/REPO \
  published-source SOURCE_RUN_ID --receptor=llm
```

The consumer verifies reporter workflow identity, artifact digest and ZIP bounds, then
checks source run ID, attempt, commit, terminal state, conclusion, and URL against fresh
GitHub metadata. The report labels its profile interpretation as published rather than
independently recomputed.

For a custom reporter, consume an explicit artifact from its reporter run:

```bash
gh run-receptor --repo OWNER/REPO published REPORTER_RUN_ID \
  --artifact EXACT_ARTIFACT_NAME --receptor=llm
```

If the artifact expired or is insufficient, inspect the source run directly.

## Do not report an active source as complete

Calling the Action from inside the workflow being reported is permitted, but the honest
assessment is `PENDING`: the source run cannot be terminal while its reporting step is
executing. Prefer `workflow_run` or the reusable downstream workflow when a final verdict
is required.

## Permissions

Ordinary public reporting requires only:

```yaml
permissions:
  actions: read
  contents: read
```

Do not grant write permissions to a read-only receptor. Inline rules are accepted only
from a caller on the same repository's default branch; pull-request refs, feature branches,
tags, cross-repository targets, or missing provenance are rejected before acquisition.
