"""Acquiring structured evidence through the authenticated GitHub CLI."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from gh_run_receptor.errors import AcquisitionError

API_VERSION = "2022-11-28"
MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
MAX_ERROR_CHARACTERS = 500
_HTTP_STATUS = re.compile(r"\bHTTP ([1-5][0-9]{2})\b")
_GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
_AUTHORIZATION = re.compile(r"(?i)\b(authorization\s*:\s*(?:bearer|token)\s+)\S+")
_TOKEN_ASSIGNMENT = re.compile(r"(?i)\b(GH_TOKEN|GITHUB_TOKEN|access_token)=\S+")
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def _safe_error_line(error_output: bytes) -> tuple[str, str, int | None]:
    text = error_output.decode("utf-8", errors="replace")
    status_match = _HTTP_STATUS.search(text)
    http_status = int(status_match.group(1)) if status_match else None
    lowered = text.lower()
    if http_status == 429 or "rate limit" in lowered:
        category = "rate_limited"
    elif http_status == 401:
        category = "authentication_failed"
    elif http_status == 403:
        category = "permission_denied"
    elif http_status == 404:
        category = "not_found_or_inaccessible"
    elif "gh auth login" in lowered and "gh_token" in lowered:
        category = "authentication_required"
    else:
        category = "acquisition_failed"

    if category == "authentication_required":
        detail = "GitHub CLI is not authenticated; run gh auth login"
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        detail = lines[-1] if lines else "unknown error"
        if detail.startswith("gh: "):
            detail = detail[4:]
    detail = _GITHUB_TOKEN.sub("[REDACTED]", detail)
    detail = _AUTHORIZATION.sub(r"\1[REDACTED]", detail)
    detail = _TOKEN_ASSIGNMENT.sub(r"\1=[REDACTED]", detail)
    visible = []
    for character in detail:
        codepoint = ord(character)
        if codepoint < 32 or codepoint == 127 or character in _BIDI_CONTROLS:
            visible.append(f"\\u{codepoint:04x}")
        else:
            visible.append(character)
    bounded = "".join(visible)[:MAX_ERROR_CHARACTERS]
    return category, bounded, http_status


def _cli_failure(prefix: str, error_output: bytes) -> AcquisitionError:
    category, detail, http_status = _safe_error_line(error_output)
    return AcquisitionError(
        f"{prefix}: {detail}", category=category, http_status=http_status
    )


class GitHubClient:
    """Calling GitHub APIs without owning authentication credentials."""

    def __init__(self, hostname: str = "github.com") -> None:
        self.hostname = hostname

    def _run(self, arguments: list[str]) -> str:
        command = ["gh", *arguments]
        try:
            with tempfile.TemporaryFile() as stderr:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr)
                assert process.stdout is not None
                chunks: list[bytes] = []
                size = 0
                while chunk := process.stdout.read(READ_CHUNK_BYTES):
                    size += len(chunk)
                    if size > MAX_JSON_BYTES:
                        process.terminate()
                        process.wait()
                        raise AcquisitionError(
                            f"GitHub CLI response exceeded the {MAX_JSON_BYTES}-byte limit"
                        )
                    chunks.append(chunk)
                return_code = process.wait()
                stderr.seek(0)
                error_output = stderr.read(MAX_JSON_BYTES)
        except OSError as error:
            raise AcquisitionError(f"could not execute GitHub CLI: {error}") from error

        if return_code:
            raise _cli_failure("GitHub CLI request failed", error_output)
        try:
            return b"".join(chunks).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise AcquisitionError("GitHub CLI returned non-UTF-8 structured output") from error

    def repository(self, explicit: str | None) -> str:
        """Resolving an explicit or current repository name."""
        if explicit:
            parts = explicit.strip().strip("/").split("/")
            if len(parts) != 2 or not all(parts):
                raise AcquisitionError("repository must use OWNER/REPO form")
            return "/".join(parts)

        output = self._run(
            ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
        )
        repository = output.strip()
        if not repository:
            raise AcquisitionError("could not infer the current GitHub repository")
        return repository

    def json(self, endpoint: str, *, paginate: bool = False) -> Any:
        """Fetching one JSON resource through ``gh api``."""
        arguments = [
            "api",
            "--hostname",
            self.hostname,
            "-H",
            f"X-GitHub-Api-Version: {API_VERSION}",
        ]
        if paginate:
            arguments.extend(["--paginate", "--slurp"])
        arguments.append(endpoint)
        output = self._run(arguments)
        try:
            return json.loads(output)
        except json.JSONDecodeError as error:
            raise AcquisitionError(f"GitHub returned invalid JSON for {endpoint}") from error

    def optional_json(self, endpoint: str) -> Any | None:
        """Fetching JSON while treating an HTTP 404 as an absent optional resource."""
        try:
            return self.json(endpoint)
        except AcquisitionError as error:
            if error.http_status == 404:
                return None
            raise

    def download(
        self,
        endpoint: str,
        destination: Path,
        *,
        max_bytes: int = MAX_DOWNLOAD_BYTES,
    ) -> None:
        """Downloading a binary API response without sending it to stdout."""
        command = [
            "gh",
            "api",
            "--hostname",
            self.hostname,
            "-H",
            f"X-GitHub-Api-Version: {API_VERSION}",
            endpoint,
        ]
        try:
            with destination.open("wb") as stream, tempfile.TemporaryFile() as stderr:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr)
                assert process.stdout is not None
                size = 0
                while chunk := process.stdout.read(READ_CHUNK_BYTES):
                    size += len(chunk)
                    if size > max_bytes:
                        process.terminate()
                        process.wait()
                        raise AcquisitionError(
                            f"GitHub download exceeded the {max_bytes}-byte limit"
                        )
                    stream.write(chunk)
                return_code = process.wait()
                stderr.seek(0)
                error_output = stderr.read(MAX_JSON_BYTES)
        except (FileNotFoundError, OSError) as error:
            destination.unlink(missing_ok=True)
            raise AcquisitionError(f"could not download GitHub evidence: {error}") from error
        except AcquisitionError:
            destination.unlink(missing_ok=True)
            raise
        if return_code:
            destination.unlink(missing_ok=True)
            raise _cli_failure("GitHub CLI download failed", error_output)


def merge_pages(payload: Any, collection: str) -> dict[str, Any]:
    """Merging the object pages emitted by ``gh api --slurp``."""
    pages = payload if isinstance(payload, list) else [payload]
    merged: list[Any] = []
    total_count = 0
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get(collection), list):
            raise AcquisitionError(f"unexpected paginated response for {collection}")
        merged.extend(page[collection])
        total_count = max(total_count, int(page.get("total_count", 0)))
    return {"total_count": max(total_count, len(merged)), collection: merged}
