import io

import pytest

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import (
    MINIMUM_GH_VERSION,
    GitHubClient,
    _parse_gh_version,
    _safe_error_line,
    merge_pages,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "gh version 2.48.0 (2024-04-17)\nhttps://github.com/cli/cli/releases/tag/v2.48.0\n",
            (2, 48, 0),
        ),
        ("gh version 2.93.0 (2026-05-27)\r\n", (2, 93, 0)),
        ("gh version 2.48.0-pre.1\n", None),
        ("wrapper version unknown\n", None),
        ("gh version 2.48\n", None),
    ],
)
def test_parse_gh_version_uses_only_the_stable_first_line(text, expected):
    assert _parse_gh_version(text) == expected


def _process(output: bytes, return_code: int = 0):
    class Process:
        def __init__(self):
            self.stdout = io.BytesIO(output)

        def wait(self):
            return return_code

    return Process()


@pytest.mark.parametrize("version", ["2.47.0", "unknown"])
def test_unsupported_cli_fails_before_the_api_command(monkeypatch, version):
    commands = []

    def factory(command, stdout, stderr):
        commands.append(command)
        return _process(f"gh version {version}\n".encode())

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)

    with pytest.raises(AcquisitionError) as captured:
        GitHubClient()._run(["api", "/example"])

    assert captured.value.category == "unsupported_gh_cli"
    assert commands == [["gh", "--version"]]
    assert "2.48.0 or newer" in str(captured.value)


@pytest.mark.parametrize("version", ["2.48.0", "2.93.0"])
def test_supported_cli_is_checked_once_before_requests(monkeypatch, version):
    commands = []

    def factory(command, stdout, stderr):
        commands.append(command)
        if command == ["gh", "--version"]:
            return _process(f"gh version {version}\n".encode())
        return _process(b"{}\n")

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)
    client = GitHubClient()

    assert client._run(["api", "/first"]) == "{}\n"
    assert client._run(["api", "/second"]) == "{}\n"
    assert commands.count(["gh", "--version"]) == 1
    assert MINIMUM_GH_VERSION == (2, 48, 0)


def test_missing_cli_retains_the_executable_failure(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("gh")

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", missing)

    with pytest.raises(AcquisitionError) as captured:
        GitHubClient()._run(["api", "/example"])

    assert captured.value.category == "acquisition_failed"
    assert "could not execute GitHub CLI" in str(captured.value)


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
        lambda endpoint: (_ for _ in ()).throw(
            AcquisitionError(
                "request failed: Not Found (HTTP 404)",
                category="not_found_or_inaccessible",
                http_status=404,
            )
        ),
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


@pytest.mark.parametrize(
    ("stderr", "category", "http_status"),
    [
        (
            b"To get started with GitHub CLI, please run: gh auth login\n"
            b"Alternatively, populate the GH_TOKEN environment variable.\n",
            "authentication_required",
            None,
        ),
        (b"gh: Bad credentials (HTTP 401)\n", "authentication_failed", 401),
        (
            b"gh: You must have repository read permissions. (HTTP 403)\n",
            "permission_denied",
            403,
        ),
        (b"gh: Not Found (HTTP 404)\n", "not_found_or_inaccessible", 404),
        (b"gh: API rate limit exceeded (HTTP 403)\n", "rate_limited", 403),
        (b"gh: service unavailable (HTTP 503)\n", "acquisition_failed", 503),
    ],
)
def test_cli_error_classification_uses_measured_transport_boundaries(stderr, category, http_status):
    observed_category, detail, observed_status = _safe_error_line(stderr)

    assert observed_category == category
    assert observed_status == http_status
    assert detail
    assert len(detail) <= 500


def test_cli_error_text_is_bounded_visible_and_redacted():
    token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    category, detail, status = _safe_error_line(
        f"gh: Authorization: Bearer {token} unsafe\x1b[31m\u202e (HTTP 403)".encode() + b"x" * 1000
    )

    assert category == "permission_denied"
    assert status == 403
    assert token not in detail
    assert "[REDACTED]" in detail
    assert "\\u001b" in detail
    assert "\\u202e" in detail
    assert len(detail) == 500


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "GH_TOKEN=plain-probe-value",
        "access_token=plain-probe-value",
    ],
)
def test_cli_error_text_redacts_supported_credential_shapes(secret):
    _, detail, _ = _safe_error_line(f"gh: rejected {secret} (HTTP 403)".encode())

    assert "plain-probe-value" not in detail
    assert "abcdefghijklmnopqrstuvwxyz123456" not in detail
    assert "[REDACTED]" in detail


def test_run_raises_structured_error_from_failed_process(monkeypatch):
    class FailedProcess:
        def __init__(self, stderr):
            self.stdout = io.BytesIO()
            stderr.write(b"gh: permission denied (HTTP 403)\n")

        def wait(self):
            return 1

    monkeypatch.setattr(
        "gh_run_receptor.github.subprocess.Popen",
        lambda command, stdout, stderr: FailedProcess(stderr),
    )

    client = GitHubClient()
    client._cli_version_checked = True
    with pytest.raises(AcquisitionError) as captured:
        client._run(["api", "/example"])

    assert captured.value.category == "permission_denied"
    assert captured.value.http_status == 403


def test_download_enforces_a_caller_specific_byte_limit(tmp_path, monkeypatch):
    class OversizedProcess:
        def __init__(self):
            self.stdout = io.BytesIO(b"123456")
            self.return_code = 0

        def terminate(self):
            self.return_code = -15

        def wait(self):
            return self.return_code

    monkeypatch.setattr(
        "gh_run_receptor.github.subprocess.Popen",
        lambda command, stdout, stderr: OversizedProcess(),
    )
    destination = tmp_path / "download"

    client = GitHubClient()
    client._cli_version_checked = True
    with pytest.raises(AcquisitionError, match="5-byte limit"):
        client.download("/artifact", destination, max_bytes=5)

    assert not destination.exists()
