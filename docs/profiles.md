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

Select `generic` and inspect natively when no profile represents the visible evidence
faithfully.
