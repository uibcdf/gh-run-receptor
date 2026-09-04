# MolSysMT Conda pilot benchmark — 2026-09-04

## Subject and environment

This is a single-run pilot, not an aggregate product claim.

| Field | Value |
| --- | --- |
| Repository | `uibcdf/molsysmt` |
| Workflow | `.github/workflows/test_conda_rattler.yaml` |
| Run and attempt | `33863426589`, attempt 1 |
| GitHub conclusion | `failure` |
| Receptor source | commit `9acd4bb`, development snapshot included in `0.1.1` |
| GitHub CLI | 2.93.0 |
| GitHub API version | `2022-11-28` |
| Capture | adaptive, complete; logs and artifact inventory fetched |
| Manifest SHA-256 | `701a65a635e1a309587431fd813be514f72b644e9ca2064f1c3bfa464a1759d5` |
| Token counter | tiktoken 0.13.0 |

The expected diagnosis was reviewed against bounded context from both failed members:
macOS Bash 3 does not provide `mapfile`; both jobs failed at the same artifact-inspection
step with exit code 127. Three other platforms retained artifacts.

## Competent native baseline

The baseline deliberately does not send the raw failed log directly to the reader. It
uses native GitHub tools, local filtering, and three complementary outputs:

```text
gh run view 33863426589 --repo uibcdf/molsysmt \
  --json status,conclusion,jobs,name,url,workflowName \
  --jq '{status,conclusion,workflow:.workflowName,jobs:[.jobs[]|{name,conclusion,failed_steps:[.steps[]|select(.conclusion=="failure")|.name]}]}'

gh run view 33863426589 --repo uibcdf/molsysmt --log-failed > failed.log
rg -i -C 3 'error|failed|failure|traceback|exception|fatal|exit code|command not found' failed.log

gh api /repos/uibcdf/molsysmt/actions/runs/33863426589/artifacts \
  --jq '[.artifacts[]|{name,size_in_bytes,expired}]'
```

Only the structured output, filtered matches, and artifact inventory count as reader input.
The raw `--log-failed` output is an intermediate local file, just as the receptor's ZIP is
local evidence rather than reader input.

| Baseline component | Lines | Bytes | `cl100k_base` tokens |
| --- | ---: | ---: | ---: |
| Structured run/jobs | 1 | 755 | 183 |
| Locally filtered failed logs | 99 | 12,252 | 4,859 |
| Artifact inventory | 1 | 284 | 96 |
| **Combined competent baseline** | **101** | **13,291** | **5,138** |

For context only, unfiltered `--log-failed` produced 8,334 lines, 1,249,506 bytes, and
478,294 `cl100k_base` tokens. It is not used as the headline baseline.

## Receptor result

The receptor command was:

```text
gh-run-receptor --receptor=llm replay BUNDLE
```

Its output contained 12 lines, 908 bytes, and 296 `cl100k_base` tokens. It preserved the
official failure and exit status 1 while adding the `PARTIAL` interpretation, five-platform
coverage, three reusable artifacts, one grouped cause with two occurrences, and a precise
evidence pointer.

| Tokenizer | Competent baseline | Receptor | Reduction |
| --- | ---: | ---: | ---: |
| `cl100k_base` | 5,138 | 296 | 94.2% |
| `o200k_base` | 5,194 | 293 | 94.4% |
| `p50k_base` | 5,435 | 332 | 93.9% |
| `r50k_base` | 6,295 | 334 | 94.7% |

## Interpretation and limits

This run clears the provisional 90% reduction target against an intentionally competent
baseline across all four measured tokenizers. It also yields more workflow semantics than
the baseline. It proves usefulness for this captured Conda failure, not a general accuracy
or savings rate.

The next benchmark set must include successful runs, independent failures, non-Conda CI,
documentation, cancellation, incomplete evidence, rerun attempts, and cases where generic
filtering is already very small. Commands should move into a reproducible harness before
aggregate numbers are published.

## Successful Conda sensitivity case

Commit `7446bca` was also replayed against MolSysMT run `33849332945`, attempt 1. GitHub
reported success for all six jobs and all five native Conda platforms. No GitHub artifacts
were retained. The complete adaptive bundle manifest has SHA-256
`63906d73852aeac6bbf602e3c3f45f7fa9dd23b4b6e9d010fab1d14875f47d89`.

For a consumer verifying workflow, job/platform coverage, and artifact inventory, the
native baseline used the same structured jobs query and artifact query as above, with no
log query. It produced 609 bytes. The one-line receptor report produced 115 bytes:

| Tokenizer | Native verification baseline | Receptor | Reduction |
| --- | ---: | ---: | ---: |
| `cl100k_base` | 143 | 39 | 72.7% |
| `o200k_base` | 144 | 40 | 72.2% |
| `p50k_base` | 160 | 43 | 73.1% |
| `r50k_base` | 160 | 43 | 73.1% |

There is an important counterpoint. If the consumer asks only whether the run succeeded,
this native query is already smaller:

```text
gh run view 33849332945 --repo uibcdf/molsysmt \
  --json status,conclusion --jq '{status,conclusion}'
```

It produced 46 bytes and 10 `cl100k_base` tokens, versus the receptor's 39. The receptor
must not claim savings for that narrower question. Its extra tokens establish platform/job
coverage, artifact availability, profile, repository, and run identity. A future brief or
transition-only monitoring mode should be compared separately; users needing only a
one-time binary status should continue to use the native query.
