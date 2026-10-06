"""Inspect GHR release archives without extracting or executing their payloads."""

from __future__ import annotations

import ast
import hashlib
import stat
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

from packaging.specifiers import SpecifierSet

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
MAX_MEMBERS = 2048


def _check_path(name: str, seen: set[str]) -> None:
    path = PurePosixPath(name)
    if (
        not name
        or len(name) > 512
        or "\\" in name
        or path.is_absolute()
        or ":" in name
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or name in seen
    ):
        raise ValueError(f"Unsafe or duplicate archive path: {name!r}")
    seen.add(name)


def _read_files(path: Path) -> dict[str, bytes]:
    """Bound compressed bytes, member count and decompressed payload before use."""
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive exceeds compressed size bound")
    files: dict[str, bytes] = {}
    seen: set[str] = set()
    total = 0

    def retain(name: str, size: int, stream) -> None:
        nonlocal total
        if size < 0 or size > MAX_MEMBER_BYTES or total + size > MAX_ARCHIVE_BYTES:
            raise ValueError("Archive exceeds decompressed size bound")
        raw = stream.read(MAX_MEMBER_BYTES + 1)
        if len(raw) != size:
            raise ValueError("Archive member size differs from its declared size")
        total += size
        files[name] = raw

    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_MEMBERS:
                raise ValueError("Archive exceeds member count bound")
            for member in members:
                name = member.filename.removesuffix("/")
                _check_path(name, seen)
                mode = stat.S_IFMT(member.external_attr >> 16)
                if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or member.flag_bits & 1:
                    raise ValueError("Archive contains a link, special or encrypted member")
                if member.is_dir():
                    continue
                with archive.open(member) as stream:
                    retain(name, member.file_size, stream)
    else:
        with tarfile.open(path, "r:gz") as archive:
            for count, member in enumerate(archive, 1):
                if count > MAX_MEMBERS:
                    raise ValueError("Archive exceeds member count bound")
                _check_path(member.name.removesuffix("/"), seen)
                if member.isdir():
                    continue
                if not member.isfile() or member.issparse():
                    raise ValueError("Archive contains a link, special or sparse member")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("Archive member has no readable payload")
                with stream:
                    retain(member.name, member.size, stream)
    return files


def _version(raw: bytes) -> str:
    """Read one literal generated version; never import archive Python code."""
    values = []
    for node in ast.parse(raw.decode("utf-8")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        ):
            if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                raise ValueError("Generated version must be a literal string")
            values.append(node.value.value)
    if len(values) != 1:
        raise ValueError("Generated version is absent or ambiguous")
    return values[0]


def inspect_distribution(path: Path, *, version: str, repo: Path) -> dict:
    """Validate one owner's wheel/sdist against its reviewed runtime inventory.

    ``version`` is the caller's independently established release identity. This
    does not establish source gates, installed compatibility or registry parity.
    """
    inventory = tomllib.loads((repo / "devtools/conda-build/resources.toml").read_text())
    project = tomllib.loads((repo / "pyproject.toml").read_text())["project"]
    files = _read_files(path)
    base = f"gh_run_receptor-{version}"
    if path.suffix == ".whl":
        if path.name != f"{base}-py3-none-any.whl":
            raise ValueError("Wheel filename differs from the expected release")
        metadata_path = f"{base}.dist-info/METADATA"
        if [name for name in files if name.endswith(".dist-info/METADATA")] != [metadata_path]:
            raise ValueError("Wheel must have exactly the expected distribution metadata")
        metadata_paths = [metadata_path]
        payload = files
    else:
        if path.name != f"{base}.tar.gz" or any(not name.startswith(f"{base}/") for name in files):
            raise ValueError("Source archive filename/root differs from the expected release")
        payload = {name.removeprefix(f"{base}/"): raw for name, raw in files.items()}
        metadata_paths = ["PKG-INFO", "gh_run_receptor.egg-info/PKG-INFO"]
        source_project = tomllib.loads(payload["pyproject.toml"].decode("utf-8"))["project"]
        for field in ("name", "requires-python", "dependencies"):
            if source_project.get(field) != project.get(field):
                raise ValueError(f"Source project {field} differs from the reviewed project")
    for name in metadata_paths:
        message = BytesParser().parsebytes(payload[name])
        for field, expected in (
            ("Name", project["name"]),
            ("Version", version),
            ("Requires-Python", project["requires-python"]),
        ):
            values = message.get_all(field, [])
            matches = values == [expected]
            if field == "Requires-Python" and len(values) == 1:
                matches = SpecifierSet(values[0]) == SpecifierSet(expected)
            if not matches:
                raise ValueError(f"Archive {name} {field} differs from the expected release")
    for required in inventory["required_paths"]:
        relative = required.removeprefix("site-packages/")
        if relative not in payload or not payload[relative]:
            raise ValueError(f"Missing or empty required runtime file: {relative}")
    generated = inventory["version_file"].removeprefix("site-packages/")
    if _version(payload[generated]) != version:
        raise ValueError("Archive generated version differs from the expected release")
    prefix = "gh_run_receptor/schemas/"
    hashes = inventory["schema_sha256"]
    schema_names = {name.removeprefix(prefix) for name in payload if name.startswith(prefix)}
    # The schemas package may also contain its Python initializer.
    if {name for name in schema_names if name.endswith(".json")} != set(hashes):
        raise ValueError("Archive schema resources differ from the frozen inventory")
    for name, expected in hashes.items():
        if hashlib.sha256(payload[prefix + name]).hexdigest() != expected:
            raise ValueError(f"Archive frozen schema differs: {name}")
    return {"file": path.name, "version": version, "schemas": len(hashes)}


def verify_distributions(directory: Path, *, version: str, repo: Path) -> list[str]:
    """Return bounded inspection violations for both mandatory release archives."""
    errors = []
    for name in (
        f"gh_run_receptor-{version}-py3-none-any.whl",
        f"gh_run_receptor-{version}.tar.gz",
    ):
        try:
            inspect_distribution(directory / name, version=version, repo=repo)
        except (
            OSError,
            ValueError,
            KeyError,
            SyntaxError,
            UnicodeError,
            EOFError,
            RuntimeError,
            tarfile.TarError,
            zipfile.BadZipFile,
        ) as exc:
            errors.append(f"{name}: {exc}")
    return errors
