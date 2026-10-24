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
MAX_CAUSE_CHARACTERS = 500
MAX_PYTEST_SUMMARY_LINES = 128
MAX_TRACEBACK_LINES = 128
MAX_SOLVER_PACKAGES = 4
MAX_SOLVER_LINES = 128

_ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+Z\s+")
_JOB_PREFIX = re.compile(r"^\d+_")
_TEMP_SCRIPT = re.compile(
    r"(?:[A-Za-z]:[\\/]|/)[^:\n]*?(?:_temp|Temp)[\\/][0-9A-Fa-f-]+\.(?:sh|ps1|cmd|bat)"
)
_STRUCTURED_DIAGNOSTIC = re.compile(
    r"^[A-Za-z][A-Za-z0-9 ._/-]{0,79}:\s+"
    r"(?:FAIL|ERROR|ABSENT|INVALID|UNAVAILABLE|CANCELLED|TIMED_OUT|PARTIAL|"
    r"INCOMPLETE|UNKNOWN)\b",
    re.IGNORECASE,
)
_PYTEST_FAILED = re.compile(r"^FAILED\s+(\S+::\S+)\s+-\s+\S")
_PYTEST_RECEPTOR_FAILURE = re.compile(r"^FAIL exit=[1-9][0-9]*\s*\|")
# Match the command suggestion printed by pytest-receptor; never execute it.
_PYTEST_RECEPTOR_RERUN = re.compile(
    r"^\s*rerun:\s+(?:(?:uv run )?pytest|python -m pytest)\s+(\S+::\S+)(?:\s|$)"
)
_PYTEST_GROUP = re.compile(r"^\[[1-9][0-9]*\]\s+([\w.]+)\s*\|\s+[1-9][0-9]* tests?\s*\|")
_PYTEST_LOCATION = re.compile(r"^((?:[A-Za-z]:)?[^:<>|\r\n]+\.py):([1-9][0-9]*)$")
_PYTEST_NODE = re.compile(r"^\S+\.py::\S+$")
_CURL_FAILURE = re.compile(r"^curl:\s+\([1-9][0-9]{0,2}\)\s+\S")
_REJECTED_DIAGNOSTIC = re.compile(r"^[A-Za-z][A-Za-z0-9 ._/-]{0,79} rejected:\s+\S")
_PYTHON_FRAME = re.compile(r'^\s+File "([^"]+)", line (\d+)')
_PYTHON_EXCEPTION = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception)):\s+\S")
_SOLVER_MISSING = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9_.-]*)\s+([=<>!~][^,;]{0,200}?)"
    r"(?:,\s+which)?\s+does not exist\b",
    re.IGNORECASE,
)
_GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
_AUTHORIZATION = re.compile(r"(?i)\b(authorization\s*:\s*(?:bearer|token)\s+)\S+")
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b((?:[A-Za-z_][A-Za-z0-9_]*_)?"
    r"(?:TOKEN|PASSWORD|PASSWD|SECRET|API_KEY|PRIVATE_KEY))"
    r"(\s*[:=]\s*)\S+"
)


@dataclass(frozen=True)
class Candidate:
    """Representing one possible causal log line."""

    priority: int
    line: int
    kind: str
    message: str
    context: tuple[Candidate, ...] = ()


def _retain_candidate(candidates: dict[str, Candidate], candidate: Candidate) -> None:
    old = candidates.get(candidate.kind)
    if old is None or (candidate.priority, candidate.line) >= (old.priority, old.line):
        candidates[candidate.kind] = candidate


class _PytestSummary:
    """Read a bounded failed receptor group without executing suggested commands."""

    def __init__(self):
        self.start: int | None = None
        self.group: str | None = None
        self.location: str | None = None
        self.location_line: int | None = None
        self.exception: Candidate | None = None
        self.tests: list[Candidate] = []
        self.in_tests = False

    def feed(self, message: str, line: int) -> Candidate | None:
        text = message.strip()
        if _PYTEST_RECEPTOR_FAILURE.match(text):
            self.__init__()
            self.start = line
        if self.start is None or line - self.start > MAX_PYTEST_SUMMARY_LINES:
            return None
        if text.startswith("PASS exit="):
            self.__init__()
            return None
        if group := _PYTEST_GROUP.match(text):
            self.group = group.group(1).split(".")[-1]
            self.location = None
            self.location_line = None
            self.exception = None
            self.tests = []
            self.in_tests = False
        elif (
            self.group and self.location is None and (location := _PYTEST_LOCATION.fullmatch(text))
        ):
            path = location.group(1).replace("\\", "/")
            if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
                path = PurePosixPath(path).name
            self.location = f"{path}:{location.group(2)}"
            self.location_line = line
        elif self.group and self.location and self.exception is None:
            if (match := _PYTHON_EXCEPTION.match(text)) and match.group(1).split(".")[
                -1
            ] == self.group:
                self.exception = Candidate(120, line, "pytest_failure", text)
        if text == "tests:":
            self.in_tests = True
        node = text if self.in_tests and _PYTEST_NODE.fullmatch(text) else None
        if rerun := _PYTEST_RECEPTOR_RERUN.match(text):
            node = rerun.group(1)
        if node and len(self.tests) < 2:
            node = node.replace("\\", "/")
            if node not in {item.message for item in self.tests}:
                self.tests.append(Candidate(0, line, "test", node))
        if self.exception is None:
            return None
        frame = Candidate(
            0, self.location_line or self.exception.line, "frame", self.location or ""
        )
        return Candidate(
            120,
            self.exception.line,
            "pytest_failure",
            f"{self.exception.message} | at {self.location}",
            (frame, *self.tests),
        )


