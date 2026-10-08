"""Protect owned capture staging while preserving caller evidence (#63)."""

import subprocess
import sys
from pathlib import Path

import pytest

from gh_run_receptor import bundle, cli, github, service
from gh_run_receptor.errors import BundleError

RUN = {
    "id": 42,
    "run_attempt": 1,
    "status": "completed",
    "conclusion": "success",
    "head_sha": "abc",
    "workflow_id": 7,
}


class LifecycleClient:
    """Inject transport exits; capture writes and cleanup use the real filesystem."""

    hostname = "github.com"

    def __init__(self, error=None, stage="workflow"):
        self.error = error
        self.stage = stage

    def repository(self, value):
        return value

    def json(self, endpoint, *, paginate=False):
        if endpoint.endswith("/actions/runs/42"):
            return RUN.copy()
        if endpoint.endswith("/actions/workflows/7"):
            if self.error is not None and self.stage == "workflow":
                raise self.error
            return {"path": ".github/workflows/ci.yaml"}
        if "/jobs?" in endpoint:
            return {"total_count": 0, "jobs": []}
        if "/artifacts?" in endpoint:
            return {"total_count": 0, "artifacts": []}
        if endpoint == "/repos/uibcdf/example":
            return {"default_branch": "main"}
        raise AssertionError(endpoint)

    def optional_json(self, endpoint):
        return None

    def download(self, endpoint, destination, **kwargs):
        destination.write_bytes(b"partial owned download")
        assert self.error is not None and self.stage == "download"
        raise self.error


@pytest.fixture
def caller_files(tmp_path):
    receipt = tmp_path / "caller-receipt.json"
    receipt.write_bytes(b"caller-owned evidence\n")
    return tmp_path, receipt


def capture(parent, client):
    return bundle.capture_bundle(
        client,
        "uibcdf/example",
        42,
        attempt=1,
        policy="full" if client.stage == "download" else "metadata",
        destination=parent / "bundle",
        run=RUN.copy(),
    )


def assert_only_receipt(parent, receipt):
    assert receipt.read_bytes() == b"caller-owned evidence\n"
    assert set(parent.iterdir()) == {receipt}


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("stage", ["workflow", "download"])
def test_aborted_capture_removes_only_owned_staging(caller_files, error_type, stage):
    parent, receipt = caller_files
    error = error_type("controlled exit")

    with pytest.raises(error_type) as caught:
        capture(parent, LifecycleClient(error, stage))

    assert caught.value is error
    assert_only_receipt(parent, receipt)


def test_permission_failure_removes_allocated_staging(caller_files, monkeypatch):
    parent, receipt = caller_files
    error = PermissionError("controlled chmod failure")

    def fail_permissions(path, mode):
        assert Path(path).parent == parent and mode == 0o700
        raise error

    monkeypatch.setattr(bundle.os, "chmod", fail_permissions)
    with pytest.raises(PermissionError) as caught:
        capture(parent, LifecycleClient())

    assert caught.value is error
    assert_only_receipt(parent, receipt)


def test_cli_interrupt_keeps_exit_130_and_cleans_staging(caller_files, monkeypatch, capsys):
    parent, receipt = caller_files
    client = LifecycleClient(KeyboardInterrupt("controlled exit"))
    monkeypatch.setattr(cli, "GitHubClient", lambda hostname: client)

    result = cli.main(
        [
            "--repo",
            "uibcdf/example",
            "--cache-dir",
            str(parent / "cache"),
            "capture",
            "42",
            "--capture",
            "metadata",
            "--output",
            str(parent / "bundle"),
        ]
    )

    assert result == 130
    output = capsys.readouterr()
    assert output.err == "operation interrupted\n" and not output.out
    assert_only_receipt(parent, receipt)


