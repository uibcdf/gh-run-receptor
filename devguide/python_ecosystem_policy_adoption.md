# Python ecosystem policy decisions for GH Run Receptor

This repository applies the [MolSysSuite member policy at
`policy-v1.5.2`](https://github.com/uibcdf/molsyssuite/blob/policy-v1.5.2/devguide/python_ecosystem_policy.md).
This page records member-specific decisions under
[uibcdf/gh-run-receptor#55](https://github.com/uibcdf/gh-run-receptor/issues/55);
MolSysSuite owns the common rule.

## Development tools

The test and development extras pin the published pytest-receptor 1.1.0.
Hosted pytest commands use `--receptor=ci`; local agent runs use
`--receptor=llm`. The routine and twelve-cell weekly matrix verified the
published pin under Python 3.11–3.14 on Linux, macOS, and Windows. GH Run
Receptor inspects Actions runs first, with GitHub's native conclusions as
authority.

## Support-library applicability

The runtime package has no Python dependencies. Its public CLI and Action
consume untrusted GitHub data through bounded, versioned parsers. Changing a
parser or the diagnostic channel requires the source-truth, exit-code, and
security tests in this repository; an installed library alone cannot satisfy
those contracts.

| Library | Local decision | Evidence and reassessment |
| --- | --- | --- |
| ArgDigest | CLI arguments are parsed by `argparse`, which owns usage errors and exit status 64. Config, bundle, and report values are document/schema and trust-boundary inputs, rather than decorated Python call arguments. Adding a second argument layer would duplicate these validators and change the dependency-free runtime without replacing the schema checks. | `tests/test_cli.py::test_invalid_run_reference_is_rejected`, `tests/test_cli.py::test_watch_rejects_non_finite_or_subsecond_intervals`, and `tests/test_embedded.py::test_invalid_inline_rules_fail_before_acquisition`. Reassess if a public Python API starts accepting domain arguments outside those parsers. |
| DepDigest | The `gh` executable is the required authenticated transport, checked by the GitHub adapter. Receptor selects no optional Python backend or heavy integration at runtime. | Reassess if an optional transport or parser backend is introduced. |
| SMonitor | Receptor itself produces user-facing diagnostic reports, `RECEPTOR_ERROR` categories, Action outputs, and exit codes. Those channels are its product contract; redirecting them through another sink would alter the contract without adding a missing diagnostic. | `tests/test_cli.py::test_acquisition_error_exposes_category_and_keeps_exit_five` and `tests/test_embedded.py::test_invalid_inline_rules_fail_before_acquisition`. Reassess if diagnostics are exported to an independent consumer channel. |
| PyUnitWizard | GitHub durations and byte counts are fixed-source reporting metadata. No user quantity is parsed, converted, or checked dimensionally. | Reassess if a physical-quantity field needing conversion or dimensional checks enters the public model or artifact schema. |

These are current non-applicability decisions for the support libraries, not a
claim that they are installed. The runtime remains dependency-free while these
boundaries hold. New boundaries require member review and issue evidence.