def _clean_line(raw: bytes) -> str:
    text = raw[:MAX_LINE_BYTES].decode("utf-8", errors="replace").rstrip("\r\n")
    return _ANSI.sub("", _TIMESTAMP.sub("", text))


def _candidate(message: str, line: int) -> Candidate | None:
    if _CURL_FAILURE.match(message):
        return Candidate(110, line, "download_error", message)
    if match := _PYTEST_FAILED.match(message):
        nodeid = match.group(1).replace("\\", "/")
        return Candidate(75, line, "pytest_test", f"pytest failed: {nodeid}")
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


def _safe_cause(message: str) -> str:
    value = _GITHUB_TOKEN.sub("[REDACTED]", message)
    value = _AUTHORIZATION.sub(r"\1[REDACTED]", value)
    value = _CREDENTIAL_ASSIGNMENT.sub(r"\1\2[REDACTED]", value)
    return value[:MAX_CAUSE_CHARACTERS]


def _adjacent_diagnostic(message: str, line: int) -> Candidate | None:
    if _STRUCTURED_DIAGNOSTIC.search(message) or _REJECTED_DIAGNOSTIC.match(message):
        return Candidate(20, line, "structured_diagnostic", message)
    return None


def safe_diagnostic_text(message: str) -> str:
    """Redacting and bounding untrusted diagnostic text before derived storage."""
    return _safe_cause(message)


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
                candidates: dict[str, Candidate] = {}

                summary = _PytestSummary()
                previous: tuple[str, int] | None = None
                receptor_failure_line: int | None = None
                traceback_line: int | None = None
                traceback_frame: str | None = None
                solver_start: int | None = None
                solver_packages: list[str] = []
                solver_line: int | None = None
                with zipped.open(info) as stream:
                    for line_number, raw in _bounded_lines(stream):
                        message = _clean_line(raw)
                        if message == "Traceback (most recent call last):":
                            traceback_line = line_number
                            traceback_frame = None
                        if traceback_line is not None:
                            if line_number - traceback_line > MAX_TRACEBACK_LINES:
                                traceback_line = None
                                traceback_frame = None
                            elif frame := _PYTHON_FRAME.match(message):
                                frame_path = frame.group(1).replace("\\", "/")
                                traceback_frame = (
                                    f"{PurePosixPath(frame_path).name}:{frame.group(2)}"
                                )
                            elif traceback_frame and _PYTHON_EXCEPTION.match(message):
                                _retain_candidate(
                                    candidates,
                                    Candidate(
                                        115,
                                        line_number,
                                        "python_exception",
                                        f"{message} | at {traceback_frame}",
                                    ),
                                )
                                traceback_line = None
                                traceback_frame = None
                        if "libmamba Could not solve for environment specs" in message:
                            solver_start = line_number
                        elif solver_start is not None and (
                            message.startswith("##[error]")
                            or line_number - solver_start > MAX_SOLVER_LINES
                        ):
                            solver_start = None
                        if (
                            solver_start is not None
                            and len(solver_packages) < MAX_SOLVER_PACKAGES
                            and (missing := _SOLVER_MISSING.search(message))
                        ):
                            constraint = re.sub(r"\s+\*$", "", missing.group(2)).strip()
                            package = f"{missing.group(1)} {constraint}"
                            if package not in solver_packages:
                                solver_packages.append(package)
                                solver_line = line_number
                        if detailed := summary.feed(message, line_number):
                            _retain_candidate(candidates, detailed)
                        if _PYTEST_RECEPTOR_FAILURE.match(message):
                            receptor_failure_line = line_number
                        elif (
                            receptor_failure_line is not None
                            and line_number - receptor_failure_line <= MAX_PYTEST_SUMMARY_LINES
                            and (rerun := _PYTEST_RECEPTOR_RERUN.match(message))
                        ):
                            nodeid = rerun.group(1).replace("\\", "/")
                            _retain_candidate(
                                candidates,
                                Candidate(
                                    75,
                                    line_number,
                                    "pytest_test",
                                    f"pytest failed: {nodeid}",
                                ),
                            )
                        if candidate := _candidate(message, line_number):
                            _retain_candidate(candidates, candidate)
                            if (
                                candidate.kind == "exit_code"
                                and previous is not None
                                and line_number - previous[1] <= 3
                                and (adjacent := _adjacent_diagnostic(*previous))
                            ):
                                _retain_candidate(candidates, adjacent)
                        if message.strip():
                            previous = (message, line_number)
                if solver_packages:
                    _retain_candidate(
                        candidates,
                        Candidate(
                            110,
                            solver_line or 1,
                            "conda_solver",
                            "conda packages unavailable: " + ", ".join(solver_packages),
                        ),
                    )
                if not candidates:
                    warnings.append(f"no causal line found for failed job: {job_name}")
                    continue
                best = max(candidates.values(), key=lambda item: (item.priority, item.line))
                safe_message = _safe_cause(best.message)
                normalized = _normalized(safe_message)
                context = list(best.context)
                later = candidates.get("missing_file")
                if (
                    best.kind in {"download_error", "conda_solver"}
                    and later is not None
                    and 0 < later.line - best.line <= MAX_SOLVER_LINES
                ):
                    context.append(Candidate(0, later.line, "later diagnostic", later.message))
                occurrences.append(
                    {
                        "job_id": failed_by_name[job_name].get("id"),
                        "job_name": job_name,
                        "member": info.filename,
                        "line": best.line,
                        "kind": best.kind,
                        "message": safe_message,
                        "normalized": normalized,
                        **(
                            {
                                "context": [
                                    {
                                        "member": info.filename,
                                        "line": item.line,
                                        "kind": item.kind,
                                        "message": _safe_cause(item.message),
                                    }
                                    for item in context[:3]
                                ]
                            }
                            if context
                            else {}
                        ),
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
