# Installation

## Supported environment

| Component | Supported boundary |
| :--- | :--- |
| Python | 3.11, 3.12, or 3.13 |
| GitHub CLI | 2.48.0 or newer for network commands |
| Operating systems | Linux, macOS, and Windows |
| GitHub host | `github.com`; alternate hostnames may be selected explicitly |

The Python and operating-system combinations are exercised in a nine-job hosted matrix.
GitHub CLI 2.48.0 is tested independently as the functional floor required for paginated
API acquisition. Prefer the latest patched stable GitHub CLI for security maintenance.

## Install as a GitHub CLI extension

`gh-run-receptor` is currently distributed through exact GitHub source releases, not a
Python package index. Pin the release:

```bash
gh extension install uibcdf/gh-run-receptor --pin 0.23.0
gh run-receptor --version
```

A pinned script extension does not advance automatically. To change versions, remove and
install it again:

```bash
gh extension remove run-receptor
gh extension install uibcdf/gh-run-receptor --pin 0.23.0
```

High-assurance environments may pin the complete release commit instead of the tag.

## Authenticate GitHub CLI

Network commands use the installed `gh` process for authentication and transport. The
receptor does not implement another token store.

```bash
gh auth status
gh auth login
```

Public runs normally require `contents: read` and `actions: read` when called from a
workflow. Private repositories require a token that can read the repository and Actions
evidence. A GitHub 404 cannot prove that a private resource does not exist, so the receptor
reports `not_found_or_inaccessible` conservatively.

## Install the Python artifact directly

Every GitHub Release contains a wheel, source distribution, and `SHA256SUMS`. Direct wheel
installation is useful for an isolated Python environment:

```bash
python -m pip install \
  https://github.com/uibcdf/gh-run-receptor/releases/download/0.23.0/gh_run_receptor-0.23.0-py3-none-any.whl
gh-run-receptor --version
```

Verify the release checksum manifest when artifacts are mirrored or downloaded manually.
The package has no runtime Python dependency; JSON Schema and documentation tools are
development extras.

## Offline commands

`replay`, local `compare`, local `aggregate`, `contracts`, and local configuration commands
do not require GitHub CLI or network access once their input files exist.

## Embedded installation

The composite Action and reusable workflow need no package-install step. Pin their exact
release as shown in [Embedded reporting](embedded-reporting.md).
