# Motivation and measured evidence

## Origin

`gh-run-receptor` follows the same economic observation that led to
`pytest-receptor`: tools usually render for a human terminal, while a coding agent pays
for every returned token and cannot benefit from repeated decoration or duplicated
causes. `pytest-receptor` solved this at the pytest event boundary. GitHub Actions needs
an equivalent evidence-preserving boundary above workflow runs.

The project was proposed while diagnosing MolSysMT native Conda builds. Repeated
`gh run watch` calls printed the complete state of every unchanged job and step every
few seconds. Full and failed-log queries returned thousands of timestamped lines with
the job name repeated on every line. Individual macOS job logs reported approximately
60,000 source tokens before tool-side truncation, while the useful result was a verdict,
four timing values, one root cause, and a rerun target.

The problem is not that complete evidence is undesirable. Complete evidence is
necessary for debugging and for validating the receptor. The waste occurs when the
complete representation is sent through stdout to a language model before relevance is
known.

## Initial real-world evidence

The first corpus candidates come from `uibcdf/molsysmt`:

| Run | Purpose | Evidence represented |
| --- | --- | --- |
| `33849332945` | Production ABI3 Conda staging | Five successful native platforms with very different durations |
| `33855381273` | macOS Intel, fat LTO | Valid build and three ABI checks followed by a benchmark-harness failure |
| `33855381257` | macOS Intel, Thin LTO | Same late shared failure with a faster build phase |
| `33855381300` | macOS Intel, local Thin LTO | Same late shared failure and independently reusable artifact evidence |
| `33855381334` | macOS Intel, LTO off | Same late shared failure without an expected speed improvement |
| `33863114690`--`33863123319` | Corrected LTO reruns | Repeated attempts and structured runtime artifacts |
| `33863426589` | Rattler Build experiment | Five-platform matrix, artifact validation, and timing comparison |

Run identifiers are discovery aids, not permanent fixtures. GitHub logs and artifacts
expire. Phase 0 captures full bundles, records their hashes, and selects only sanitized
public evidence for the committed corpus.

## Lessons already established

- A red workflow does not imply that every artifact or platform failed.
- A failed final benchmark does not erase successful compilation and compatibility
  checks that preceded it.
- Upload duration, build duration, solver duration, and validation duration are distinct
  facts and should not be collapsed into total job time.
- Repeating a complete status tree is not a useful liveness protocol. Transition-only
  output retains the information at a bounded cost.
- `gh run view --log-failed` is useful but not sufficient: it can still return a very
  large log and may lose step association.
- Filtering metadata with `--jq` is an excellent primitive, but it provides no workflow
  semantics, causal grouping, replay bundle, or cross-run comparison.

## Honest baseline

Token-savings claims must compare the receptor against a competent GitHub CLI user, not
against the noisiest possible command. The baseline for a completed run is:

1. a filtered run-and-job JSON query;
2. a failed-job or failed-step log query only when required;
3. local filtering for errors and nearby context;
4. artifact inventory without downloading large artifacts.

The benchmark records bytes and token counts for the baseline and receptor output. It
reports results across available tokenizer families and labels the four-characters-per-
token estimate when an exact tokenizer is unavailable.

## Prior art and deliberate differences

`pytest-receptor` provides reusable principles: authoritative exit status, grouping by
root cause, bounded output, deterministic ordering, untrusted-output handling, and safe
degradation. Its pytest hooks and test model are not reused directly because a GitHub
run is remote, asynchronous, multi-job, and split across several APIs.

Native GitHub job summaries, checks, annotations, artifacts, `gh --json`, `--jq`,
`--log-failed`, and `--compact` watch mode remain part of the solution. The receptor
orchestrates and interprets those capabilities; it does not claim that GitHub lacks
compact primitives.

## Evidence required before product claims

No token-saving, diagnostic-accuracy, or portability percentage is a product claim
until the corpus benchmark records:

- receptor version and source commit;
- GitHub CLI and API versions;
- evidence-bundle digest;
- baseline commands;
- tokenizer or approximation method;
- raw byte counts and token counts;
- whether logs or artifacts were fetched;
- whether the expected diagnosis was independently reviewed.