def test_cleanup_failure_remains_visible_with_interruption_context(caller_files, monkeypatch):
    parent, receipt = caller_files
    interruption = KeyboardInterrupt("controlled exit")
    original_unlink = Path.unlink

    def fail_owned_removal(path, *args, **kwargs):
        if path.parent.name.startswith(".bundle-"):
            raise PermissionError("controlled cleanup failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_owned_removal)
    with pytest.raises(BaseException) as caught:
        capture(parent, LifecycleClient(interruption))

    assert isinstance(caught.value, PermissionError)
    assert str(caught.value) == "controlled cleanup failure"
    assert caught.value.__context__ is interruption
    assert receipt.read_bytes() == b"caller-owned evidence\n"
    assert not (parent / "bundle").exists()


def test_ordinary_capture_error_still_cleans(caller_files):
    parent, receipt = caller_files
    error = OSError("controlled transport failure")

    with pytest.raises(OSError) as caught:
        capture(parent, LifecycleClient(error))

    assert caught.value is error
    assert_only_receipt(parent, receipt)


def test_success_keeps_replayable_destination_and_caller_receipt(caller_files):
    parent, receipt = caller_files

    manifest = capture(parent, LifecycleClient())
    retained, evidence = bundle.load_bundle(parent / "bundle")

    assert retained == manifest and manifest["complete"] is True
    assert evidence["run.json"] == RUN
    assert set(parent.iterdir()) == {receipt, parent / "bundle"}
    assert receipt.read_bytes() == b"caller-owned evidence\n"


def test_existing_destination_is_preserved_after_collision(caller_files):
    parent, receipt = caller_files
    destination = parent / "bundle"
    destination.mkdir()
    prior = destination / "prior.json"
    prior.write_bytes(b"previous caller evidence\n")

    with pytest.raises(BundleError, match="bundle already exists"):
        capture(parent, LifecycleClient())

    assert set(parent.iterdir()) == {receipt, destination}
    assert prior.read_bytes() == b"previous caller evidence\n"
    assert receipt.read_bytes() == b"caller-owned evidence\n"


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_interrupted_refresh_restores_previous_bundle(caller_files, monkeypatch, error_type):
    parent, receipt = caller_files
    destination = parent / "bundle"
    active = {**RUN, "status": "in_progress", "conclusion": None}
    bundle.capture_bundle(
        LifecycleClient(),
        "uibcdf/example",
        42,
        attempt=1,
        policy="metadata",
        destination=destination,
        run=active,
    )
    original_bytes = {p.name: p.read_bytes() for p in destination.iterdir()}
    original_rename = Path.rename
    interruption = error_type("controlled refresh interruption")

    def interrupt_replacement(path, target):
        if path.name.startswith(".bundle.refresh-") and target == destination:
            raise interruption
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", interrupt_replacement)
    with pytest.raises(error_type) as caught:
        service.acquire_evidence(
            LifecycleClient(),
            "uibcdf/example",
            42,
            attempt=1,
            policy="metadata",
            cache_root=parent / "cache",
            output=destination,
        )

    assert caught.value is interruption
    assert destination.is_dir()
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == original_bytes
    assert bundle.load_bundle(destination)[1]["run.json"] == active
    assert set(parent.iterdir()) == {receipt, destination}
    assert receipt.read_bytes() == b"caller-owned evidence\n"


@pytest.fixture
def transport_child(monkeypatch):
    """Run a real child with controlled pipe failure, never a network request."""
    original_popen = subprocess.Popen
    children = []
    pipes = []

    def install(error):
        class FaultReader:
            def __init__(self, stream):
                self.stream = stream
                self.reads = 0

            def read(self, size):
                self.reads += 1
                if error is not None and self.reads > 1:
                    raise error
                return self.stream.read(1)

            def close(self):
                self.stream.close()

        def spawn(command, *, stdout, stderr):
            assert command[0] == "gh" and stdout == subprocess.PIPE
            program = "import sys,time; sys.stdout.buffer.write(b'{}'); sys.stdout.flush()"
            if error is not None:
                program += "; time.sleep(60)"
            child = original_popen([sys.executable, "-c", program], stdout=stdout, stderr=stderr)
            children.append(child)
            pipes.append(child.stdout)
            child.stdout = FaultReader(child.stdout)
            return child

        monkeypatch.setattr(github.subprocess, "Popen", spawn)

    yield install, children, pipes
    # Failing-before runs must not themselves orphan children or retain pipes.
    for child in children:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)
        child.stdout.close()


@pytest.mark.parametrize("operation", ["json", "download"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, OSError])
def test_transport_abort_reaps_child_and_discards_partial_bytes(
    caller_files, transport_child, operation, error_type
):
    parent, receipt = caller_files
    install, children, pipes = transport_child
    error = error_type("controlled pipe failure")
    install(error)
    client = github.GitHubClient()
    client._cli_version_checked = True
    expected = github.AcquisitionError if error_type is OSError else error_type

    with pytest.raises(expected):
        if operation == "json":
            client._run(["api", "/controlled"], check_cli=False)
        else:
            client.download("/controlled", parent / "download")

    assert len(children) == 1 and children[0].poll() is not None
    assert pipes[0].closed
    assert_only_receipt(parent, receipt)


@pytest.mark.parametrize("operation", ["json", "download"])
def test_transport_success_closes_pipe_and_keeps_requested_output(
    caller_files, transport_child, operation
):
    parent, receipt = caller_files
    install, children, pipes = transport_child
    install(None)
    client = github.GitHubClient()
    client._cli_version_checked = True

    if operation == "json":
        assert client._run(["api", "/controlled"], check_cli=False) == "{}"
        assert_only_receipt(parent, receipt)
    else:
        client.download("/controlled", parent / "download")
        assert (parent / "download").read_bytes() == b"{}"
        assert set(parent.iterdir()) == {receipt, parent / "download"}

    assert len(children) == 1 and children[0].poll() == 0
    assert pipes[0].closed
    assert receipt.read_bytes() == b"caller-owned evidence\n"
