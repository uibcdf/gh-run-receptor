"""Acquiring structured evidence through the authenticated GitHub CLI."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from gh_run_receptor.errors import AcquisitionError

API_VERSION = "2022-11-28"
MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024


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
            error_text = error_output.decode("utf-8", errors="replace")
            message = error_text.strip().splitlines()[-1] if error_text.strip() else "unknown error"
            raise AcquisitionError(f"GitHub CLI request failed: {message}")
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

    def download(self, endpoint: str, destination: Path) -> None:
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
                    if size > MAX_DOWNLOAD_BYTES:
                        process.terminate()
                        process.wait()
                        raise AcquisitionError(
                            f"GitHub download exceeded the {MAX_DOWNLOAD_BYTES}-byte limit"
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
            message = error_output.decode("utf-8", errors="replace").strip().splitlines()
            detail = message[-1] if message else "unknown error"
            raise AcquisitionError(f"GitHub CLI download failed: {detail}")


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
