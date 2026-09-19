# Watch polling and output benchmark — 2026-09-19

## Decision under test

Issue `uibcdf/gh-run-receptor#42` closes OD-005 by defining a calculable polling schedule,
transition-only output, a safe terminal handoff, and an explicit GitHub API budget. The
comparison baseline is `gh run watch --compact`, not an unfiltered log stream.

## Stable polling contract

`watch` uses a 10-second initial interval and a 60-second maximum by default. Both CLI
values must be finite and at least one second. If `--max-interval` is lower than
`--interval`, the effective maximum is the interval.

After a successful unchanged snapshot, the next delay is multiplied by 1.5 up to the
maximum. Any emitted job or run transition resets the delay to the initial interval. An
acquisition failure doubles the delay up to the maximum; the first two consecutive
failures emit one bounded degraded message each and the third aborts. A successful poll
resets the failure counter. There is deliberately no jitter: this is a local CLI rather
than a fleet service, and deterministic delays make latency and request budgets
reproducible.

Progress contains one initial line for an active run and then only observed job discovery,
rename, state, conclusion, completion, run-state, terminal, or degraded-acquisition
changes. An already completed run emits no progress. Exactly one ordinary final report is
written to stdout.

## API budget

For each successful current-attempt snapshot, the receptor performs one run request plus
`J` jobs requests, where `J` is the number of 100-job pages returned by GitHub. A selected
historical attempt adds one attempt-specific run request per snapshot. A failed snapshot
can consume one or more requests before the failure; pagination makes that cost dependent
on where the failure occurs. Three consecutive failures bound one uninterrupted degraded
sequence, but later successful polls reset that bound.

On a fresh terminal capture, the final report may additionally request workflow metadata,
artifact pages, eligible producer-event artifacts, check-run pages, repository metadata,
the default-branch configuration, and — according to the capture policy — one log archive.
The terminal run and merged jobs collection from the final successful poll are handed to
the capture layer only after run ID, attempt, terminal state, and any available job
identity fields agree. They are not requested again. A completed cached bundle can reduce
the final cost further.

Repository inference may add a native GitHub CLI query. The measurements below use an
explicit repository and therefore exclude that optional cost. `gh --version` subprocesses
are not API requests.

## Active-run comparison

Manual workflow `Validate adaptive capture policy` run `35432811964` executed one Ubuntu
job at commit `2880263af6330c3f988c78433945ec4d66a0e7e9` and completed successfully. Both
watchers started together while the run was active:

```text
gh run watch 35432811964 --repo uibcdf/gh-run-receptor --compact
./gh-run-receptor watch 35432811964 --repo uibcdf/gh-run-receptor \
  --cache-dir FRESH_CACHE --receptor=llm
```

`tiktoken` 0.13.0 with `cl100k_base` measured both stdout and stderr:

| Watcher | Lines | Bytes | Input tokens |
| --- | ---: | ---: | ---: |
| Native compact watch | 38 | 1,280 | 321 |
| gh-run-receptor | 4 | 286 | 86 |

The receptor reduced observed reader input by 73.2%. Its four lines were the initial
state, two terminal transitions, and the final report; no unchanged job tree was printed.
The final report agreed with GitHub's `completed`/`success` source state.

A temporary wrapper recorded only the first `gh` argument and counted nine `gh api`
invocations: two successful one-page snapshots (four invocations) plus five fresh final
capture invocations. It did not record headers, tokens, bodies, or raw evidence.

## Already-completed boundary

Successful MolSysMT run `33849332945` establishes the opposite boundary. Native compact
watch emitted one line, 87 bytes, and 20 `cl100k_base` tokens. The receptor emitted one
line, 115 bytes, and 39 tokens because it retained repository, run, attempt, job, artifact,
and evidence-completeness context. The receptor therefore makes no token-saving claim for
a question already answered by a minimal native status view.

With a fresh cache, the optimized completed-run path made seven `gh api` invocations. The
pre-change path made nine logical invocations because final capture repeated the terminal
run and jobs calls. Terminal handoff removes those two calls, a 22.2% reduction for this
case, without omitting any final report source.

Sampling the REST `X-RateLimit-Remaining` header did not yield a reliable exact delta on
this host: two direct samples around the seven-invocation path differed by six, while the
rate-limit resource itself remained unchanged. The stable claim is therefore the
transport invocation/page formula and the instrumented adapter count, not an unsupported
account-wide quota delta.

## Limitations

The active measurement has one job and one jobs page. Larger workflows pay one request per
additional page. Producer artifacts, failed-run logs, missing configuration, cache reuse,
transient failures, and historical attempts change the total according to the formula
above. Native GitHub CLI implementation details are not frozen by this project; the native
line/token result is a dated comparison only.

Raw outputs, debug files, caches, and the temporary counting wrapper stayed under `/tmp`
and are not committed. Deterministic tests independently guard schedule changes, page
counting, historical-attempt cost, transient failure behavior, terminal identity, and the
absence of duplicate terminal run/jobs acquisition.
