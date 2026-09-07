import copy
import json
from pathlib import Path

import pytest

from devtools.scripts.release_tools import main, verify_zenodo_search

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.18.0"


def _record() -> dict:
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    return {
        "id": 123456,
        "doi": "10.5281/zenodo.123456",
        "metadata": {
            "title": "gh-run-receptor",
            "version": VERSION,
            "access_right": "open",
            "resource_type": {"type": "software", "title": "Software"},
            "creators": zenodo["creators"],
            "related_identifiers": zenodo["related_identifiers"],
        },
        "files": [
            {
                "key": "uibcdf/gh-run-receptor-0.18.0.zip",
                "size": 1234,
                "checksum": "md5:" + "a" * 32,
            }
        ],
    }


def _search(*records: dict) -> dict:
    return {"hits": {"hits": list(records), "total": len(records)}}


def test_zenodo_verifier_distinguishes_absence_from_invalid_data():
    assert verify_zenodo_search(_search(), repo=ROOT, version=VERSION) == (
        "absent",
        [],
        None,
    )
    state, errors, record = verify_zenodo_search({}, repo=ROOT, version=VERSION)
    assert state == "invalid"
    assert errors == ["Zenodo response must contain hits.hits as a list"]
    assert record is None


def test_zenodo_verifier_rejects_incomplete_or_malformed_hit_pages():
    incomplete = _search(_record())
    incomplete["hits"]["total"] = 2
    malformed = _search(_record())
    malformed["hits"]["hits"][0]["metadata"] = []

    for payload, message in (
        (incomplete, "fetch every matching hit"),
        (malformed, "metadata must be a JSON object"),
    ):
        state, errors, record = verify_zenodo_search(payload, repo=ROOT, version=VERSION)
        assert state == "invalid"
        assert message in " ".join(errors)
        assert record is None


def test_zenodo_verifier_accepts_one_semantically_complete_record():
    expected = _record()

    state, errors, record = verify_zenodo_search(_search(expected), repo=ROOT, version=VERSION)

    assert state == "verified"
    assert errors == []
    assert record == expected


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda item: item.update(doi=""), "version DOI"),
        (lambda item: item["metadata"].update(resource_type={}), "resource type"),
        (lambda item: item["metadata"].update(access_right="closed"), "access_right"),
        (lambda item: item["metadata"].update(creators=[]), "creators/ORCIDs"),
        (lambda item: item["metadata"].update(related_identifiers=[]), "source repository"),
        (lambda item: item.update(files=[]), "archived file"),
        (lambda item: item["files"].append(dict(item["files"][0])), "duplicate file"),
    ],
)
def test_zenodo_verifier_rejects_incomplete_or_inconsistent_records(mutation, message):
    record = copy.deepcopy(_record())
    mutation(record)

    state, errors, _ = verify_zenodo_search(_search(record), repo=ROOT, version=VERSION)

    assert state == "invalid"
    assert message in " ".join(errors)


def test_zenodo_verifier_rejects_ambiguous_exact_records():
    state, errors, record = verify_zenodo_search(
        _search(_record(), _record()), repo=ROOT, version=VERSION
    )

    assert state == "invalid"
    assert errors == ["expected one exact Zenodo record, found 2"]
    assert record is None


def test_zenodo_verifier_ignores_other_titles_and_versions():
    wrong_title = copy.deepcopy(_record())
    wrong_title["metadata"]["title"] = "another-project"
    wrong_version = copy.deepcopy(_record())
    wrong_version["metadata"]["version"] = "0.17.0"

    assert verify_zenodo_search(
        _search(wrong_title, wrong_version), repo=ROOT, version=VERSION
    ) == ("absent", [], None)


@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_stream", "expected_text"),
    [
        (_search(_record()), 0, "out", "Zenodo archive: VERIFIED"),
        (_search(), 2, "err", "Zenodo archive: ABSENT"),
        ({}, 1, "err", "Release tooling: FAIL"),
    ],
)
def test_zenodo_cli_preserves_three_distinct_states(
    payload, expected_code, expected_stream, expected_text, tmp_path, monkeypatch, capsys
):
    response = tmp_path / "response.json"
    response.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "release_tools.py",
            "zenodo",
            VERSION,
            "--response",
            str(response),
            "--repo",
            str(ROOT),
        ],
    )

    assert main() == expected_code
    captured = capsys.readouterr()
    assert expected_text in getattr(captured, expected_stream)
    assert len(captured.out.splitlines()) + len(captured.err.splitlines()) == 1
