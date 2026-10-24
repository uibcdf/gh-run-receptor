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


@pytest.mark.parametrize("limit,accepted", [(3, True), (2, False)])
def test_json_transport_enforces_a_caller_specific_byte_limit(monkeypatch, limit, accepted):
    process = _process(b"[]\n")
    terminated = []
    process.terminate = lambda: terminated.append(True)
    monkeypatch.setattr(
        "gh_run_receptor.github.subprocess.Popen", lambda command, stdout, stderr: process
    )
    client = GitHubClient()
    client._cli_version_checked = True
    if accepted:
        assert client.json("/example", max_bytes=limit) == []
        assert terminated == []
    else:
        with pytest.raises(AcquisitionError, match="2-byte limit"):
            client.json("/example", max_bytes=limit)
        assert terminated == [True]


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


@pytest.mark.parametrize("mode", ["json", "download"])
@pytest.mark.parametrize(
    "stderr, category, status",
    [
        (
            b'Get "https://api.github.com/private?token=private-value": dial tcp: no such host\n'
            b"check your internet connection or https://githubstatus.com\n",
            "acquisition_failed",
            None,
        ),
        (b"gh: Not Found (HTTP 404)\n", "not_found_or_inaccessible", 404),
        (b"gh: permission denied (HTTP 403)\n", "permission_denied", 403),
        (b"gh: Bad credentials (HTTP 401)\n", "authentication_failed", 401),
        (b"gh: API rate limit exceeded (HTTP 429)\n", "rate_limited", 429),
    ],
)
def test_failed_request_keeps_identity_status_diagnostic_and_no_retry(
    tmp_path, monkeypatch, mode, stderr, category, status
):
    calls = []

    def factory(command, stdout, stderr):
        calls.append(command)
        # Popen's named stderr argument is the private output stream.
        stderr.write(error_bytes)
        return _process(b"", 1)

    error_bytes = stderr
    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)
    client = GitHubClient()
    client._cli_version_checked = True
    endpoint = "/repos/uibcdf/moli/actions/runs/39513025386?access_token=private-value"
    output = tmp_path / "partial"
    with pytest.raises(AcquisitionError) as captured:
        if mode == "json":
            client.json(endpoint)
        else:
            client.download(endpoint, output)
    error = captured.value
    assert error.category == category and error.http_status == status
    assert error.operation == f"api.{mode}"
    assert error.request_path == endpoint.split("?")[0]
    assert error.request_path in str(error)
    assert "private-value" not in str(error)
    assert "check your internet connection" not in str(error)
    if category == "acquisition_failed":
        assert "dial tcp: no such host" in str(error)
    assert len(calls) == 1
    assert not output.exists()


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/" + "a" * 1000,
        "https://user:secret@host/path?signature=secret",
        "/repos/name\nTOKEN=secret",
        "/api/%0a",
    ],
)
def test_request_context_never_prints_credentials_or_control_characters(monkeypatch, endpoint):
    def factory(command, stdout, stderr):
        stderr.write(b"gh: rejected (HTTP 403)\n")
        return _process(b"", 1)

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)
    client = GitHubClient()
    client._cli_version_checked = True
    with pytest.raises(AcquisitionError) as captured:
        client.json(endpoint)
    assert "secret" not in str(captured.value)
    assert "\n" not in str(captured.value)
    assert len(captured.value.request_path) <= 240
    assert len(str(captured.value)) <= 800


@pytest.mark.parametrize(
    "output, diagnostic", [(b"{truncated", "invalid JSON"), (b"\xff", "non-UTF-8")]
)
def test_malformed_response_retains_safe_request_context(monkeypatch, output, diagnostic):
    monkeypatch.setattr(
        "gh_run_receptor.github.subprocess.Popen", lambda *args, **kwargs: _process(output)
    )
    client = GitHubClient()
    client._cli_version_checked = True
    with pytest.raises(AcquisitionError, match=diagnostic) as captured:
        client.json("/repos/example/project/actions/runs/1")
    assert captured.value.operation == "api.json"
    assert captured.value.request_path == "/repos/example/project/actions/runs/1"


def test_version_failure_is_not_misattributed_to_an_api_request(monkeypatch):
    def factory(command, stdout, stderr):
        stderr.write(b"gh: cannot execute version probe\n")
        return _process(b"", 1)

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)
    with pytest.raises(AcquisitionError) as captured:
        GitHubClient().json("/example")
    assert captured.value.operation == "cli.version"
    assert captured.value.request_path is None


def test_cli_request_failure_keeps_exit_five_and_one_safe_line(monkeypatch, capsys):
    from gh_run_receptor.cli import main

    def factory(command, stdout, stderr):
        if command == ["gh", "--version"]:
            return _process(b"gh version 2.100.0\n")
        stderr.write(
            b"error connecting to api.github.com\ncheck your internet connection or https://githubstatus.com\n"
        )
        return _process(b"", 1)

    monkeypatch.setattr("gh_run_receptor.github.subprocess.Popen", factory)
    result = main(["inspect", "39513025386", "--repo", "uibcdf/moli", "--receptor", "llm"])
    output = capsys.readouterr()
    assert result == 5
    assert output.out == ""
    assert len(output.err.splitlines()) == 1
    assert "category=acquisition_failed" in output.err
    assert "api.json /repos/uibcdf/moli/actions/runs/39513025386" in output.err
    assert "error connecting to api.github.com" in output.err
    assert "check your internet connection" not in output.err


@pytest.mark.parametrize("length", [239, 240, 241])
def test_safe_request_path_has_an_exact_size_boundary(length):
    from gh_run_receptor.github import _request_error

    path = "/" + "a" * (length - 1)
    error = _request_error(AcquisitionError("failed"), "api.json", path)
    assert error.request_path == path[:240]
    assert len(error.request_path) == min(length, 240)
