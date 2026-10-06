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

The maintained GitHub archive guard is
`python devtools/scripts/release_tools.py archives X.Y.Z --directory dist`.
It checks both wheel and sdist without extraction or payload execution, using
`devtools/scripts/distribution_archives.py::inspect_distribution` and the owner
inventory in `devtools/conda-build/resources.toml`. Required runtime paths,
generated and metadata versions, Python bounds and all nine frozen schema
digests must agree. The sdist's root and egg-info metadata are both checked;
the wheel must contain exactly its expected distribution metadata. Unsafe or
duplicate paths, links, truncated archives and bounded size/count violations fail.
The limits are 64 MiB compressed/total payload, 2 MiB per member and 2,048 members.
If legitimate payload growth exceeds those limits, review the limit and its
regression evidence before publishing; do not bypass the check.

The manual publisher runs this guard before installing or uploading any asset;
`release_tools.py verify` repeats it for both draft and public verification in
addition to the original tag/source/API size/digest checks. Checksums alone do
not qualify payload contents. `--repo` selects the reviewed owner inventory for
an independently downloaded file. These checks establish archive integrity,
not an installed cross-platform matrix or Conda authorization. The historical
1.2.0 files retain their bytes and original evidence scope.

For the 1.2.0 candidate, build from an isolated clone at the exact release commit
with a temporary local 1.2.0 tag. That staging tag is not pushed. Verify the
wheel/sdist metadata, frozen runtime schemas and a clean installed-wheel replay
before creating the same lightweight tag in the authoritative checkout. Record
the exact commit, tool/dependency versions, artifact digests, tested scope and
hosted run identities in a reviewable candidate receipt outside the source tree;
after publication incorporate the observed receipt into this guide. A release
metadata edit creates a new candidate and invalidates its consuming gate evidence.
The public route remains the existing GitHub Release assets and pinned CLI
extension; package-index and Conda publication are separate unclaimed routes.

For a release that changes a platform-support claim, manually dispatch
`.github/workflows/compatibility.yml`. Its explicit matrix must pass the full suite, build,
wheel installation, and outside-checkout console smoke test on Ubuntu, macOS, and Windows
with Python 3.11, 3.12, 3.13, and 3.14. This is evidence for the Python package and console
entry point; script-extension support requires its own installation gate.

Release 1.1.0 completed the Python 3.14 transition tracked by
`uibcdf/gh-run-receptor#49`: all twelve compatibility cells passed, and its exact-tag
public wheel and pinned GitHub CLI extension were independently installed on a clean
Python 3.14 environment. Future platform-support changes still require the hosted matrix
and installed-product verification before updating public claims. Keep the 1.0.0 evidence
and historical guidance scoped to their actual tag.

Release 1.1.1 carries the log-cause correction tracked by
`uibcdf/gh-run-receptor#50`. Its local gate passed 451 tests with twelve workers, Ruff,
all nine frozen-contract checks, citation agreement, strict documentation, exact-tag
wheel/sdist construction, and an isolated installed-wheel check. The tag points to
`3ff6d3c29a8b12ddc86a4ef2a02b6367f2c774c9`. Draft-first publication run
`35582734192` passed; the public release contained exactly the wheel, source archive,
and checksum manifest, which were independently downloaded and hash-verified. The public
wheel replayed the original Ackredit and SMonitor failures, named their tests, and retained
GitHub's failed conclusion. This patch changes neither Python support nor serialized
contracts nor the GitHub Action/reusable-workflow interface.
An isolated GitHub CLI extension installed from the public `1.1.1` tag resolved to the
same commit, reported version 1.1.1, and named the Ackredit test in its compact report
while retaining process status 1.

Zenodo independently archived version 1.1.1 as DOI `10.5281/zenodo.22871415` under
concept DOI `10.5281/zenodo.22843377`. Its observed file inventory is exactly one
GitHub-generated source ZIP, `uibcdf/gh-run-receptor-1.1.1.zip` (582,251 bytes); do not
claim that Zenodo archived the three GitHub Release assets. The GitHub Release remains
the authoritative wheel/sdist download surface.

## Verified release 1.2.0 — 2026-10-02

