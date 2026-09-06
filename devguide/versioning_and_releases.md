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
