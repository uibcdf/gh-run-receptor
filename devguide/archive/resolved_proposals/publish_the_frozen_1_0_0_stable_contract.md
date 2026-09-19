---
summary: Publish the frozen 1.0.0 stable contract
issue: uibcdf/gh-run-receptor#48
status: resolved
opened: 2026-09-19
closed: 2026-09-19
verification: measured
area: ['governance', 'packaging', 'tests', 'documentation']
guard:
normative: release_readiness_1_0.md
blocked_by: []
supersedes: []
---

# Publishing the frozen 1.0.0 stable contract

**Reported:** 2026-09-19, after the complete 0.23.0 readiness and public dogfooding
sequence closed `uibcdf/gh-run-receptor#47`.
**Status:** Resolved; 1.0.0 is public and every stable-release observation passes.

**Progress:** The stable surfaces, 1.0.0 pins, citation, release notes, maturity classifier,
and preview-language guard are implemented. The local source gate passes 443 tests, Ruff,
strict Sphinx, report-lifecycle validation, citation validation, and all nine frozen
contracts. Exact-commit and exact-tag hosted gates, draft-first publication, independent
assets, Zenodo, public-wheel MolSysMT dogfooding, and twelve-client guide synchronization
all pass.

## What

Publish 1.0.0 as the stable form of the already frozen, released, and dogfooded product
boundary. This milestone changes lifecycle status and public pins; it does not add a
profile, command, schema, transport, permission, or mutation capability.

## How

Prepare one exact commit that:

- moves the 0.23.0 changelog contents into a 1.0.0 stable-release section without
  rewriting the historical 0.23.0 record;
- updates citation metadata, installation examples, Action/reusable-workflow pins, the
  canonical client guide, and package maturity classification to 1.0.0;
- replaces preview wording with the normative support and exclusion boundary in
  `release_readiness_1_0.md`;
- retains all nine serialized contract resources byte-for-byte against their original
  publishing tags;
- repeats the local, exact-commit, exact-tag, draft-first publication, public artifact,
  installed-product, Zenodo, Pages, and client-guide synchronization gates.

The tag is the three-component lightweight tag `1.0.0`. No release-candidate suffix and no
moving tag are permitted.

## Why

Version 0.23.0 completed every finite readiness observation: cross-platform installation,
frozen contracts, public release assets, Zenodo, twelve synchronized clients, and
installed-wheel truth parity on a real MolSysMT workflow. Continuing to call that boundary
a preview would understate its tested compatibility promise, while adding new features now
would invalidate the audited scope.

## What is measured and what is assumed

Measured and recorded in `devguide/mvp_validation.md`:

- 442 local tests, Ruff, strict Sphinx, citation, report lifecycle, and nine frozen
  contracts pass;
- the 0.23.0 candidate and exact tag passed Linux, macOS, Windows, Python 3.11--3.13,
  GitHub CLI 2.48.0, Action, reusable-workflow, documentation, and release gates;
- public 0.23.0 assets and isolated installation were independently verified;
- Zenodo version DOI `10.5281/zenodo.22848495` was independently observed;
- the public wheel preserved GitHub truth for real MolSysMT run `35196968944`;
- the 0.23.0 guide is byte-identical in all twelve tracked client repositories;
- the only open product issue is blocked post-1.0 proposal
  `uibcdf/gh-run-receptor#46`; no critical or high defect is open.

No 1.0.0 build, hosted run, public asset, or Zenodo record is assumed before it is
observed and recorded.

## What was refuted

- **Add deferred pattern, organization, timeout-producer, or mutation features first.**
  Refuted by the frozen scope: each requires a separate post-1.0 contract and evidence
  decision.
- **Rename 0.23.0 as 1.0.0 or move its tag.** Refuted by immutable release identity and
  the repository's version policy.
- **Skip the release gates because 1.0.0 changes only lifecycle language.** Refuted: the
  public pins, metadata, distributions, exact tag, and hosted consumers are themselves
  release behavior.
- **Introduce a package-index publication route in 1.0.0.** Refuted: it was not part of
  the audited distribution promise.

## Scope and exclusions

The exclusions in `release_readiness_1_0.md` are unchanged. This report does not implement
new product behavior, broaden private/fork/GitHub Enterprise claims, publish to PyPI or
Conda, infer external delivery from workflow prose, or begin the post-1.0 timeout producer
project.

## Acceptance criteria

- Public and developer documentation describe a stable 1.0 boundary without obsolete
  preview language or contradictory support claims.
- All public install, Action, reusable-workflow, validation-workflow, citation, and
  canonical-guide pins identify 1.0.0.
- The package maturity classifier and release notes agree with the stable lifecycle.
- The complete local gate passes, including all nine immutable contract comparisons.
- A clean exact-commit temporary tag builds and installs as 1.0.0 outside the checkout.
- Candidate and exact-tag hosted gates pass according to the readiness matrix.
- The draft-first GitHub Release, downloaded assets, hashes, installed wheel, stable
  process statuses, Zenodo record, and one real MolSysSuite inspection are independently
  verified.
- The canonical 1.0.0 guide is synchronized only after the public release exists.
- The GitHub issue and archived report identify the exact stable commit and normative
  compatibility boundary.

## Dependencies and risks

There is no product blocker. Hosted services can delay an observation without weakening
the gate. The primary risk is accidental scope expansion or a stale 0.23.0 pin; repository
searches and behavioral/hosted tests must fail those conditions before publication.

## Provenance

Linux development checkout, Python 3.13.14, GitHub CLI 2.93.0, Sphinx 8.2.3,
gh-run-receptor public 0.23.0 evidence, 2026-09-19. Exact 1.0.0 hosted and public evidence
will be appended as it is observed.