The lightweight tag `1.2.0` identifies
`c3df5ad87f7bab95c53be3f7b0b3007f59d7abf3`. This minor release adds the
source-preserving annotation reader in `uibcdf/gh-run-receptor#46` and the
targeted Conda inspection capability, together with the #56 silent-failure
correction and intervening compact/primary failure-diagnostic fixes. Python
bounds, dependency-free runtime, the stable process-status map and all nine
frozen serialized resource bytes remain unchanged. No producer contract or new
distribution index is introduced.

The pre-tag candidate receipt was recorded outside the source checkout with
exact commit, intended version, route, metadata/resource hashes, tool versions,
candidate artifact digests and gate scopes. The temporary staging tag was never
pushed from its isolated clone. Local Python 3.13.14 ran 565 passing tests with
the installed development pytest-receptor 1.2.0 renderer; hosted gates installed
the committed published test pin `pytest-receptor==1.1.0`. Local build inputs
were build 1.5.0, setuptools 80.10.2, versioningit 3.3.0 and wheel 0.47.0.
Ruff 0.16.5 lint/format, strict Sphinx 8.2.3, citation, developer-guide and
all nine frozen-contract checks passed for the exact candidate.

The staged wheel and sdist both carried version 1.2.0, the new reader modules
and nine unchanged runtime schemas. Isolated installed-wheel replay preserved
the original #56 failure, exit 1 and three exit-code occurrences; #46 retained
native cancellation, exit 2, unknown cause and an unverified execution-limit
hint. Negative in-memory payload checks rejected a stale embedded version and
a missing runtime schema without changing either distribution.

Exact-source hosted evidence:

