# 1.0 release readiness

This document is the normative scope and evidence map for the first stable release. It
does not replace the tests, hosted workflows, public-service observations, or release
procedure that it cites. A checked claim is valid only while its named guard continues to
pass.

## Stable product boundary

Version 1.0 is a read-only GitHub Actions evidence receptor delivered as a Python package,
GitHub CLI script extension, composite Action, and reusable reporting workflow. Its
supported environment is:

- Python 3.11 through 3.13 on Linux, macOS, and Windows;
- GitHub CLI 2.48.0 or newer for network commands, with the latest patched stable release
  recommended;
- `github.com` as the measured host;
- exact workflow selection by path, positive numeric ID, or exact display name;
- built-in `generic`, `ci`, `docs`, `conda`, and `release` profiles;
- the nine serialized v1 resources listed in `data_contracts.md` and frozen against their
  first publishing releases;
- authoritative GitHub state preserved separately from bounded receptor interpretation.

The supported installation routes are the exact GitHub Release wheel and source archive,
and the exact-tag GitHub CLI extension. PyPI, Conda, a standalone binary, and a floating
branch installation are not 1.0 distribution promises.

## Explicit exclusions

The following capabilities are not required for 1.0 and cannot be inferred from its
contracts:

- glob or regular-expression workflow selectors;
- organization-level configuration discovery or precedence;
- mutation such as rerun, cancellation, approval, upload, or deployment;
- a second authentication or GitHub transport implementation;
- general log search or arbitrary executable configuration;
- broad GitHub Enterprise Server, private-repository, or fork-token compatibility beyond
  the documented measured behavior;
- external registry, Git tag, GitHub Release, deployment, or archive verification derived
  from workflow names, step names, logs, or Actions artifacts;
- producer-owned structured timeout evidence tracked after 1.0 by
  `uibcdf/gh-run-receptor#46` and `uibcdf/molsyssuite#25`.

Adding one of these later requires its own issue, evidence, trust analysis, and contract
decision. No excluded capability may be smuggled into an existing frozen v1 resource.

## Evidence matrix

| 1.0 requirement | Executable or measured evidence | Release-time observation |
| --- | --- | --- |
| Versioned evidence and report schemas | `tests/test_contracts.py`, `tests/test_contract_compatibility.py`, and `devtools/scripts/validate_contracts.py` | Exact-tag contract workflow passes against every first-publishing tag |
| GitHub truth, incompleteness, and degraded-mode semantics | `tests/test_report.py`, `tests/test_exit_codes.py`, `tests/test_bundle.py`, and the committed sanitized corpus | Candidate and installed wheel preserve the same source conclusions and statuses |
| Deterministic replay | CLI process-boundary replay tests in `tests/test_cli.py` across paths, times, time zones, and all renderers | Candidate wheel replays a reviewed bundle outside the checkout |
| Bounded and terminal-safe output | renderer bounds in `tests/test_report.py`, aggregation/comparison bounds, and adversarial text tests in `tests/test_logs.py` | Hosted reports remain bounded; native fallback is used on incomplete evidence |
| Configuration and pull-request trust | `tests/test_config.py`, `tests/test_embedded.py`, and `tests/test_inline_rules_pr_workflow.py` | Exact-revision inline-rules boundary gate passes |
| Archive, artifact, credential, and resource safety | `tests/test_bundle.py`, `tests/test_published.py`, `tests/test_events.py`, and `security.md` | Distributed Action and published-report gates pass without raw evidence publication |
| Token economy without semantic misses | `benchmark_2026-09-04.md`, `benchmark_watch_2026-09-19.md`, and `docs/benchmarks.md` | Candidate changes do not invalidate the measured corpus or tokenizer inputs |
| Portable installation | `tests/test_compatibility_workflow.py` and `compatibility.yml` | Nine Python/OS jobs build, install, import, and execute outside the checkout |
| GitHub CLI floor | `tests/test_minimum_gh_cli_workflow.py` | Checksum-pinned 2.48.0 extension installation and network boundary pass |
| CLI, Action, and reusable-workflow parity | shared model/renderer tests plus Action and reusable-workflow workflow guards | Exact-tag distributed Action and reusable reporting gates pass |
| Repository-agnostic behavior | `tests/test_public_runs.py` and the non-UIBCDF corpus recorded in `mvp_validation.md` | Any new candidate-specific portability claim is observed, not inferred |
| Contract migration rules | `tests/test_contract_compatibility.py`, the runtime registry, and `data_contracts.md` | All nine current resources remain byte-compatible; a new resource uses a new version |
| External-release truth | `tests/test_release_tools.py`, `tests/test_zenodo_verification.py`, and the release authority-map guards | Draft/public assets, tag identity, hashes, installed wheel, and Zenodo are queried independently |
| Documentation accuracy | `tests/test_documentation.py` and strict Sphinx build | Published site and canonical client guide name the public tag and current boundaries |

The detailed run IDs, candidate commits, artifact hashes, and public DOI observations live
in `mvp_validation.md`. That evidence log is append-only in meaning: later results may
supersede a candidate, but a failed or absent observation is never rewritten as success.

## Final sequence

The stable tag is eligible only after this finite sequence:

1. publish 0.23.0 through the exact-tag, draft-first release workflow;
2. pass its full local gate, nine-platform/interpreter compatibility gate, contract gate,
   minimum-GitHub-CLI gate, distributed Action gate, reusable-report gate, and strict
   documentation build;
3. independently verify the public tag, assets, hashes, isolated wheel import, and Zenodo
   record;
4. synchronize the canonical 0.23.0 client guide after the public release exists;
5. use the installed public 0.23.0 product on at least one real MolSysSuite workflow and
   record source-truth parity and any limitation;
6. confirm that no unresolved critical or high defect affects the stable boundary.

There is no arbitrary waiting period and no percentage judgment after these checks. A
defect found during dogfooding reopens the affected evidence row; a desired excluded
feature does not block 1.0.

## Current checkpoint

As of 2026-09-19, the implementation/evidence rows are complete through published 0.22.0
and the 1.0 scope is frozen. The 0.23.0 candidate, public-release observations, client-guide
synchronization, and public-version dogfooding steps remain open. Therefore this document
records a release-ready scope, not a published 1.0 release.
