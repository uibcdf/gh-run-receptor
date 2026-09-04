"""Extracting bounded causal evidence from untrusted GitHub log archives."""

from __future__ import annotations

import hashlib
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

MAX_ARCHIVE_MEMBERS = 2_000
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_LINE_BYTES = 16 * 1024

_ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+Z\s+")
_JOB_PREFIX = re.compile(r"^\d+_")
_TEMP_SCRIPT = re.compile(
    r"(?:[A-Za-z]:[\\/]|/)[^:\n]*?(?:_temp|Temp)[\\/][0-9A-Fa-f-]+\.(?:sh|ps1|cmd|bat)"
)


@dataclass(frozen=True)
class Candidate:
    """Representing one possible causal log line."""

    priority: int
    line: int
    kind: str
    message: str


def _clean_line(raw: bytes) -> str:
    text = raw[:MAX_LINE_BYTES].decode("utf-8", errors="replace").rstrip("\r\n")
    return _ANSI.sub("", _TIMESTAMP.sub("", text))


def _candidate(message: str, line: int) -> Candidate | None:
    lowered = message.lower()
    command_missing = (
        "command not found" in lowered
        or "is not recognized as an internal or external command" in lowered
    )
    if command_missing:
        return Candidate(100, line, "command_not_found", message)
    if "no such file or directory" in lowered:
        return Candidate(95, line, "missing_file", message)
    if re.search(r"\b(?:module|import|file)notfounderror\b", message, re.IGNORECASE):
        return Candidate(95, line, "python_import", message)
    if re.search(r"\b(?:segmentation fault|fatal error|out of memory)\b", message, re.IGNORECASE):
        return Candidate(90, line, "fatal", message)
    if "##[error]" in lowered and "process completed with exit code" not in lowered:
        return Candidate(80, line, "github_error", message.replace("##[error]", "", 1).strip())
    if re.search(r"(?:^|:\s)(?:error|exception):\s+\S", message, re.IGNORECASE):
        return Candidate(70, line, "error", message)
    if "##[error]process completed with exit code" in lowered:
        return Candidate(10, line, "exit_code", message.replace("##[error]", "", 1).strip())
    return None


def _normalized(message: str) -> str:
    value = _TEMP_SCRIPT.sub("$RUNNER_TEMP/script", message)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _safe_member(info: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(info.filename)
    mode = info.external_attr >> 16
    return (
        not path.is_absolute()
        and "\\" not in info.filename
        and not re.match(r"^[A-Za-z]:", info.filename)
        and ".." not in path.parts
        and not info.is_dir()
        and not stat.S_ISLNK(mode)
        and info.file_size <= MAX_MEMBER_BYTES
    )


def _bounded_lines(stream: Any):
    line_number = 0
    while raw := stream.readline(MAX_LINE_BYTES + 1):
        line_number += 1
        prefix = raw[:MAX_LINE_BYTES]
        while raw and not raw.endswith((b"\n", b"\r")):
            raw = stream.readline(MAX_LINE_BYTES + 1)
        yield line_number, prefix


def _job_name(filename: str) -> str | None:
    path = PurePosixPath(filename)
    if len(path.parts) != 1 or path.suffix != ".txt":
        return None
    return _JOB_PREFIX.sub("", path.stem)


def extract_causes(
    archive: Path, failed_jobs: list[dict[str, Any]]
) -> tuple[list[dict], list[str]]:
    """Extracting one best causal line per failed job and grouping equal causes."""
    failed_by_name = {str(job.get("name")): job for job in failed_jobs}
    warnings: list[str] = []
    occurrences: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(archive) as zipped:
            infos = zipped.infolist()
            if len(infos) > MAX_ARCHIVE_MEMBERS:
                return [], [f"log archive exceeds the {MAX_ARCHIVE_MEMBERS}-member limit"]
            if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
                return [], [f"log archive exceeds the {MAX_EXPANDED_BYTES}-byte expanded limit"]
            if len({info.filename for info in infos}) != len(infos):
                return [], ["log archive contains duplicate member names"]
            if unsafe := [info.filename for info in infos if not _safe_member(info)]:
                return [], [f"log archive contains an unsafe member: {unsafe[0]}"]
            for info in infos:
                job_name = _job_name(info.filename)
                if job_name not in failed_by_name:
                    continue
                candidates: list[Candidate] = []
                with zipped.open(info) as stream:
                    for line_number, raw in _bounded_lines(stream):
                        if candidate := _candidate(_clean_line(raw), line_number):
                            candidates.append(candidate)
                if not candidates:
                    warnings.append(f"no causal line found for failed job: {job_name}")
                    continue
                best = max(candidates, key=lambda item: (item.priority, item.line))
                normalized = _normalized(best.message)
                occurrences.append(
                    {
                        "job_id": failed_by_name[job_name].get("id"),
                        "job_name": job_name,
                        "member": info.filename,
                        "line": best.line,
                        "kind": best.kind,
                        "message": best.message,
                        "normalized": normalized,
                    }
                )
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        return [], [f"could not analyze log archive: {error}"]

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for occurrence in occurrences:
        key = (occurrence["kind"], occurrence["normalized"])
        grouped.setdefault(key, []).append(occurrence)

    causes = []
    for (kind, normalized), items in grouped.items():
        fingerprint = hashlib.sha256(f"{kind}\0{normalized}".encode()).hexdigest()[:16]
        causes.append(
            {
                "fingerprint": fingerprint,
                "kind": kind,
                "message": normalized,
                "occurrences": sorted(
                    items, key=lambda item: (str(item["job_name"]), item["line"])
                ),
            }
        )
    causes.sort(key=lambda item: (-len(item["occurrences"]), item["fingerprint"]))
    return causes, warnings
