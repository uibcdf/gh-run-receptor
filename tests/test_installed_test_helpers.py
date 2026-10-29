"""Exercise original-source administrative binding in fresh isolated interpreters."""

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "devtools/scripts/installed_test_helpers.py"


@pytest.fixture
def producer(tmp_path):
    for name in ("devtools", "tests"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "original.py").write_text("answer = 42\n")
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            "Original helper fixture",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    return tmp_path, sha


@pytest.mark.parametrize(
    "mode",
    [
        "success",
        "body-error",
        "wrong-source",
        "untracked",
        "collision",
        "descendant-collision",
        "changed-bytes",
        "escaped-module",
        "changed-binding",
        "source-on-path",
    ],
)
def test_bound_helpers_preserve_original_paths_and_clean_only_owned_bindings(producer, mode):
    root, sha = producer
    script = f"""
import importlib,runpy,sys,types
from pathlib import Path
root=Path({str(root)!r});sha={sha!r};mode={mode!r}
binding=runpy.run_path({str(HELPER)!r})['bound_helpers']
sentinel=types.ModuleType('caller_marker');sys.modules['caller_marker']=sentinel
caller=None
if mode=='wrong-source':sha='0'*40
if mode=='untracked':(root/'devtools/untracked.py').write_text('secret = 1')
if mode in ['collision','descendant-collision']:
 key='devtools' if mode=='collision' else 'devtools.preexisting'
 caller=types.ModuleType(key);sys.modules[key]=caller
failed=False
try:
 with binding(root,sha) as receipt:
  module=importlib.import_module('devtools.original')
  assert module.answer==42 and Path(module.__file__)==root/'devtools/original.py'
  assert str(root) not in sys.path
  if mode=='body-error':raise RuntimeError('controlled interruption')
  if mode=='changed-bytes':(root/'devtools/original.py').write_text('answer = 99')
  if mode=='escaped-module':
   rogue=types.ModuleType('devtools.rogue');rogue.__file__=str(root/'outside.py');sys.modules[rogue.__name__]=rogue
  if mode=='changed-binding':sys.modules['devtools']=types.ModuleType('devtools')
  if mode=='source-on-path':sys.path.append(str(root))
except Exception:
 failed=True
assert failed==(mode!='success'),mode
if caller is not None:assert sys.modules[key] is caller
else:
 assert not any(n=='devtools' or n.startswith('devtools.') or
                n=='tests' or n.startswith('tests.') for n in sys.modules)
assert sys.modules['caller_marker'] is sentinel
if mode=='success':
 assert receipt['state']=='verified-helpers' and receipt['bindings_removed']
 assert receipt['checks']==2
print('verified')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script], cwd=root.parent, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "verified"


def test_recovery_workflow_keeps_original_artifact_and_separate_administrative_identity():
    path = ROOT / ".github/workflows/test-staged-conda.yml"
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    prepare = workflow["jobs"]["prepare"]
    assert prepare["name"] == "installed / prepare"
    assert "--qualification-sha" in json.dumps(prepare)
    job = workflow["jobs"]["installed"]
    assert job["name"] == "installed / ${{ matrix.platform }} · Python ${{ matrix.python }}"
    checkout_refs = [
        (s.get("with", {}).get("path"), s.get("with", {}).get("ref"))
        for s in job["steps"]
        if s.get("uses", "").startswith("actions/checkout@")
    ]
    assert ("component", "${{ inputs.candidate_sha }}") in checkout_refs
    assert ("qualification", "${{ github.sha }}") in checkout_refs
    setup = next(s for s in job["steps"] if "setup-miniconda@" in s.get("uses", ""))
    assert setup["with"]["run-init"] == setup["with"]["remove-profiles"] == "false"
    steps = {s.get("name"): s for s in job["steps"]}
    repair = steps["Repair Windows installer launcher metadata"]
    assert repair["if"] == "runner.os == 'Windows'"
    assert repair["env"]["CONDA_SAFETY_CHECKS"] == "enabled"
    assert "--name base --force-reinstall" in repair["run"]
    assert "conda-launchers" in repair["run"]
    assert "installed_test_helpers.py" in steps["Run installed tests"]["run"]
    assert " verify " in steps["Validate installed files"]["run"]
    assert " verify " in steps["Recheck installed provenance after scientific tests"]["run"]
    assert "--sha256" in steps["Install exact artifact"]["run"]
    assert "pip install" not in json.dumps(job) and "upload: true" not in json.dumps(job)


@pytest.mark.parametrize("operation", ["insert", "append", "extend", "slice", "item", "iadd"])
def test_legacy_source_path_addition_is_refused_without_hiding_other_admin_paths(
    tmp_path, operation
):
    guarded = runpy.run_path(str(HELPER))["InstalledPath"](["allowed"], tmp_path)
    value = str(tmp_path)
    if operation == "insert":
        guarded.insert(0, value)
    elif operation == "append":
        guarded.append(value)
    elif operation == "extend":
        guarded.extend([value, "sdk-helpers"])
    elif operation == "slice":
        guarded[:] = [value, "sdk-helpers"]
    elif operation == "item":
        guarded[0] = value
    else:
        guarded += [value, "sdk-helpers"]
    assert value not in guarded and guarded.blocked == 1
    assert "allowed" in guarded or "sdk-helpers" in guarded
