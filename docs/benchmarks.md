# Benchmarks

Token economy is measured against bounded native GitHub queries, not against deliberately
printing every log. Results are case measurements rather than a universal savings promise.

## Initial workflow corpus

| Question | Native baseline | Receptor | `cl100k_base` reduction |
| :--- | ---: | ---: | ---: |
| Diagnose a partial five-platform Conda failure | 5,138 | 296 | 94.2% |
| Verify a successful five-platform Conda matrix | 143 | 39 | 72.7% |
| Diagnose seven failed MolSysViewer CI jobs | 223 | 198 | 11.2% |
| Verify a successful MolSysViewer noarch workflow | 101 | 45 | 55.4% |
| Diagnose a failed notebook workflow | 136 | 113 | 16.9% |
| Verify a successful documentation workflow | 254 | 48 | 81.1% |
| Diagnose a failed npm release workflow | 103 | 93 | 9.7% |
| Verify a successful npm release workflow | 95 | 84 | 11.6% |

The baseline is already filtered to the fields needed for each question. The receptor adds
consistent source identity, evidence completeness, profile semantics, bounded grouping,
and a replay path. Its first ungrouped CI implementation was larger than the native query
and was rejected before release.

## Where native GitHub is smaller

For the narrow question “did this completed run succeed?”, measured native GitHub JSON was
10 tokens versus 39 for the receptor. Use the native query when status alone is enough:

```bash
gh run view RUN_ID --repo OWNER/REPO --json status,conclusion
```

Compression is valuable only when it preserves information the reader actually needs.

## Multi-run counterexample

For two known successful runs, two separate receptor lines measured 87 `cl100k_base`
tokens, while the three-line aggregate measured 139. The aggregate was still 33.2% smaller
than a compact native multi-run projection, but it is not the smallest answer to every
question. Its value is a versioned collection assessment, source-by-source identity, and
coverage summary.

## What the measurements preserve

The corpus checks that compact output keeps:

- official run and job outcomes;
- failed and reusable platform identity;
- artifact inventory at capture time;
- source repository, run, attempt, commit, and URL;
- explicit missing or expired evidence;
- profile-specific phase and expectation state.

Measurements cover `cl100k_base`, `o200k_base`, and a portable punctuation/word heuristic.
The complete commands, raw byte counts, tokenizer versions, and limitations live in the
[development benchmark record](https://github.com/uibcdf/gh-run-receptor/blob/main/devguide/benchmark_2026-09-04.md).

## Interpreting a percentage

A high reduction does not prove a good diagnosis, and a low reduction does not mean the
tool is useless. Correctness gates run before token comparison. A receptor result is
acceptable only when it preserves source truth and uncertainty; the benchmark then asks
whether the correct answer is cheaper to consume.
