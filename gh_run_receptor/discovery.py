"""Discovering local GitHub workflows and proposing bounded configuration."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from gh_run_receptor.config import CONFIG_PATH, MAX_CONFIG_BYTES, parse_config
from gh_run_receptor.errors import ConfigError

MAX_DISCOVERED_WORKFLOWS = 128
MAX_WORKFLOW_BYTES = 1024 * 1024
MAX_TOTAL_WORKFLOW_BYTES = 8 * 1024 * 1024
_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./ ()+-]+$")
_WORD = re.compile(r"[a-z0-9]+")

_FILENAME_SIGNALS = {
    "conda": {"conda", "rattler", "anaconda"},
    "docs": {"docs", "documentation", "sphinx", "notebook", "notebooks", "pages"},
    "release": {"publish", "release", "zenodo"},
    "ci": {"benchmark", "benchmarks", "ci", "coverage", "lint", "ruff", "test", "tests"},
}
_CONTENT_SIGNALS = {
    "conda": (
        "conda build",
        "conda-build",
        "rattler build",
        "rattler-build",
        "anaconda upload",
        "anaconda.org",
    ),
    "docs": (
        "sphinx",
        "jupyter-book",
        "mkdocs",
        "deploy-pages",
        "upload-pages-artifact",
        "gh-pages",
    ),
    "release": (
        "npm publish",
        "gh-action-pypi-publish",
        "action-gh-release",
        "zenodo",
    ),
    "ci": (
        "pytest",
        "ruff check",
        "playwright",
        "codecov",
        "coverage run",
    ),
}


@dataclass(frozen=True)
class DiscoveredWorkflow:
    """Describing one local workflow and its conservative profile suggestion."""

    path: str
    profile: str
    confidence: str
    reasons: tuple[str, ...]
    settings: tuple[tuple[str, str], ...] = ()


def _words(value: str) -> set[str]:
    return set(_WORD.findall(value.lower()))


def _source_text(data: bytes, path: Path) -> str:
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ConfigError(f"workflow is not valid UTF-8: {path}") from error


def _classify(relative_path: str, source: str) -> DiscoveredWorkflow:
    filename_words = _words(Path(relative_path).stem)
    filename_matches = {
        profile: sorted(filename_words & signals)
        for profile, signals in _FILENAME_SIGNALS.items()
    }
    content = "\n".join(
        line.strip().lower()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    content_matches = {
        profile: [signal for signal in signals if signal in content]
        for profile, signals in _CONTENT_SIGNALS.items()
    }

    specialized = []
    for profile in ("conda", "docs", "release"):
        if filename_matches[profile] or content_matches[profile]:
            specialized.append(profile)

    if len(specialized) > 1:
        reasons = tuple(f"ambiguous:{profile}" for profile in specialized)
        return DiscoveredWorkflow(relative_path, "generic", "low", reasons)
    if specialized:
        profile = specialized[0]
        filename_evidence = filename_matches[profile]
        evidence = filename_evidence or content_matches[profile]
        source_kind = "filename" if filename_evidence else "content"
        confidence = "high" if filename_evidence else "medium"
        settings: tuple[tuple[str, str], ...] = ()
        if profile == "conda" and (
            "noarch" in filename_words
            or "noarch package" in content
            or "noarch: python" in content
        ):
            settings = (("package_kind", "noarch"),)
        return DiscoveredWorkflow(
            relative_path,
            profile,
            confidence,
            tuple(f"{source_kind}:{item}" for item in evidence),
            settings,
        )

    ci_evidence = filename_matches["ci"] or content_matches["ci"]
    if ci_evidence:
        source_kind = "filename" if filename_matches["ci"] else "content"
        confidence = "high" if filename_matches["ci"] else "medium"
        return DiscoveredWorkflow(
            relative_path,
            "ci",
            confidence,
            tuple(f"{source_kind}:{item}" for item in ci_evidence),
        )
    return DiscoveredWorkflow(relative_path, "generic", "low", ("no-profile-signal",))


def discover_workflows(root: Path) -> list[DiscoveredWorkflow]:
    """Discovering immediate workflow files below a local repository root."""
    workflow_directory = root / ".github" / "workflows"
    if (root / ".github").is_symlink() or workflow_directory.is_symlink():
        raise ConfigError("workflow discovery directories must not be symlinks")
    try:
        candidates = []
        for path in workflow_directory.iterdir():
            if path.suffix.lower() not in {".yml", ".yaml"}:
                continue
            candidates.append(path)
            if len(candidates) > MAX_DISCOVERED_WORKFLOWS:
                raise ConfigError(
                    f"workflow count exceeds the {MAX_DISCOVERED_WORKFLOWS}-file "
                    "discovery limit"
                )
    except OSError as error:
        raise ConfigError(f"cannot read workflow directory: {workflow_directory}") from error
    candidates.sort(key=lambda path: path.name)
    if not candidates:
        raise ConfigError(f"no workflow files found in {workflow_directory}")

    discovered = []
    total_bytes = 0
    for path in candidates:
        relative_path = path.relative_to(root).as_posix()
        if _SAFE_PATH.fullmatch(relative_path) is None:
            raise ConfigError(f"workflow path cannot be represented safely: {path.name!r}")
        if path.is_symlink() or not path.is_file():
            raise ConfigError(f"workflow must be a regular non-symlink file: {path}")
        try:
            with path.open("rb") as stream:
                data = stream.read(MAX_WORKFLOW_BYTES + 1)
        except OSError as error:
            raise ConfigError(f"cannot read workflow: {path}") from error
        if len(data) > MAX_WORKFLOW_BYTES:
            raise ConfigError(
                f"workflow exceeds the {MAX_WORKFLOW_BYTES}-byte discovery limit: {path}"
            )
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_WORKFLOW_BYTES:
            raise ConfigError(
                "workflow sources exceed the "
                f"{MAX_TOTAL_WORKFLOW_BYTES}-byte total discovery limit"
            )
        discovered.append(_classify(relative_path, _source_text(data, path)))
    return discovered


def render_config(workflows: list[DiscoveredWorkflow]) -> bytes:
    """Rendering a deterministic strict version 1 configuration proposal."""
    lines = ["schema_version: 1", "workflows:"]
    for workflow in workflows:
        lines.extend(
            [
                "  - match:",
                f"      path: {workflow.path}",
                f"    profile: {workflow.profile}",
            ]
        )
        if workflow.settings:
            lines.append("    settings:")
            lines.extend(f"      {key}: {value}" for key, value in workflow.settings)
    data = ("\n".join(lines) + "\n").encode("utf-8")
    if len(data) > MAX_CONFIG_BYTES:
        raise ConfigError(f"generated configuration exceeds the {MAX_CONFIG_BYTES}-byte limit")
    parse_config(data)
    return data


def write_config(root: Path, data: bytes) -> Path:
    """Publishing a generated configuration atomically without replacing a target."""
    target = root / CONFIG_PATH
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".gh-run-receptor.", dir=target.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        os.link(temporary, target)
    except FileExistsError as error:
        raise ConfigError(f"configuration already exists: {target}") from error
    except OSError as error:
        raise ConfigError(f"cannot write configuration: {target}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
