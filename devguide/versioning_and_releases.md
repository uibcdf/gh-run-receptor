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
configuration and must not be moved or recreated. The next release is cut from a later,
clean commit and receives its own three-component tag.

Before creating a release tag:

1. confirm the checkout is clean and on the intended commit;
2. run Ruff and the complete test suite with `pytest --receptor=llm`;
3. build both wheel and source distribution;
4. install the wheel in a clean environment and verify `gh-run-receptor --version`;
5. verify that the built metadata version equals the intended tag;
6. create and push the lightweight tag without moving an existing tag.

A tag identifies source but does not by itself publish a package or GitHub Release. Those
are separate, explicit release steps.