- [Compatibility run 37073452071](https://github.com/uibcdf/gh-run-receptor/actions/runs/37073452071):
  all twelve Ubuntu/macOS Apple Silicon/Windows and Python 3.11--3.14 cells
  passed the complete suite, build, wheel install and outside-checkout smoke test.
- [Policy run 37073454392](https://github.com/uibcdf/gh-run-receptor/actions/runs/37073454392): passed.
- [Publication run 37073949431](https://github.com/uibcdf/gh-run-receptor/actions/runs/37073949431):
  the exact-tag build, tests, draft verification and public verification passed.
- [Pages run 37073952158](https://github.com/uibcdf/gh-run-receptor/actions/runs/37073952158):
  build and deployment passed on the candidate `main` commit. An independent
  fetch of the public installation page contained the 1.2.0 wheel URL.

The public [GitHub Release](https://github.com/uibcdf/gh-run-receptor/releases/tag/1.2.0)
contains exactly these downloaded and independently verified assets:

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `gh_run_receptor-1.2.0-py3-none-any.whl` | 94,594 | `a69b4ce158eb5c74a9b165847279d12f6867ddd41e9fdaa47b3de11463cf210c` |
| `gh_run_receptor-1.2.0.tar.gz` | 149,532 | `7574499f7b8e62c281a5aaf0ba7ea7b6233116e1a3b1e09c3be9852649bfbc37` |
| `SHA256SUMS` | 200 | `16a4c497a390387da37f85330ab22b90eedb6c24cb6dead0d9b66153b2042fbb` |

These hosted-build assets have their own digests; they are not claimed to be
byte-identical to the locally staged archives. Their metadata, new modules and
all nine frozen schemas were independently checked after download. A fresh
Linux/Python 3.13.14 venv installed only the public wheel with `--no-deps` outside
the checkout and repeated both original issue replays and the usage-status-64
check. The imported module belonged to that isolated installation. The hosted
matrix above is source-build/install evidence, not an assertion that the
downloaded public wheel was independently installed on all twelve platforms.

An isolated XDG data directory received the public CLI extension with
`gh extension install uibcdf/gh-run-receptor --pin 1.2.0`. Its checkout resolved
to the exact release commit, version output was 1.2.0 and #46 replay preserved
exit 2 and its unverified hint. The maintainer's existing pinned extension was
preserved. Authenticated transport remained the existing installed GitHub CLI.

Zenodo independently verified version DOI
[`10.5281/zenodo.23112015`](https://doi.org/10.5281/zenodo.23112015) under
concept DOI `10.5281/zenodo.22843377`. Its observed inventory is exactly
`uibcdf/gh-run-receptor-1.2.0.zip`, 651,072 bytes, checksum
`md5:f44d7949eee12757c359a2d3c37f0c6b`. Zenodo records its publication date as
2026-10-03; GitHub records publication at 2026-10-02T22:43:23Z and the source
citation date is 2026-10-02. The archive is a GitHub-generated source ZIP;
the GitHub wheel and sdist are not claimed to be Zenodo files.

The release and package handoff is `uibcdf/molsyssuite#75`. It requests central
triage of registered client-guide synchronization, appropriate consumer pins
and inventory updates using the canonical 1.2.0 guide. No sibling worktree was
changed by this publication. The independently delivered timeout assessment in
`uibcdf/molsyssuite#25` is now available in the published package; any later
operation-supervisor trust/compatibility decision still belongs there.

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

The exact-tag workflow runs
`python devtools/scripts/validate_contracts.py --baseline 0.21.0` before building. Each
registered resource is compared with its own first publishing tag: four against 0.18.0,
three against 0.19.0, one against 0.20.0, and one against 0.21.0. A contract change that
cannot satisfy this gate requires a new integer contract version and the
migration/retirement process in `data_contracts.md`; editing a baseline tag or weakening
the comparison is not a release operation.

A candidate that introduces a freeze must be validated before its tag exists. For 0.21.0,
use `python devtools/scripts/validate_contracts.py --baseline 0.20.0 --candidate 0.21.0`.
Candidate mode requires the named tag to be absent and only permits a resource absent from
the published baseline to acquire the new freeze. The ordinary mode continues to fail
until the tag exists, so candidate mode cannot be reused to bypass a published baseline.

## Zenodo maintainer handoff

Zenodo account configuration is a maintainer operation, not a GitHub Actions permission or
receptor feature. A maintainer with access to the UIBCDF Zenodo integration must:

1. sign in to Zenodo and connect the GitHub account if it is not already connected;
2. open the GitHub integration page and select **Sync now**;
3. find `uibcdf/gh-run-receptor` and enable its repository toggle;
4. publish a new GitHub Release after enablement, because prior tags or releases are not
   assumed to be backfilled;
5. wait for Zenodo's asynchronous processing to finish and inspect any integration error;
6. query and save the public response, then run the repository verifier;
7. record the version DOI, concept DOI, files, and verification date in this guide only
   after the verifier reports `VERIFIED`.

The official account procedure is
`https://help.zenodo.org/docs/github/enable-repository/`. Acquire bounded public evidence
without a token:

```text
curl --fail --location --silent --show-error --get \
  https://zenodo.org/api/records/ \
  --data-urlencode 'q="gh-run-receptor"' \
  --data 'all_versions=true' --data 'size=25' \
  --output /tmp/gh-run-receptor-zenodo.json
python devtools/scripts/release_tools.py zenodo X.Y.Z \
  --response /tmp/gh-run-receptor-zenodo.json
```

Exit 0 and `VERIFIED` mean exactly one semantically complete record matched. Exit 2 and
`ABSENT` mean no exact title/version record was present at query time. Exit 1 means the
response was malformed, ambiguous, or the matching record disagreed with required DOI,
creator, repository, type, access, or file evidence. `.github/workflows/verify-zenodo-release.yml`
provides the same bounded read-only check manually on a hosted runner. It intentionally
fails while the record is absent; it does not create or repair deposits.

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

The `0.17.0` gate additionally requires matching citation and Zenodo ingestion metadata,
an exact-tag GitHub Release containing the verified wheel, source distribution, and
checksum manifest, and independent public revalidation of tag/commit identity and every
asset's name, size, and SHA-256 digest. Zenodo archival remains a separate observed fact.

The `0.18.0` gate repeats the exact-tag publication after correcting authenticated draft
lookup and requires the uninterrupted workflow to verify draft and public release states
without maintainer recovery.

The `0.19.0` gate additionally freezes all seven current v1 contract resources, validates
new freezes before tag creation without relabeling published resources, and publishes run
comparison, explicit regression policy, and the same-revision reusable terminal reporter.

The `0.19.1` gate retains those seven frozen resources and publishes the safe discovery
correction: filename-only Conda hints and action-internal platform inputs cannot be
misrepresented as an observable native-platform matrix. Its distributed Action, minimum
GitHub CLI, exact-tag build, and public release gates repeat against the patch tag.

The `0.20.0` gate freezes `events@1` as the eighth serialized boundary and publishes
strict, attempt-qualified producer evidence for Action-internal Conda matrices. Hosted
Ubuntu and Windows producers, normal network capture, sanitized offline replay, and
producer-failure truth semantics must pass before the tag is created.

The `0.21.0` gate freezes `aggregate@1` as the ninth serialized boundary and publishes
bounded multi-run aggregation. Offline CI/documentation/Conda fixtures, failure and
incompleteness truth tables, a real cross-repository success collection, a real mixed
success/failure collection, output bounds, and the exact-revision hosted gate must pass
before the tag is created. The release record retains the measured counterexample that
individual receptor lines are smaller for a narrow known-run question.

The `0.21.1` patch retains all nine contract freezes and corrects the mismatch between the
documented CLI usage status 64 and argparse's former status 2, which collided with a valid
terminal non-success outcome. Its gate requires the local and hosted process-status truth
tables, an exact-tag installed-wheel usage check outside the checkout, and the minimum
GitHub CLI extension installation check before the map becomes stable for CLI 1.0.

The `0.22.0` gate retains all nine contract freezes and publishes the public documentation
site, the stable adaptive log-acquisition truth table, and deterministic transition-only
watch semantics. It requires the paired full/adaptive hosted benchmark, active-run watch
measurement, strict Sphinx build, exact-tag distribution and extension checks, and the
ordinary cross-platform and frozen-contract gates. Zenodo ingestion remains an independent
post-publication observation and cannot be inferred from the GitHub Release workflow.
Release 0.22.0 completed that independent observation: its version DOI is
`10.5281/zenodo.22843378` and the stable project concept DOI is
`10.5281/zenodo.22843377`.

The `0.23.0` gate is the final pre-1.0 dogfooding gate. It retains all nine contract
freezes, publishes the stable scope and evidence map in `release_readiness_1_0.md`, and
closes every decision gate that applies at or before 1.0. In addition to the ordinary
exact-tag release checks, it repeats the nine Python/operating-system combinations,
minimum GitHub CLI, distributed Action, reusable reporter, frozen-contract, and strict
documentation gates. The public artifacts, hashes, isolated wheel import, and Zenodo
record are then verified independently. At least one real MolSysSuite workflow is
inspected with the installed public 0.23.0 product before 1.0 eligibility is declared.
Desired post-1.0 features do not delay the stable tag unless their absence contradicts a
documented 1.0 promise.

GitHub Pages deployment is a candidate-commit `main` observation, not an exact-tag
operation. The protected `github-pages` environment rejects tag deployments before a
runner starts. Exact tags therefore repeat the strict documentation build while the
workflow deploys only from `refs/heads/main`; a tag must not turn this expected protection
boundary into a failed deployment job. Release 0.23.0 completed its independent Zenodo
observation with version DOI `10.5281/zenodo.22848495` and the stable concept DOI
`10.5281/zenodo.22843377`.

The `1.0.0` gate publishes the boundary frozen in `release_readiness_1_0.md` without
adding product capability. It replaces preview lifecycle wording and pins with the stable
version, retains all nine serialized v1 resources and the stable process-status map, and
repeats the complete 0.23.0 local, exact-commit, exact-tag, public-release, independent
asset, Zenodo, Pages, client-guide, and installed-product observations. A desired excluded
feature is not a release blocker; an unresolved critical or high defect in the documented
boundary is.

Release 1.0.0 completed this gate at commit
`95e63cbdfbc2a22b8cfecb011297331194e6a316`. Its independently observed Zenodo version
DOI is `10.5281/zenodo.22849252`; the stable concept DOI remains
`10.5281/zenodo.22843377`.

Installed-wheel verification must run outside the source checkout and assert that the
imported module path belongs to the isolated installation target. A matching version string
alone is not evidence that the wheel payload was imported.


## Additional Conda distribution

The noarch Python route accepted under uibcdf/gh-run-receptor#60 is prepared
separately from GitHub release assets. Follow the
[committed route handoff](../devtools/conda-build/README.md) for the actual plan,
external gh constraint, candidate gates, staging and twelve installed cells.
Only `release_plan.toml` can authorize a candidate; the example plan cannot.
Public files and existing tags are immutable. Promotion retains original source
and tested bytes; a newer administrative workflow gets a separate qualification
identity. Current source readiness, credential access, artifact installation and
public delivery are separate claims. The first Conda release remains pending.
