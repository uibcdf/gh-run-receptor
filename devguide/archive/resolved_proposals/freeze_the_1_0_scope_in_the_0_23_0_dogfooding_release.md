---
summary: Freeze the 1.0 scope in the 0.23.0 dogfooding release
issue: uibcdf/gh-run-receptor#47
status: resolved
opened: 2026-09-19
closed: 2026-09-19
verification: inspected
area: ['governance', 'packaging', 'tests']
guard:
normative: release_readiness_1_0.md
blocked_by: []
supersedes: []
---

# Freezing the 1.0 scope in the 0.23.0 dogfooding release

**Reported:** 2026-09-19, after the defined 1.0 implementation and evidence roadmap
reached full credit while the repository still had no stable 1.0 contract.
**Status:** Resolved; the stable scope is normative and the complete 0.23.0 dogfooding
sequence is observed.

**Progress:** The normative scope/evidence map is implemented, OD-003 and OD-004 are
explicitly post-1.0, and executable guards reject both deferred configuration shapes.
The 0.23.0 source candidate passes 442 tests, Ruff lint, strict Sphinx, citation and
release-note validation, developer-report validation, and all nine frozen contracts.
Candidate and exact-tag hosted gates, draft-first publication, independent artifact and
Zenodo verification, client-guide synchronization, and public-wheel MolSysMT dogfooding
are complete. Pages run `35464444035` confirms that the explicit `main` authority guard
retains the strict build and successful deployment while tags remain build-only.

## What

Use 0.23.0 as the final pre-1.0 dogfooding release. Freeze what 1.0 does and does not
promise, map every release-readiness claim to durable evidence, and exercise the complete
release and installed-product path once more before publishing 1.0.

The implementation roadmap reports 100% evidence credit toward the defined 1.0 scope.
That percentage deliberately does not mean that the stable tag is published. Two design
questions also remain under an “open decision gates” heading even though neither pattern
matching nor organization-level configuration belongs in the defined 1.0 product. That
wording leaves avoidable ambiguity about whether they block the tag.

## How

The increment has three parts:

1. Publish one normative 1.0 readiness record that maps every roadmap requirement to its
   implementation, local guard, hosted evidence, and remaining release-time observation.
2. Resolve OD-003 and OD-004 for 1.0 by retaining exact workflow selectors and
   repository/inline configuration only. Pattern rules and organization-level discovery
   remain possible post-1.0 additions behind new evidence and explicit contract decisions;
   they are not implicit promises of the stable release.
3. Prepare and validate 0.23.0 from an exact candidate commit. It retains all nine frozen
   serialized contracts and exercises the full local, installed-wheel, hosted,
   documentation, release, and Zenodo observation sequence used by the published product.

A readiness validator may protect objective repository properties, but it must not award
readiness because prose contains expected words. Semantic behavior remains guarded by the
existing tests, schema comparisons, builds, hosted workflows, and public-release checks.
The readiness record connects those independent guards rather than replacing them.

## Why

A stable major version is a compatibility promise. Publishing it from a percentage or an
informal impression would make the promise difficult to audit and repeat. Conversely,
adding attractive post-1.0 features now would expand the contract after the evidence plan
has already closed. A final dogfooding release lets MolSysSuite use the complete product,
exposes release-path regressions, and makes the subsequent 1.0 decision depend on a finite
set of recorded facts.

## What is measured and what is assumed

Observed on 2026-09-19:

- `devguide/development_roadmap.md` assigns 100% implementation/evidence credit to the
  defined 1.0 scope and explicitly distinguishes that result from publishing the tag.
- all nine registered serialized boundaries are frozen against published tags;
- 0.22.0 has a verified GitHub Release, installed-product gates, public documentation,
  and independently observed Zenodo version and concept DOI evidence;
- the only open product issue before opening this report was post-1.0 issue
  `uibcdf/gh-run-receptor#46`, blocked by the central ownership decision
  `uibcdf/molsyssuite#25`;
- OD-003 and OD-004 still appeared as open decisions, but their gates are triggered only
  by capabilities outside the current exact-selector, repository-local 1.0 boundary.

These observations were made with:

```text
git status --short --branch
gh issue list --repo uibcdf/gh-run-receptor --state open --limit 100
python devtools/scripts/validate_contracts.py --baseline 0.21.0
rg -n "OD-003|OD-004|1.0|0.23" devguide CHANGELOG.md
```

The remaining 0.23.0 hosted run IDs, exact candidate commit, artifact hashes, installation
result, and Zenodo state are not assumed. They will be added only after observation.

## What was refuted

- **Publish 1.0 immediately because the roadmap says 100%.** Refuted: implementation
  credit does not exercise the final candidate and publication path or define the exact
  compatibility promise.
- **Implement pattern and organization rules before 1.0.** Refuted: neither is needed for
  the measured product, and each introduces a new trust, precedence, and compatibility
  surface without corresponding corpus evidence.
- **Treat a checklist document as a new semantic gate.** Refuted: a gate that verifies
  only expected prose can be satisfied without the protected behavior. Existing tests and
  hosted observations remain authoritative.
- **Call 0.23.0 a release candidate suffix.** Refuted: MolSysSuite uses three-component
  tags without annotations. Dogfooding intent belongs in the release record, not the tag.

## Scope and exclusions

This report covers the final pre-1.0 scope audit and 0.23.0 release. It does not add:

- glob or regular-expression workflow selectors;
- organization-level configuration discovery;
- mutation of GitHub state;
- a second authentication or transport system;
- claims of broad GitHub Enterprise, private-repository, or fork coverage beyond measured
  permissions and documented fallback behavior;
- verification of external package registries from successful workflow-step names;
- the post-1.0 producer-timeout project tracked by `uibcdf/gh-run-receptor#46` and
  `uibcdf/molsyssuite#25`.

Package-index publication is also not invented by this milestone: the supported GitHub
Release/extension installation route remains the distribution boundary unless separately
proposed and evidenced.

## Acceptance criteria

- One normative readiness document defines the stable 1.0 support and exclusion boundary
  and maps every roadmap requirement to a real guard or observation.
- No decision whose trigger lies inside the 1.0 boundary remains open.
- The public README, documentation, client guide, roadmap, checkpoint, decision record,
  and release policy agree on the boundary.
- 0.23.0 retains all nine serialized contract freezes and introduces no incompatible
  contract mutation.
- The full local suite passes with `pytest --receptor=llm`, Ruff, strict Sphinx,
  developer-report validation, citation validation, and contract validation.
- The exact candidate builds wheel and source distribution; the wheel installs outside
  the checkout, reports 0.23.0, and passes a representative offline command.
- Required exact-revision and exact-tag hosted gates pass and are inspected through
  gh-run-receptor with native fallback for any incomplete evidence.
- The draft-first GitHub Release, downloaded assets, hashes, tag identity, public install,
  and independent Zenodo result are recorded before this report closes.
- The canonical client guide is synchronized only after the public release it names.

## Dependencies and risks

There is no external blocker to preparing 0.23.0. GitHub-hosted runners, GitHub Release,
Pages, and Zenodo are external observations and may delay closure without changing local
readiness. The principal product risk is accidentally widening 1.0 while auditing it; any
new capability discovered here requires its own issue and evidence rather than silent
inclusion.

## Provenance

Initial audit: Linux development checkout, Python 3.13.14, GitHub CLI 2.93.0, Sphinx
8.2.3, 2026-09-19. Exact hosted runner evidence will be recorded with the candidate
validation results.
