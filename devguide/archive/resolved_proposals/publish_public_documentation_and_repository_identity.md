---
summary: Publish public documentation and repository identity
issue: uibcdf/gh-run-receptor#40
status: resolved
opened: 2026-09-17
closed: 2026-09-17
verification: measured
area: ['documentation']
guard: tests/test_documentation.py
normative: ../docs/index.md
blocked_by: []
supersedes: []
---

# Publishing public documentation and repository identity

**Reported:** 2026-09-17, after the verified 0.21.1 rollout and comparison with the public
pytest-receptor presentation.
**Status:** Resolved; the public site, strict build/deploy workflow, tagline, homepage,
truthful status badges, and package/README links are published and independently verified.

## What

Give gh-run-receptor a concise public identity and publish a user-facing documentation
site before 1.0. The proposed GitHub tagline is:

> A GitHub Actions evidence receptor for coding agents: compact reports without hiding
> failures or uncertainty

The site is distinct from `devguide/`: it teaches installation, everyday use, Action and
reusable-workflow adoption, rules, profiles, contracts, output authority, security,
limitations, and measured token reduction. The developer checkpoint continues to carry
design history, release evidence, and internal workflow.

## How

Use the proven pytest-receptor structure: Sphinx, MyST Markdown, Read the Docs theme, a
strict warning-as-error build, and GitHub Pages deployment. Add a `docs` optional
dependency set without changing runtime dependencies. Build on pull requests and relevant
main changes; deploy only outside pull requests. Pin every third-party Action to an exact
commit and split the read-only build from the Pages/id-token deployment boundary.

Start with task-oriented pages rather than mirroring the README verbatim. Cross-link one
authoritative explanation per concept and test the workflow permissions, pins, navigation,
and strict local build. After the first hosted deployment, set the repository description
to the tagline and its homepage to the actual Pages URL returned by GitHub.

## Why

The tool has a verified public release and twelve MolSysSuite clients, but its GitHub
repository has neither description, homepage, topics, nor Pages site. A new user currently
has to mine a long README or an explicitly internal developer guide. That is an adoption
and trust gap: security boundaries and unsupported cases should be visible before someone
adds the Action to a workflow.

## What is measured and what is assumed

GitHub API queries on 2026-09-17 report for `uibcdf/gh-run-receptor`:

```text
description=null homepage=null has_pages=false topics=[]
```

The same query reports pytest-receptor with a descriptive tagline, a homepage, six topics,
and `has_pages=true`. Its Pages API reports `build_type=workflow` and `status=built`; its
repository contains nine task-oriented MyST pages and a strict Sphinx workflow. The local
MolSysSuite Python 3.13 environment already has Sphinx 8.2.3, MyST Parser 4.0.1, and
sphinx-rtd-theme 3.1.0, so local verification requires no dependency installation.

The official Action tags used by the reference workflow currently resolve to
`actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa` and
`actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`; the new workflow will pin those commits.

## What was refuted

- Keeping only the README was rejected because installation, security, contracts, and
  embedded modes already compete for one long linear document.
- Publishing `devguide/` directly was rejected because it contains internal checkpoints,
  historical evidence, and maintainer procedure rather than a stable learning path.
- Copying pytest-receptor wording or plugin-specific page structure was rejected; only its
  build architecture and task-oriented information design are reusable.
- Floating major Action tags were rejected because this repository already requires exact
  third-party revisions at workflow trust boundaries.
- Setting a guessed homepage before deployment was rejected; GitHub's observed Pages URL
  is the authority.

## Scope and exclusions

This work does not declare the CLI 1.0 contract complete, publish to PyPI or Conda, activate
Zenodo, add runtime dependencies, or expose internal archives as public documentation. It
does not promise private-fork behavior that has not been validated.

## Acceptance criteria

- The repository has an accurate tagline and observed Pages homepage.
- `docs/` has a navigable index and task-oriented pages covering every public delivery mode.
- Installation, permissions, source authority, exit codes, limitations, and fallback are
  findable without reading `devguide/`.
- `sphinx-build -W --keep-going` passes locally.
- The workflow builds on pull requests, deploys only trusted non-PR revisions, uses minimum
  permissions, bounded timeout, concurrency, and exact Action commits.
- Hosted Pages deployment succeeds and its public index is fetched after publication.
- README and package URLs point to the public documentation without replacing source,
  issue, changelog, or developer-guide links.
- README badges expose only real project surfaces and do not label a manual validation
  workflow as continuous test coverage.
- Tests guard the workflow trust boundary and the documentation navigation.

## Dependencies and risks

No code dependency blocks implementation. GitHub Pages must be enabled with workflow build
type before deployment; this is a reversible repository setting and will be performed only
after the build workflow is present. Public DNS/Pages propagation may be asynchronous.

## Provenance

Measured 2026-09-17 from GitHub's repository and Pages APIs and the local checkouts of
gh-run-receptor `80e47cb` and pytest-receptor main. Local environment: Linux
7.0.0-28-generic x86_64, Python 3.13.14, Sphinx 8.2.3, MyST Parser 4.0.1, and
sphinx-rtd-theme 3.1.0.

## Resolution

Commit `62b314d` added ten MyST source pages, optional bounded documentation dependencies,
the least-privilege pinned Pages workflow, README/package links, contributor instructions,
and executable repository guards. The completion checkpoint added badges for the policy
gate, documentation deployment, latest release, supported Python versions, and MIT license.
It deliberately omitted a generic “Tests” badge because the full compatibility workflows
are release gates rather than continuous push/PR checks. Local Sphinx completed with
warnings as errors and the full suite passed with 391 tests.

Hosted run `35224624974` passed both build and deploy jobs. Pages was enabled with workflow
build type, and independent HTTP checks returned 200 for every published page at
`https://www.uibcdf.org/gh-run-receptor/`. GitHub now exposes the proposed tagline and
that verified HTTPS homepage. The public site is the durable user-facing norm; devguide
retains implementation evidence and maintainer decisions.
