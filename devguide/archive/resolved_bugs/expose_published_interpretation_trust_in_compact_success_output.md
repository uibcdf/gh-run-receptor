---
summary: Expose published interpretation trust in compact success output
issue: uibcdf/gh-run-receptor#20
status: resolved
opened: 2026-09-06
closed: 2026-09-06
severity: medium
verification: reproduced
area: ['reports']
guard: tests/test_published.py
normative:
blocked_by: []
supersedes: []
---

# Expose published interpretation trust in compact success output

**Reported:** 2026-09-06, while reviewing the installed 0.13.0 command against its live
published artifact.
**Status:** Resolved; published compact success now carries both structured trust values.

## What

`published` adds `consumer_verification.interpretation=published_not_recomputed` and a
warning to the canonical report, but the successful LLM renderer returns its one-line
summary before it visits warnings. The compact output therefore omits the trust distinction:

```text
gh run-receptor published 34045953527 --repo uibcdf/gh-run-receptor \
  --artifact terminal-source-report --receptor=llm
```

## How

`render_llm` has an intentional fast path for `PASS`. Ordinary success warnings were not
expected when it was written. Published consumption introduced a security-relevant warning
without adding its structured verification fields to that fast path.

## Why

The official conclusion remains correct and JSON is explicit, so this does not manufacture
success. It does make artifact-derived profile interpretation look independently verified
to the primary agent-facing receptor, contradicting the new trust contract.

## What is measured and what is assumed

The installed 0.13.0 extension prints one successful line without `source_facts` or
`published_not_recomputed`; `--format=json` on the same run contains both fields and the
warning. This is directly reproduced, not inferred.

The regression failed against the 0.13.0 renderer and passes after the fast path appends
`source_facts=verified` and `interpretation=published_not_recomputed`. A live source-checkout
invocation against reporter run `34045953527` displays both fields while preserving the
one-line success form. The complete suite passes 211 tests.

## What was refuted

- Removing the successful fast path is rejected because its bounded one-line form is a core
  token-economy behavior.
- Relying on the generic warning list is rejected because this fast path deliberately omits
  it.
- Marking all published reports incomplete is rejected because source facts were freshly
  verified and the distinction concerns interpretation provenance.

## Scope and exclusions

Add the two structured trust values to successful compact output. General success-warning
policy and cryptographic producer attestation remain outside this fix.

## Acceptance criteria

- Ordinary locally computed success output remains byte-identical.
- Published success output includes `source_facts=verified` and
  `interpretation=published_not_recomputed` on its bounded line.
- Human and JSON output retain their existing details.
- The live installed command exposes the distinction.

## Dependencies and risks

There is no blocker. Because 0.13.0 is immutable, the fix requires a 0.13.1 patch tag rather
than moving the release tag.

## Provenance and guard

Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.13.0 and the 0.13.1
release candidate, 2026-09-06.
