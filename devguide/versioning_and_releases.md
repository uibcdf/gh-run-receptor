# Versioning and releases

`versioningit` is the sole source of package versions after the bootstrap `0.1.1` tag.
The project metadata is dynamic and the version is derived from Git tags; do not restore a
static version in `pyproject.toml` or edit generated version code.

Release tags are lightweight tags named with exactly three numeric components, for example
`0.2.0`. On that exact commit, a build reports the tag as its package version. Commits after
a tag report a PEP 440 development identity such as `0.1.1+2.gabc1234`; a dirty checkout
adds `.dirty`. `gh_run_receptor/_version.py` is generated during the build and ignored by
Git. Installed metadata is preferred at runtime, with the generated file as the source-tree
fallback.

The existing `0.1.1` tag remains attached to its original commit. It predates this dynamic
configuration and must not be moved or recreated. Release `0.2.0` is the first tag governed
by this dynamic configuration. Release `0.2.1` adds the equivalent Git-tag fallback needed
when GitHub CLI executes a script-extension clone without building the Python package.

Before creating a release tag:

1. confirm the checkout is clean and on the intended commit;
2. run Ruff and the complete test suite with `pytest --receptor=llm`;
3. build both wheel and source distribution;
4. install the wheel in a clean environment and verify `gh-run-receptor --version`;
5. verify that the built metadata version equals the intended tag;
6. create and push the lightweight tag without moving an existing tag.

For a release that changes a platform-support claim, manually dispatch
`.github/workflows/compatibility.yml`. Its explicit matrix must pass the full suite, build,
wheel installation, and outside-checkout console smoke test on Ubuntu, macOS, and Windows
with Python 3.11, 3.12, and 3.13. This is evidence for the Python package and console
entry point; script-extension support requires its own installation gate.

A tag identifies source but does not by itself publish a package or GitHub Release. Those
are separate, explicit release steps.

Starting with 0.17.0, `.github/workflows/publish-release.yml` is the only normal GitHub
Release publication path. Dispatch it from the exact tag ref and provide the same tag as
its input. Its single writer job checks tag/ref/commit identity, validates citation
metadata, runs the complete suite, builds and installs the distributions, generates a
checksum manifest and bounded changelog notes, and creates a draft containing exactly
those assets. It publishes only after the draft agrees with the local names, sizes, and
SHA-256 values, then repeats the check against the public release.

An interrupted workflow may leave a draft. That is a fail-closed recovery state: inspect
it explicitly instead of deleting or replacing it automatically. The repository currently
does not enforce GitHub immutable releases; enabling that administrative policy is separate
from product publication. The draft-first workflow is compatible with enabling it later.

`CITATION.cff` is the GitHub-facing citation record. `.zenodo.json` supplies the matching
creators and project metadata used by Zenodo, which gives it precedence when both files
exist. Version and publication date remain absent from `.zenodo.json` because the release
event supplies them. A published GitHub Release does not prove Zenodo ingestion: record
existence, DOI, version, repository relation, and files must be observed independently.
Before preparing a release commit, run
`python devtools/scripts/release_tools.py prepare-citation X.Y.Z --date YYYY-MM-DD`; the
release workflow independently validates the resulting records but never rewrites tagged
source.

The `0.12.0` gate additionally requires checkout-local and exact-commit remote-source
execution of the composite Action on Ubuntu, macOS, and Windows. A same-run test must stay
`PENDING`; a completed source failure must not become a reporter failure.

The `0.14.0` gate additionally requires deterministic source run/attempt artifact identity,
a live canonical `workflow_run` reporter, source-first consumption from only the original
run ID, and installed-extension validation on Ubuntu, macOS, and Windows. The report must
distinguish verified source facts, verified reporter identity, and published rather than
recomputed interpretation.

The `0.15.0` gate additionally requires inline `config@1` equivalence, default-branch
provenance, stable fail-open outputs, exact public permission observations, live
same-repository pull-request rejection, and a canonical `workflow_run` report selected by
trusted inline policy. Private-repository and fork behavior remain unclaimed unless tested
in those environments.

The `0.16.0` gate additionally requires pre-acquisition enforcement of GitHub CLI 2.48.0,
offline independence from `gh`, and a real installed-extension metadata capture through
the official checksum-pinned minimum Linux amd64 binary. Documentation distinguishes the
functional floor from the recommendation to use the latest patched stable CLI.
