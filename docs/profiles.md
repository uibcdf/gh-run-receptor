# Profiles

Profiles interpret one normalized evidence model. They change the questions asked of the
evidence; they do not change GitHub's status or conclusion.

| Profile | Intended workflow | Added interpretation |
| :--- | :--- | :--- |
| `generic` | Unknown or unsupported shape | Complete bounded job, step, check, and artifact inventory |
| `ci` | Test, lint, coverage, validation | Presentation roles and repeated failed-step grouping |
| `conda` | Native or noarch package builds | Platform coverage, reusable artifacts, producer build/upload state |
| `docs` | Documentation build and deployment | Build/deploy phases without splitting indivisible composite work |
| `release` | Tag, package, and release workflows | Observed ref/SHA/event, material phases, and external-verification limits |

Use `--profile=generic|ci|conda|docs|release` to select explicitly. `auto` is conservative:
it uses trusted repository configuration first, then bounded workflow evidence, and falls
back to `generic` when a specialized interpretation would overclaim.

## Assessment and source truth

Every report keeps both layers:

```text
PARTIAL conclusion=failure status=completed | OWNER/REPO | run=123 attempt=1
```

`conclusion=failure` is GitHub's source fact. `PARTIAL` means the selected profile found a
meaningful completed phase separately from failed or skipped work. It never means success.

Common assessments are:

- `PASS`: GitHub completed successfully and required expectations are satisfied;
- `FAIL`: GitHub failed or a required expectation failed;
- `PARTIAL`: useful completed work exists alongside an unsuccessful run;
- `PENDING`: required work is nonterminal;
- `CANCELLED`, `TIMED_OUT`, `ACTION_REQUIRED`, or `STALE`: preserved terminal state;
- `INCOMPLETE`: evidence required for the assertion is missing;
- `UNKNOWN`: the source value or shape cannot be classified safely.

## Conda evidence

A visible GitHub job matrix may identify platforms directly. When one composite Action
hides several builds inside a job, inputs and filenames are not proof of results. A
producer can upload bounded `events@1` evidence containing actual platform, build, digest,
and upload-attempt state. Registry presence is still a separate external fact.

For `noarch` packages, the receptor does not invent a native matrix. Configure
`package_kind: noarch` so the report retains job and artifact identity without expecting
operating-system-specific package outputs.

## Documentation and release boundaries

A combined build/deploy Action is one indivisible observed unit; it is not counted once as
build and again as deployment. Release reports similarly distinguish an observed upload
command from independent registry delivery, and a Git tag from a verified GitHub Release
or Zenodo archive.

The release profile freezes the following authority boundary for 1.0:

| Reported claim | Evidence source | Strongest allowed statement |
| :--- | :--- | :--- |
| Event, head ref, and head SHA | GitHub run API | Observed source fact |
| Release phase and state | GitHub jobs API plus bounded name classification | Presentation facet with the original job or step state |
| Git tag verification | No dedicated source | `not_observed` (`tag=unverified` in compact output) |
| Registry delivery | Name-classified workflow step | `step_success`; never independent registry verification |
| GitHub Release delivery | No dedicated source | `not_observed` |
| Citation or archive delivery | Name-classified workflow step | `step_success`; never independent archive verification |
| Actions artifact inventory | GitHub artifacts API | Current observed inventory only |
| Aggregate external delivery | No independent external query | `not_observed` |

Names and log messages are untrusted presentation evidence. A successful step named
`Publish to PyPI`, `Git tag verified`, or `Zenodo DOI created` cannot strengthen any row
beyond the limit above. Registry, Git-ref, GitHub Release, or Zenodo verification requires
a future dedicated structured source.

Select `generic` and inspect natively when no profile represents the visible evidence
faithfully.


## Diagnosing acquisition and inconsistent metadata

The following improvements are prepared for candidate 1.5.0; public 1.4.0
retains its original diagnostic behavior until the new release is delivered.

Failed-job summaries retain specific Conda transport, micromamba binary and
missing artifact-download messages before later cleanup or empty-upload
diagnostics. Source log locators remain available; later context does not prove
a causal relationship. Independent cleanup/upload failures remain visible.

A successful workflow can have contradictory child step metadata in GitHub's
response. The report preserves the successful run conclusion while warning that
terminal step qualification is unknown, with affected counts and source
pointers. Preserve the first capture and request a separate fresh observation:

```bash
gh-run-receptor inspect RUN_ID --repo OWNER/REPO --attempt ATTEMPT \
  --capture metadata --output fresh-observation --receptor llm
```

Use a new output directory and compare native selected-attempt job/step evidence.
Logs and a later coherent response are separate evidence; they do not replace
missing original step conclusions.

For cancelled jobs with no steps, exact linked annotations may expose unverified
hosted-runner acquisition or macOS arm64 capacity hints. Repeated capacity
notices are shown once. Capacity notices and absent steps never prove the cause
of cancellation, and all native conclusions and exit codes remain unchanged.
