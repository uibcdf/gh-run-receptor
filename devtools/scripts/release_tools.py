#!/usr/bin/env python3
"""Prepare and verify exact-tag GitHub Release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPOSITORY = "uibcdf/gh-run-receptor"
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
PROJECT_TITLE = "gh-run-receptor"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ZENODO_DOI_RE = re.compile(r"^10\.5281/zenodo\.\d+$")


def distribution_names(version: str) -> tuple[str, str]:
    """Return the exact distribution asset names for a release version."""

    if not VERSION_RE.fullmatch(version):
        raise ValueError("version must use X.Y.Z without a leading 'v'")
    normalized = version.replace("-", "_")
    return (
        f"gh_run_receptor-{normalized}-py3-none-any.whl",
        f"gh_run_receptor-{normalized}.tar.gz",
    )


def extract_release_notes(changelog: Path, version: str) -> str:
    """Extract one nonempty version section from the changelog."""

    distribution_names(version)
    text = changelog.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## {re.escape(version)} - \d{{4}}-\d{{2}}-\d{{2}}\n\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected one changelog section for {version}, found {len(matches)}")
    body = matches[0].group("body").strip()
    if not body:
        raise ValueError(f"changelog section for {version} is empty")
    return body + "\n"


def sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksum_manifest(directory: Path, version: str) -> Path:
    """Write a deterministic checksum manifest for the two distributions."""

    names = distribution_names(version)
    unexpected = sorted(path.name for path in directory.iterdir() if path.is_file())
    if unexpected != sorted(names):
        raise ValueError(f"distribution directory must contain exactly {sorted(names)!r}")
    manifest = directory / "SHA256SUMS"
    manifest.write_text(
        "".join(f"{sha256(directory / name)}  {name}\n" for name in sorted(names)),
        encoding="utf-8",
    )
    return manifest


def _orcid(value: object) -> str:
    return str(value or "").removeprefix("https://orcid.org/")


def _cff_creators(payload: dict) -> set[tuple[str, str]]:
    return {
        (
            f"{author.get('family-names', '')}, {author.get('given-names', '')}",
            _orcid(author.get("orcid")),
        )
        for author in payload.get("authors", [])
    }


def _zenodo_creators(payload: dict) -> set[tuple[str, str]]:
    return {
        (str(creator.get("name", "")), _orcid(creator.get("orcid")))
        for creator in payload.get("creators", [])
    }


def validate_citation(repo: Path, expected_version: str) -> list[str]:
    """Return citation and Zenodo metadata violations."""

    distribution_names(expected_version)
    errors: list[str] = []
    try:
        cff = yaml.safe_load((repo / "CITATION.cff").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"CITATION.cff cannot be parsed: {exc}"]
    try:
        zenodo = json.loads((repo / ".zenodo.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f".zenodo.json cannot be parsed: {exc}"]

    if not isinstance(cff, dict):
        return ["CITATION.cff must contain a mapping"]
    if not isinstance(zenodo, dict):
        return [".zenodo.json must contain an object"]

    released = cff.get("date-released")
    released_text = released.isoformat() if isinstance(released, date) else str(released)
    expected_cff = {
        "cff-version": "1.2.0",
        "title": PROJECT_TITLE,
        "type": "software",
        "version": expected_version,
        "url": REPOSITORY_URL,
        "repository-code": REPOSITORY_URL,
        "license": "MIT",
    }
    for key, expected in expected_cff.items():
        if cff.get(key) != expected:
            errors.append(f"CITATION.cff {key} must be {expected!r}")
    try:
        date.fromisoformat(released_text)
    except ValueError:
        errors.append("CITATION.cff date-released must use YYYY-MM-DD")
    if not cff.get("abstract") or not cff.get("message"):
        errors.append("CITATION.cff must contain a message and abstract")

    expected_zenodo = {
        "title": PROJECT_TITLE,
        "upload_type": "software",
        "license": "mit",
        "access_right": "open",
    }
    for key, expected in expected_zenodo.items():
        if zenodo.get(key) != expected:
            errors.append(f".zenodo.json {key} must be {expected!r}")
    if "version" in zenodo or "publication_date" in zenodo:
        errors.append(".zenodo.json must leave version and publication_date to the release")
    if not zenodo.get("description"):
        errors.append(".zenodo.json must contain a description")
    if not _cff_creators(cff) or _cff_creators(cff) != _zenodo_creators(zenodo):
        errors.append("CITATION.cff and .zenodo.json creators/ORCIDs disagree")
    relations = zenodo.get("related_identifiers") or []
    expected_relation = {
        "relation": "isSupplementTo",
        "identifier": REPOSITORY_URL,
        "scheme": "url",
    }
    if expected_relation not in relations:
        errors.append(".zenodo.json must relate the software to its source repository")
    return errors


def prepare_citation(repo: Path, version: str, released: date) -> None:
    """Update release-specific CFF fields and validate both metadata records."""

    distribution_names(version)
    path = repo / "CITATION.cff"
    text = path.read_text(encoding="utf-8")
    for pattern, replacement in (
        (r"^version: .+$", f"version: {version}"),
        (r"^date-released: .+$", f"date-released: {released.isoformat()}"),
    ):
        text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"expected one release field matching {pattern!r}")
    path.write_text(text, encoding="utf-8")
    errors = validate_citation(repo, version)
    if errors:
        raise ValueError("; ".join(errors))


def _expected_manifest(directory: Path, version: str) -> str:
    return "".join(
        f"{sha256(directory / name)}  {name}\n" for name in sorted(distribution_names(version))
    )


def verify_release(
    release: dict,
    tag_ref: dict,
    *,
    version: str,
    commit: str,
    asset_dir: Path,
    state: str,
) -> list[str]:
    """Return violations in GitHub Release identity and local asset parity."""

    names = (*distribution_names(version), "SHA256SUMS")
    errors: list[str] = []
    if not COMMIT_RE.fullmatch(commit):
        return ["commit must be a full lowercase 40-character SHA"]
    if state not in {"draft", "published"}:
        return ["state must be 'draft' or 'published'"]

    expected_release = {
        "tag_name": version,
        "name": version,
        "draft": state == "draft",
        "prerelease": False,
    }
    for key, expected in expected_release.items():
        if release.get(key) != expected:
            errors.append(f"release {key} must be {expected!r}")
    if state == "published" and not release.get("published_at"):
        errors.append("published release must have published_at")
    if state == "draft" and release.get("published_at") is not None:
        errors.append("draft release must not have published_at")

    if tag_ref.get("ref") != f"refs/tags/{version}":
        errors.append("tag ref identity disagrees with the release version")
    tag_object = tag_ref.get("object") or {}
    if tag_object.get("type") != "commit" or tag_object.get("sha") != commit:
        errors.append("release tag is not the expected lightweight commit ref")

    local = {name: asset_dir / name for name in names}
    for name, path in local.items():
        if not path.is_file():
            errors.append(f"missing local release asset: {name}")
    manifest = local["SHA256SUMS"]
    distributions_exist = all(local[name].is_file() for name in distribution_names(version))
    if (
        manifest.is_file()
        and distributions_exist
        and manifest.read_text(encoding="utf-8") != _expected_manifest(asset_dir, version)
    ):
        errors.append("SHA256SUMS does not match the two distribution assets")

    assets = release.get("assets")
    if not isinstance(assets, list):
        errors.append("release assets must be a list")
        return errors
    by_name: dict[str, dict] = {}
    for asset in assets:
        name = asset.get("name")
        if not isinstance(name, str) or name in by_name:
            errors.append("release assets contain an invalid or duplicate name")
            continue
        by_name[name] = asset
    if set(by_name) != set(names):
        errors.append(f"release assets must be exactly {sorted(names)!r}")
    for name, path in local.items():
        asset = by_name.get(name)
        if asset is None or not path.is_file():
            continue
        if asset.get("state") != "uploaded":
            errors.append(f"release asset {name} is not uploaded")
        if asset.get("size") != path.stat().st_size or path.stat().st_size <= 0:
            errors.append(f"release asset {name} size disagrees with local bytes")
        if asset.get("digest") != f"sha256:{sha256(path)}":
            errors.append(f"release asset {name} digest disagrees with local bytes")
    return errors


def verify_zenodo_search(
    payload: dict, *, repo: Path, version: str
) -> tuple[str, list[str], dict | None]:
    """Classify a saved public Zenodo records response."""

    distribution_names(version)
    hits_container = payload.get("hits")
    hits = hits_container.get("hits") if isinstance(hits_container, dict) else None
    if not isinstance(hits, list):
        return "invalid", ["Zenodo response must contain hits.hits as a list"], None
    total = hits_container.get("total")
    if not isinstance(total, int) or total < 0:
        return "invalid", ["Zenodo response must contain a nonnegative integer total"], None
    if total != len(hits):
        return "invalid", ["Zenodo response is incomplete; fetch every matching hit"], None

    exact = []
    for record in hits:
        if not isinstance(record, dict):
            return "invalid", ["Zenodo hits must be JSON objects"], None
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            return "invalid", ["Zenodo record metadata must be a JSON object"], None
        if metadata.get("title") == PROJECT_TITLE and str(metadata.get("version")) == version:
            exact.append(record)
    if not exact:
        return "absent", [], None
    if len(exact) != 1:
        return "invalid", [f"expected one exact Zenodo record, found {len(exact)}"], None

    record = exact[0]
    metadata = record.get("metadata") or {}
    errors: list[str] = []
    doi = record.get("doi")
    if not isinstance(doi, str) or not ZENODO_DOI_RE.fullmatch(doi):
        errors.append("Zenodo record must expose a version DOI")
    if (metadata.get("resource_type") or {}).get("type") != "software":
        errors.append("Zenodo record resource type must be software")
    if metadata.get("access_right") != "open":
        errors.append("Zenodo record access_right must be open")

    expected_metadata = json.loads((repo / ".zenodo.json").read_text(encoding="utf-8"))
    if not isinstance(expected_metadata, dict):
        errors.append(".zenodo.json must contain an object")
        expected_metadata = {}
    expected_creators = _zenodo_creators(expected_metadata)
    actual_creators = _zenodo_creators({"creators": metadata.get("creators", [])})
    if not expected_creators or actual_creators != expected_creators:
        errors.append("Zenodo record creators/ORCIDs disagree with .zenodo.json")

    relations = metadata.get("related_identifiers") or []
    source_relation = {
        "relation": "isSupplementTo",
        "identifier": REPOSITORY_URL,
        "scheme": "url",
    }
    if source_relation not in relations:
        errors.append("Zenodo record does not identify the source repository")

    files = record.get("files")
    if not isinstance(files, list) or not files:
        errors.append("Zenodo record must contain at least one archived file")
    else:
        names: set[str] = set()
        for item in files:
            name = item.get("key") if isinstance(item, dict) else None
            size = item.get("size") if isinstance(item, dict) else None
            checksum = item.get("checksum") if isinstance(item, dict) else None
            if (
                not isinstance(name, str)
                or not name
                or name in names
                or not isinstance(size, int)
                or size <= 0
                or not isinstance(checksum, str)
                or ":" not in checksum
            ):
                errors.append("Zenodo record contains invalid or duplicate file evidence")
                break
            names.add(name)
    return ("verified" if not errors else "invalid"), errors, record


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    notes = subparsers.add_parser("notes")
    notes.add_argument("version")
    notes.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    notes.add_argument("--output", type=Path, required=True)

    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("version")
    manifest.add_argument("--directory", type=Path, default=Path("dist"))

    citation = subparsers.add_parser("citation")
    citation.add_argument("version")
    citation.add_argument("--repo", type=Path, default=Path.cwd())

    prepare = subparsers.add_parser("prepare-citation")
    prepare.add_argument("version")
    prepare.add_argument("--date", dest="released", default=date.today().isoformat())
    prepare.add_argument("--repo", type=Path, default=Path.cwd())

    verify = subparsers.add_parser("verify")
    verify.add_argument("version")
    verify.add_argument("--commit", required=True)
    verify.add_argument("--asset-dir", type=Path, default=Path("dist"))
    verify.add_argument("--release-json", type=Path, required=True)
    verify.add_argument("--tag-json", type=Path, required=True)
    verify.add_argument("--state", choices=("draft", "published"), required=True)

    zenodo = subparsers.add_parser("zenodo")
    zenodo.add_argument("version")
    zenodo.add_argument("--response", type=Path, required=True)
    zenodo.add_argument("--repo", type=Path, default=Path.cwd())

    args = parser.parse_args()
    try:
        if args.command == "notes":
            args.output.write_text(
                extract_release_notes(args.changelog, args.version), encoding="utf-8"
            )
            print(f"Release notes: PASS — {args.version}")
        elif args.command == "manifest":
            path = write_checksum_manifest(args.directory, args.version)
            print(f"Release checksums: PASS — {path}")
        elif args.command == "citation":
            errors = validate_citation(args.repo.resolve(), args.version)
            if errors:
                raise ValueError("; ".join(errors))
            print(f"Release citation: PASS — {args.version}")
        elif args.command == "prepare-citation":
            prepare_citation(args.repo.resolve(), args.version, date.fromisoformat(args.released))
            print(f"Release citation preparation: PASS — {args.version} ({args.released})")
        elif args.command == "verify":
            errors = verify_release(
                _load_json(args.release_json),
                _load_json(args.tag_json),
                version=args.version,
                commit=args.commit,
                asset_dir=args.asset_dir,
                state=args.state,
            )
            if errors:
                raise ValueError("; ".join(errors))
            print(f"GitHub Release: PASS — {args.version} ({args.state})")
        else:
            state, errors, record = verify_zenodo_search(
                _load_json(args.response), repo=args.repo.resolve(), version=args.version
            )
            if state == "absent":
                print(f"Zenodo archive: ABSENT — {args.version}", file=sys.stderr)
                return 2
            if errors:
                raise ValueError("; ".join(errors))
            print(f"Zenodo archive: VERIFIED — {args.version} doi={record['doi']}")
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Release tooling: FAIL — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
