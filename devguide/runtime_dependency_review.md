# Runtime minimum dependency review

Owner: uibcdf/gh-run-receptor#79; central receiving: uibcdf/molsyssuite#137.
Reviewed 2026-11-11 against the published `provider>=X` rule. The source/input
digests and separate provider review are retained in
[the owner review receipt](evidence/issues_79_80_owner_review.json).

## Runtime and optional features

`pyproject.toml` declares no required Python runtime providers. There are no
optional Python runtime feature groups: the `test`, `docs` and `dev` extras
install development tools, not product backends. Capture, replay, profiles,
configuration, annotation interpretation, the extension and embedded reporting
use the Python standard library. No unused dependency or invented minimum is
introduced by this review.

The external GitHub CLI requirement is `gh>=2.48.0`. That floor supplies the
`gh api --paginate --slurp` acquisition interface used by `github.py`. The
adapter rejects an older/unrecognized executable before network acquisition;
offline replay does not require gh. The Conda recipe and resource inventory
declare the same inclusive floor. Existing minimum-gh native and offline guards
remain required. Actual release qualification verifies prefix-owned gh and GHR
commands separately; permissive bounds do not certify every future gh version.

Python `>=3.11,<3.15` is the separately governed supported interpreter range,
not an upper bound on a sibling provider. The recipe, metadata, native matrices
and installed descriptors retain that range.

## Build, test, documentation and acquisition routes

Setuptools/versioningit are build providers. Pytest, Pytest Receptor, JSON Schema,
Ruff, packaging, Jinja2 and PyYAML are test/development/qualification tools.
Sphinx, MyST and the theme are documentation tools. Their exact reproducibility
pins or reviewed compatibility ceilings are not product runtime restrictions.
The installed-test `jsonschema>=4.23,<5` is a qualification dependency, absent
from the package's run requirements. Preserve these separate scopes.

The Conda run requirements contain only Python and external gh. Its build script
uses `--no-deps --no-build-isolation`, with declared build providers in the host
environment. The extension and composite Action launch their identified source;
they install no hidden Python runtime providers. The reusable workflow delegates
to that same Action. Thirty maintained distribution/acquisition routes are
reviewed through `devtools/dependency_routes.toml` and the immutable shared SDK.
No repository-specific runtime-bearing Conda environment or additional
requirements manifest is maintained outside those declared routes.

**Disposition:** complies without runtime declaration changes. No provider
ceiling/exclusion or runtime-policy exception is required. Reassess when a
Python runtime dependency, optional backend, acquisition route, consumed gh API
or interpreter support boundary changes. Source/installed compatibility remains
an executed gate, not a consequence of this classification. The caller's shared
development environment has unrelated pre-existing dependency findings; this
review does not certify that environment as a clean release installation.
