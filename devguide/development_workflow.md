# Development workflow

## Starting point

Read [README.md](README.md) in order. Phase 0 and Phase 1 work may begin without recovering
the design conversation: current decisions are recorded in this guide, and unresolved
choices have owners and gates in [decisions_and_open_questions.md](decisions_and_open_questions.md).

The initial implementation target is Python 3.11 through 3.13. It uses the installed `gh`
CLI for authentication and HTTP transport behind an adapter so transport can change later
without changing normalized evidence or reports.

## Development environment

The source-tree MVP has a `pyproject.toml`, console entry point, and optional development
dependencies. In a disposable environment, install it with:

```text
python -m pip install -e '.[dev]'
```

The package uses the same flat repository layout as MolSysMT and MolSysViewer, so commands
and tests run from the checkout without a `PYTHONPATH` override. The expected local tools
are Git, an authenticated GitHub CLI, Python 3.11 or newer, Ruff, pytest, and
`pytest-receptor`.

GitHub-dependent validation uses reviewed public UIBCDF captures or bounded, manually
dispatched workflows and an explicitly authenticated `gh` session. Unit, contract, replay,
and adversarial tests remain offline. Never require a personal token in a committed file or
echo authentication state containing credentials.

## Architecture boundaries

Implementation follows the dependency direction in [architecture.md](architecture.md):
acquisition adapters produce versioned source records; normalization produces the internal
model; profiles interpret without mutating official facts; rendering consumes a report.
The core must not parse terminal-formatted `gh` output when a JSON or API representation is
available.

New profile behavior starts with a source example and a semantic test. New schema fields
state whether they are required, optional, or derived and include provenance. New output
must have a bound or pagination strategy.

## Change procedure

For each focused change:

1. identify the applicable contract and decision record; for substantial bugs or
   proposals, follow [the reporting protocol](reporting_protocol.md) and open the issue
   before writing its report;
2. add or update a semantic test that would fail if the intended property regressed;
3. implement the smallest compatible vertical change;
4. update user and developer documentation in the same change;
5. run focused tests, then the full applicable local gate;
6. inspect `git diff --check`, repository status, and staged content;
7. commit one coherent change and report exactly what was and was not tested.

When developer reports change, regenerate and validate their indexes:

```text
python devtools/scripts/devguide_index.py
python devtools/scripts/validate_devguide.py
```

Tests and validators check intent, not merely output shape. A fixture or golden file that
copies the expected label without establishing its source state is not a valid gate.

## Commit and branch conventions

Commit subjects are imperative and focused. Include `[skip ci]` only when the applicable
work has been validated locally and skipping remote CI is intentional; do not use it to
hide an untested change. Do not add attribution trailers. Never rewrite shared history or
use destructive Git commands in automated workflows.

Small branches and reviewable commits are preferred. Generated captures, credentials,
caches, and private evidence never enter version control. If a schema or public CLI
contract changes, the commit includes migration and compatibility notes.

Package versions come from lightweight, three-component Git tags through `versioningit`.
The full release procedure and the bootstrap status of tag `0.1.1` are recorded in
[Versioning and releases](versioning_and_releases.md).

## Definition of done

A feature is done when:

- behavior and non-goals match the product contract;
- official state and evidence provenance are preserved;
- success, failure, incomplete evidence, and adversarial paths are tested;
- output and resource use are bounded;
- CLI help and relevant devguide pages are current;
- schemas and compatibility policy are updated;
- supported platforms are verified or the limitation is explicit;
- local checks pass and their scope is reported.

For an Action feature, permissions, fail-open behavior, summary/artifact/outputs, and a
commit-pinned consumer example are also required.

## Review checklist

Reviewers ask:

- Could conforming output satisfy the test without preserving the underlying meaning?
- Can untrusted text or configuration affect a verdict or execute behavior?
- Can missing evidence be mistaken for success?
- Are run, attempt, commit, workflow, job, and artifact identities unambiguous?
- Does this add unbounded output, downloads, regex work, or API pagination?
- Does it duplicate capability already available from native GitHub tools without a
  measured benefit?
- Can the new contributor reproduce the result from committed fixtures or documented
  live setup?

## Documentation checkpoint

The devguide is the current project checkpoint, not a diary. Settled conclusions are
incorporated into the relevant normative page. Superseded discussions, if retained later,
belong in an archive with a short index; contributors do not read that history unless a
current document gives a specific reason.
