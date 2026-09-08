import json
from datetime import date
from pathlib import Path

import yaml

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
CURRENT_VERSION = "0.19.0"
COMMIT = "a" * 40


def _assets(tmp_path: Path) -> None:
    (tmp_path / f"gh_run_receptor-{VERSION}-py3-none-any.whl").write_bytes(b"wheel")
    (tmp_path / f"gh_run_receptor-{VERSION}.tar.gz").write_bytes(b"source")
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

    prepare_citation(tmp_path, "0.19.0", date(2026, 9, 8))

    cff = yaml.safe_load((tmp_path / "CITATION.cff").read_text(encoding="utf-8"))
    assert cff["version"] == "0.19.0"
    assert cff["date-released"].isoformat() == "2026-09-08"
    assert validate_citation(tmp_path, "0.19.0") == []


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
