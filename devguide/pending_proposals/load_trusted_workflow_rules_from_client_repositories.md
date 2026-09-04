---
summary: Load trusted workflow rules from client repositories
issue: uibcdf/gh-run-receptor#5
status: open
opened: 2026-09-04
closed:
verification: asserted
area: ['profiles', 'security', 'cli']
guard:
normative:
blocked_by: []
supersedes: []
---

# Loading trusted workflow rules from client repositories

**Reported:** 2026-09-04, while preparing MolSysMT as the first client repository.
**Status:** Open; the first exact-match configuration slice is under implementation.

## What

Add a real, validated `.github/gh-run-receptor.yaml` contract before asking client
repositories to add configuration. The first slice assigns the implemented `generic` or
`conda` profile by exact workflow path, repository-local numeric ID, or display name. A
Conda rule may additionally declare the recognized native platforms that must be present.

## How

Capture reads the configuration only from the repository default branch through the
GitHub contents API. It parses an intentionally narrow YAML subset without a runtime
dependency or executable YAML features, normalizes the rules, and stores the normalized
document plus path, branch, blob SHA, and content SHA-256 as `config.json` in the evidence
bundle. Replay uses that captured policy and never consults the current checkout.

Matching is exact. Path outranks numeric ID, which outranks display name. An explicit CLI
profile still wins over the repository profile. Unknown fields, profiles, platforms,
duplicate identities, ambiguous YAML features, and oversized documents fail closed as
configuration errors. `config check` validates a local candidate and `config explain`
shows the selected rule without making that local file policy for remote inspection.

## Why

Without an active configuration contract, a client file is dangerous documentation: it
looks like a gate while the receptor ignores it. Trusted repository rules also let
MolSysMT state that its Conda workflow is a Conda workflow even when a single-platform run
cannot satisfy conservative auto-detection. Expected platforms turn a GitHub-successful
but incomplete matrix into a receptor `FAIL` while preserving GitHub's source conclusion.

## What is measured and what is assumed

Observed behavior is covered by parser, CLI, bundle, report truth-table, and schema tests
run with:

```text
python -m pytest --receptor=llm
```

No token-reduction or runtime claim is added by this proposal. The existing benchmark is
independent of repository configuration.

## What was refuted

- Loading the pull-request checkout was rejected because a change must not define the
  policy used to certify itself.
- General YAML loading was rejected for the initial dependency-free release because the
  accepted contract is small and executable or ambiguous YAML features add risk.
- Patterns were deferred; exact workflow identity is sufficient for MolSysMT and avoids
  claiming pattern semantics before their safety contract exists.
- Arbitrary rule keys were rejected because accepting inert or misspelled criteria would
  create false confidence.

## Scope and exclusions

This slice does not implement CI, documentation, or release profiles; workflow discovery
or `init`; path or name patterns; inline Action rules; organization policy; arbitrary
local configuration for `inspect`; artifact patterns; expected Python versions; or
mutation.

## Acceptance criteria

- A valid default-branch configuration is captured with immutable provenance and replayed.
- A missing configuration remains compatible with existing bundles and auto-detection.
- Exact path, ID, and name matching have deterministic precedence.
- Unknown or ambiguous input fails with a bounded receptor error.
- `expected_platforms` cannot turn an official failure into success and makes missing
  required platforms visible and unsuccessful.
- `config check` and `config explain` behave without network access.
- MolSysMT adopts the file only after a released receptor version enforces it.

## Dependencies and risks

No tracked dependency blocks the initial slice. The GitHub contents API requires
`contents: read`; absence of the optional file is a normal 404, while other acquisition
failures remain errors. Fetching one repository resource per new capture adds API latency,
but replay remains offline and cache reuse does not repeat the request.

## Provenance

Implementation tests run on 2026-09-04 on the local Linux development host with Python
3.13 and the repository development dependencies. No performance measurement is claimed.
