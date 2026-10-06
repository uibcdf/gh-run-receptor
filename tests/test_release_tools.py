import io
import json
import tarfile
import tomllib
import zipfile
from datetime import date
from pathlib import Path

import pytest
import yaml

from devtools.scripts import distribution_archives
from devtools.scripts.distribution_archives import inspect_distribution, verify_distributions
from devtools.scripts.release_tools import (
    extract_release_notes,
    prepare_citation,
    sha256,
    validate_citation,
    verify_release,
    write_checksum_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.18.0"
CURRENT_VERSION = "1.2.0"
COMMIT = "a" * 40


def _payload(kind: str) -> dict[str, bytes]:
    inventory = tomllib.loads((ROOT / "devtools/conda-build/resources.toml").read_text())
    data = {}
    for name in inventory["required_paths"]:
        name = name.removeprefix("site-packages/")
        data[name] = (
            f'__version__ = "{VERSION}"\n'.encode()
            if name.endswith("/_version.py")
            else (ROOT / name).read_bytes()
        )
    metadata = (
        f"Metadata-Version: 2.4\nName: gh-run-receptor\nVersion: {VERSION}\n"
        "Requires-Python: >=3.11,<3.15\n\n"
    ).encode()
    if kind == "wheel":
        data[f"gh_run_receptor-{VERSION}.dist-info/METADATA"] = metadata
        return data
    data["PKG-INFO"] = metadata
    data["gh_run_receptor.egg-info/PKG-INFO"] = metadata
    data["pyproject.toml"] = (ROOT / "pyproject.toml").read_bytes()
    return {f"gh_run_receptor-{VERSION}/{name}": raw for name, raw in data.items()}


def _write_archive(tmp_path: Path, kind: str, data: dict[str, bytes]) -> Path:
    if kind == "wheel":
        path = tmp_path / f"gh_run_receptor-{VERSION}-py3-none-any.whl"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in data.items():
                archive.writestr(name, raw)
    else:
        path = tmp_path / f"gh_run_receptor-{VERSION}.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for name, raw in data.items():
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
    return path


def _assets(tmp_path: Path) -> None:
    for kind in ("wheel", "sdist"):
        _write_archive(tmp_path, kind, _payload(kind))
    write_checksum_manifest(tmp_path, VERSION)


def _release(tmp_path: Path, *, draft: bool = False) -> dict:
    return {
        "tag_name": VERSION,
        "name": VERSION,
        "draft": draft,
        "prerelease": False,
        "published_at": None if draft else "2026-09-07T12:00:00Z",
        "assets": [
            {
                "name": path.name,
                "state": "uploaded",
                "size": path.stat().st_size,
                "digest": f"sha256:{sha256(path)}",
            }
            for path in sorted(tmp_path.iterdir())
        ],
    }


def _tag_ref() -> dict:
    return {"ref": f"refs/tags/{VERSION}", "object": {"type": "commit", "sha": COMMIT}}


def test_extract_release_notes_selects_exact_nonempty_section(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changes\n\n## Unreleased\n\n## 0.18.0 - 2026-09-07\n\n- New.\n\n"
        "## 0.17.0 - 2026-09-07\n\n- Old.\n",
        encoding="utf-8",
    )

    assert extract_release_notes(changelog, VERSION) == "- New.\n"


def test_extract_release_notes_rejects_missing_and_empty_sections(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## 0.18.0 - 2026-09-07\n\n", encoding="utf-8")

    for version in (VERSION, "0.18.0"):
        try:
            extract_release_notes(changelog, version)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid changelog section was accepted")


def test_manifest_requires_exact_distributions_and_is_deterministic(tmp_path):
    wheel = tmp_path / f"gh_run_receptor-{VERSION}-py3-none-any.whl"
    source = tmp_path / f"gh_run_receptor-{VERSION}.tar.gz"
    wheel.write_bytes(b"wheel")
    source.write_bytes(b"source")

    manifest = write_checksum_manifest(tmp_path, VERSION)

    assert manifest.read_text(encoding="utf-8") == (
        f"{sha256(wheel)}  {wheel.name}\n{sha256(source)}  {source.name}\n"
    )
    try:
        write_checksum_manifest(tmp_path, VERSION)
    except ValueError:
        pass
    else:
        raise AssertionError("an unexpected pre-existing manifest was accepted")


def test_repository_citation_metadata_is_consistent():
    assert validate_citation(ROOT, CURRENT_VERSION) == []


def test_citation_validator_detects_creator_disagreement(tmp_path):
    cff = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    zenodo["creators"][0]["orcid"] = "0000-0000-0000-0000"
    (tmp_path / "CITATION.cff").write_text(yaml.safe_dump(cff), encoding="utf-8")
    (tmp_path / ".zenodo.json").write_text(json.dumps(zenodo), encoding="utf-8")

    assert "creators/ORCIDs disagree" in " ".join(validate_citation(tmp_path, VERSION))


def test_prepare_citation_updates_release_fields_and_revalidates(tmp_path):
    (tmp_path / "CITATION.cff").write_text(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / ".zenodo.json").write_text(
        (ROOT / ".zenodo.json").read_text(encoding="utf-8"), encoding="utf-8"
    )

    prepare_citation(tmp_path, "0.19.1", date(2026, 9, 8))

    cff = yaml.safe_load((tmp_path / "CITATION.cff").read_text(encoding="utf-8"))
    assert cff["version"] == "0.19.1"
    assert cff["date-released"].isoformat() == "2026-09-08"
    assert validate_citation(tmp_path, "0.19.1") == []


def test_release_verifier_accepts_exact_draft_and_published_assets(tmp_path):
    _assets(tmp_path)

    assert (
        verify_release(
            _release(tmp_path, draft=True),
            _tag_ref(),
            version=VERSION,
            commit=COMMIT,
            asset_dir=tmp_path,
            state="draft",
        )
        == []
    )
    assert (
        verify_release(
            _release(tmp_path),
            _tag_ref(),
            version=VERSION,
            commit=COMMIT,
            asset_dir=tmp_path,
            state="published",
        )
        == []
    )


def test_release_verifier_rejects_wrong_truth_identity_and_bytes(tmp_path):
    _assets(tmp_path)
    release = _release(tmp_path)
    release["prerelease"] = True
    release["assets"][0]["digest"] = "sha256:" + "0" * 64
    release["assets"].append(dict(release["assets"][0]))
    tag_ref = _tag_ref()
    tag_ref["object"]["sha"] = "b" * 40

    errors = verify_release(
        release,
        tag_ref,
        version=VERSION,
        commit=COMMIT,
        asset_dir=tmp_path,
        state="published",
    )

    assert any("prerelease" in error for error in errors)
    assert any("duplicate" in error for error in errors)
    assert any("digest" in error for error in errors)
    assert any("lightweight commit" in error for error in errors)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize(
    "mutation",
    [
        "metadata",
        "name",
        "duplicate-version",
        "generated",
        "ambiguous-generated",
        "executable-version",
        "missing-code",
        "missing-schema",
        "changed-schema",
        "extra-schema",
        "python",
    ],
)
def test_archive_payload_mutations_fail_even_with_matching_names_and_digests(
    tmp_path, kind, mutation
):
    _assets(tmp_path)
    data = _payload(kind)
    prefix = "" if kind == "wheel" else f"gh_run_receptor-{VERSION}/"
    metadata = f"gh_run_receptor-{VERSION}.dist-info/METADATA" if kind == "wheel" else "PKG-INFO"
    metadata = prefix + metadata
    generated = prefix + "gh_run_receptor/_version.py"
    schema = prefix + "gh_run_receptor/schemas/model-v1.schema.json"
    if mutation == "metadata":
        data[metadata] = data[metadata].replace(VERSION.encode(), b"9.9.9")
    elif mutation == "name":
        data[metadata] = data[metadata].replace(b"Name: gh-run-receptor", b"Name: other-project")
    elif mutation == "duplicate-version":
        data[metadata] = data[metadata].replace(b"\n\n", b"\nVersion: 9.9.9\n\n")
    elif mutation == "generated":
        data[generated] = b'__version__ = "9.9.9"\n'
    elif mutation == "ambiguous-generated":
        data[generated] += b'__version__ = "9.9.9"\n'
    elif mutation == "executable-version":
        data[generated] = b'__version__ = __import__("os").getcwd()\n'
    elif mutation == "missing-code":
        del data[prefix + "gh_run_receptor/cli.py"]
    elif mutation == "missing-schema":
        del data[schema]
    elif mutation == "changed-schema":
        data[schema] += b"\n"
    elif mutation == "extra-schema":
        data[prefix + "gh_run_receptor/schemas/unreviewed-v1.schema.json"] = b"{}"
    else:
        data[metadata] = data[metadata].replace(b">=3.11,<3.15", b">=3.11,<3.14")
    _write_archive(tmp_path, kind, data)
    (tmp_path / "SHA256SUMS").unlink()
    write_checksum_manifest(tmp_path, VERSION)
    release = _release(tmp_path)
    errors = verify_release(
        release, _tag_ref(), version=VERSION, commit=COMMIT, asset_dir=tmp_path, state="published"
    )
    assert errors
    assert not any(
        "digest disagrees" in error or "SHA256SUMS does not match" in error for error in errors
    )


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("name", ["../escape", "/absolute", "back\\slash", "C:/drive", "a/./b"])
def test_archive_reader_rejects_unsafe_paths_without_extraction(tmp_path, kind, name):
    path = _write_archive(tmp_path, kind, {name: b"bad"})
    with pytest.raises(ValueError, match="Unsafe"):
        inspect_distribution(path, version=VERSION, repo=ROOT)
    assert not (tmp_path.parent / "escape").exists()


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_archive_reader_rejects_duplicate_paths(tmp_path, kind):
    path = _write_archive(tmp_path, kind, {"duplicate": b"one"})
    if kind == "wheel":
        with zipfile.ZipFile(path, "a") as archive, pytest.warns(UserWarning):
            archive.writestr("duplicate", b"two")
    else:
        with tarfile.open(path, "w:gz") as archive:
            for raw in (b"one", b"two"):
                member = tarfile.TarInfo("duplicate")
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
    with pytest.raises(ValueError, match="duplicate"):
        inspect_distribution(path, version=VERSION, repo=ROOT)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("bound", ["MAX_ARCHIVE_BYTES", "MAX_MEMBER_BYTES", "MAX_MEMBERS"])
def test_archive_reader_enforces_size_and_count_bounds(tmp_path, monkeypatch, kind, bound):
    path = _write_archive(tmp_path, kind, _payload(kind))
    monkeypatch.setattr(distribution_archives, bound, 1)
    with pytest.raises(ValueError, match="bound"):
        inspect_distribution(path, version=VERSION, repo=ROOT)


def test_archive_reader_rejects_tar_links(tmp_path):
    path = tmp_path / f"gh_run_receptor-{VERSION}.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("linked")
        member.type = tarfile.SYMTYPE
        member.linkname = "/outside"
        archive.addfile(member)
    with pytest.raises(ValueError, match="link"):
        inspect_distribution(path, version=VERSION, repo=ROOT)


def test_archive_verifier_returns_missing_and_truncated_errors(tmp_path):
    assert len(verify_distributions(tmp_path, version=VERSION, repo=ROOT)) == 2
    for kind in ("wheel", "sdist"):
        path = _write_archive(tmp_path, kind, _payload(kind))
        path.write_bytes(path.read_bytes()[:20])
    assert len(verify_distributions(tmp_path, version=VERSION, repo=ROOT)) == 2


def test_source_archive_checks_secondary_metadata_and_root(tmp_path):
    data = _payload("sdist")
    secondary = f"gh_run_receptor-{VERSION}/gh_run_receptor.egg-info/PKG-INFO"
    data[secondary] = data[secondary].replace(VERSION.encode(), b"9.9.9")
    path = _write_archive(tmp_path, "sdist", data)
    with pytest.raises(ValueError, match="PKG-INFO Version"):
        inspect_distribution(path, version=VERSION, repo=ROOT)
    data = _payload("sdist")
    data["other-root/extra"] = b"extra"
    path = _write_archive(tmp_path, "sdist", data)
    with pytest.raises(ValueError, match="root"):
        inspect_distribution(path, version=VERSION, repo=ROOT)


def test_wheel_archive_rejects_extra_distribution_and_zip_link(tmp_path):
    data = _payload("wheel")
    data["other.dist-info/METADATA"] = b"Name: other\n"
    path = _write_archive(tmp_path, "wheel", data)
    with pytest.raises(ValueError, match="exactly"):
        inspect_distribution(path, version=VERSION, repo=ROOT)
    path = _write_archive(tmp_path, "wheel", _payload("wheel"))
    with zipfile.ZipFile(path, "a") as archive:
        info = zipfile.ZipInfo("linked")
        info.external_attr = 0o120777 << 16
        archive.writestr(info, "/outside")
    with pytest.raises(ValueError, match="link"):
        inspect_distribution(path, version=VERSION, repo=ROOT)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_archive_reader_bounds_total_decompressed_bytes(tmp_path, monkeypatch, kind):
    data = {f"file-{i}": b"x" * 1000 for i in range(10)}
    path = _write_archive(tmp_path, kind, data)
    monkeypatch.setattr(distribution_archives, "MAX_ARCHIVE_BYTES", 5000)
    assert path.stat().st_size < 5000
    with pytest.raises(ValueError, match="decompressed"):
        inspect_distribution(path, version=VERSION, repo=ROOT)
