# Adaptive capture benchmark — 2026-09-17

## Decision under test

Issue `uibcdf/gh-run-receptor#41` asks when automatic inspection should download logs.
The candidate stable rule is:

```text
full OR (adaptive AND status == completed AND conclusion != success)
```

`metadata` never requests logs. `full` always requests them. `adaptive` does not infer
terminal state from duration, jobs, steps, or prose. A completed absent or unrecognized
conclusion requests logs because it is unresolved; an unrecognized status does not because
GitHub has not confirmed completion.

## Reproducible tool

`devtools/scripts/benchmark_capture_policies.py` discovers and validates local bundles,
recomputes the expected request decision, and reports structured bytes, observed log
bytes, unavailable requests, failed-job diagnoses, and full/adaptive pairs. It never
prints raw log content. It rejects duplicate source/policy identities and any bundle whose
observed log state contradicts the policy.

The committed corpus is checked with:

```text
python devtools/scripts/benchmark_capture_policies.py tests/fixtures/bundles
```

The hosted gate additionally captures a successful and terminal non-success run in both
modes, then requires both pair classes:

```text
python devtools/scripts/benchmark_capture_policies.py PAIR_ROOT \
  --require-paired-success --require-paired-non-success
```

Raw bundles stay in an owner-controlled temporary directory and are neither printed nor
uploaded as workflow artifacts.

## Paired result

Two completed gh-run-receptor runs with retained logs were captured locally in both modes:

| Run | GitHub conclusion | Adaptive total | Full total | Adaptive logs | Full logs | Diagnosed failed jobs |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `35224624974` | success | 29,966 B | 43,644 B | 0 B | 13,678 B | 0 / 0 in both |
| `35221505754` | failure | 27,322 B | 27,322 B | 5,397 B | 5,397 B | 1 / 1 in both |

For the successful run, adaptive avoided one request and 13,678 observed bytes, reducing
the captured bundle by 31.3% relative to full. For the failed run, adaptive and full
acquired equal bytes and produced equal diagnostic coverage. Across the two pairs the
benchmark reported 13,678 observed bytes saved and zero missing diagnoses.

## Opportunistic local corpus

A separate read-only inventory found 42 existing adaptive captures across UIBCDF and
three unrelated public repositories:

| State | Captures | Log requests | Log bytes | Structured bytes |
| --- | ---: | ---: | ---: | ---: |
| completed / success | 30 | 0 | 0 | 1,969,443 |
| completed / failure | 9 | 9 | 815,585 | 377,399 |
| completed / cancelled | 2 | 2 | 63,527 | 66,007 |
| in progress / absent conclusion | 1 | 0 | 0 | 88,695 |
| **Total** | **42** | **11** | **879,112** | **2,501,544** |

Adaptive avoided 31 of 42 possible log requests, or 73.8%. This is a request result, not a
byte-savings claim: the 30 skipped successful archives were not downloaded and their sizes
are unknown. Treating them as zero-byte counterfactuals would overstate the evidence.

The observed logs diagnosed 14 of 17 failed jobs. Three failed jobs had retained logs but
no cause recognized by the deliberately bounded parser. That is a log-analysis coverage
limit, not an adaptive acquisition miss. The paired non-success run demonstrates parity
with full for the measured case; it does not prove that every possible log is diagnosable.

## Committed incomplete and unknown cases

The 13-bundle committed corpus passes the policy benchmark. Its real PyUnitWizard failure
requested logs adaptively but received HTTP 410; the bundle retains six failed jobs,
records the unavailable request, remains replayable, and reports `INCOMPLETE` rather than
inventing a diagnosis. Sanitization now preserves `adaptive` for this bundle because no
log member was removed. A retained archive that is removed during sanitization still
becomes `metadata`.

The pure policy truth table covers every documented conclusion plus active, absent, and
unrecognized status/conclusion values. These synthetic boundary cases prove deterministic
behavior; they are not presented as live GitHub observations.

## Decision

The measured rule is accepted for the 0.22.0 candidate:

- `inspect` and the terminal capture made by `watch` default to `adaptive`;
- explicit archival `capture` defaults to `full`;
- remote `compare` and `aggregate` default to `metadata`;
- explicit `--capture` overrides every command default;
- adaptive requests no logs for active or completed successful runs;
- adaptive requests the complete attempt archive for a GitHub-confirmed completed
  conclusion other than `success`, including absent or unrecognized values;
- a failed required request makes evidence incomplete without changing GitHub truth.

The rule is run-level. Selective per-job downloads would change source provenance and
bundle construction and are not smuggled into this threshold decision.

## Limitations

The 42-capture inventory is opportunistic and dominated by gh-run-receptor validation
runs. Only two runs form paired full/adaptive evidence. Logs are retention-bound, and the
same endpoint can become unavailable later. The benchmark measures transfer and bounded
diagnosis, not API billing or all possible causal signatures. No raw log content or
credential-bearing request data is committed.
