import pytest

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import GitHubClient, merge_pages


def test_merge_pages_preserves_every_item():
    payload = [
        {"total_count": 3, "jobs": [{"id": 1}, {"id": 2}]},
        {"total_count": 3, "jobs": [{"id": 3}]},
    ]

    assert merge_pages(payload, "jobs") == {
        "total_count": 3,
        "jobs": [{"id": 1}, {"id": 2}, {"id": 3}],
    }


def test_merge_pages_rejects_wrong_shape():
    with pytest.raises(AcquisitionError, match="unexpected paginated response"):
        merge_pages([{"items": []}], "jobs")


def test_optional_json_treats_only_http_404_as_absent(monkeypatch):
    client = GitHubClient()
    monkeypatch.setattr(
        client,
        "json",
        lambda endpoint: (_ for _ in ()).throw(AcquisitionError("request failed: HTTP 404")),
    )

    assert client.optional_json("/missing") is None


def test_optional_json_preserves_other_acquisition_failures(monkeypatch):
    client = GitHubClient()
    monkeypatch.setattr(
        client,
        "json",
        lambda endpoint: (_ for _ in ()).throw(AcquisitionError("request failed: HTTP 403")),
    )

    with pytest.raises(AcquisitionError, match="HTTP 403"):
        client.optional_json("/forbidden")
