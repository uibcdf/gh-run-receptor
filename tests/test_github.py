import pytest

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import merge_pages


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
