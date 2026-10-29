"""Receive shared portable support with the actual product and failure boundaries."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from gh_run_receptor_tools.check_distribution_inputs import checked_provider

ROOT = Path(__file__).resolve().parents[1]


def _provider():
    root = Path(os.environ.get("GH_RECEPTOR_SUITE_ROOT", ROOT / ".molsyssuite"))
    checked_provider(ROOT, root)
    return root


def test_original_generic_helper_import_fails_outside_the_source_tree(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-c", "from devtools.scripts.sanitize_bundle import sanitize"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" in result.stderr and "devtools" in result.stderr


@pytest.mark.parametrize(
    "mode",
    ["success", "missing", "tampered", "collision", "changed-stage", "abort", "cleanup-failure"],
)
def test_shared_support_receives_portable_inputs_and_visible_failures(tmp_path, mode):
    script = r"""
import hashlib,importlib,json,os,shutil,sys,types
from pathlib import Path
from unittest.mock import patch
from devtools.scripts import installed_test_support as support
root=Path(sys.argv[1]);mode=sys.argv[2];namespace='ghr76_receiving_probe'
file=root/'helper.py'
file.write_text('from gh_run_receptor.github import MINIMUM_GH_VERSION\n'
                'VALUE=MINIMUM_GH_VERSION\n')
declaration={'schema':support.SCHEMA,'namespace':namespace,'reason':'GHR portable receiving',
 'files':[{'source':'helper.py','target':namespace+'/helper.py','sha256':hashlib.sha256(file.read_bytes()).hexdigest()}]}
if mode=='missing':file.unlink()
if mode=='tampered':file.write_text('VALUE="changed"\n')
sentinel=None
if mode=='collision':
 sentinel=types.ModuleType(namespace);sys.modules[namespace]=sentinel
stage=None;failure=None;original_path=list(sys.path)
def fail_cleanup(*args,**kwargs):raise OSError('controlled cleanup failure')
context=(patch.object(support.TemporaryDirectory,'cleanup',fail_cleanup)
         if mode=='cleanup-failure' else __import__('contextlib').nullcontext())
try:
 with context:
  with support.staged_support(root,declaration,('gh_run_receptor',)) as stage:
   helper=importlib.import_module(namespace+'.helper')
   assert helper.VALUE==(2,48,0)
   assert Path(helper.__file__).is_relative_to(stage.root)
   assert not Path(helper.__file__).is_relative_to(root)
   if os.environ.get('GHR_EXPECT_INSTALLED')=='1':
    import gh_run_receptor
    assert Path(gh_run_receptor.__file__).resolve().is_relative_to(Path(sys.prefix))
   if mode=='changed-stage':(stage.root/namespace/'helper.py').write_text('VALUE=0')
   if mode=='abort':raise KeyboardInterrupt('controlled abort')
except (ValueError,OSError,KeyboardInterrupt) as error:failure=type(error).__name__
assert (failure is None)==(mode=='success'),(mode,failure)
assert sys.path==original_path
if sentinel is not None:assert sys.modules[namespace] is sentinel
else:assert not any(n==namespace or n.startswith(namespace+'.') for n in sys.modules)
if stage is not None:
 assert stage.receipt['imports_retired']
 if mode=='cleanup-failure':
  assert not stage.receipt['resources_retired']
  if stage.root.exists():shutil.rmtree(stage.root)
 assert not stage.root.exists()
print(json.dumps({'mode':mode,'failure':failure,
                  'resources_removed':stage is None or not stage.root.exists()}))
"""
    result = subprocess.run(
        [sys.executable, "-P", "-c", script, str(tmp_path), mode],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(_provider())),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["resources_removed"]
    assert (receipt["failure"] is None) == (mode == "success")


def test_shared_runner_rejects_a_src_checkout_before_collection(tmp_path):
    runtime = tmp_path / "src/gh_run_receptor"
    runtime.mkdir(parents=True)
    (runtime / "__init__.py").write_text('__version__ = "source-shadow"\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_unreachable.py").write_text(
        'raise AssertionError("collection reached")\n'
    )
    helper = tmp_path / "helper.py"
    helper.write_text('VALUE = "support"\n')
    import hashlib

    inventory = {
        "import_name": "gh_run_receptor",
        "required_paths": ["site-packages/gh_run_receptor/__init__.py"],
        "installed_tests": {
            "paths": ["tests"],
            "pytest_args": ["--receptor=llm"],
            "support": {
                "schema": "molsyssuite.installed-test-support@1",
                "namespace": "ghr76_shadow_probe",
                "reason": "Source substitution counterfactual",
                "files": [
                    {
                        "source": "helper.py",
                        "target": "ghr76_shadow_probe/helper.py",
                        "sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
                    }
                ],
            },
        },
    }
    command = (
        "import json,sys;from pathlib import Path;"
        "from devtools.scripts.installed_noarch import run_tests;"
        "run_tests(Path(sys.argv[1]),json.loads(sys.argv[2]))"
    )
    result = subprocess.run(
        [sys.executable, "-P", "-c", command, str(tmp_path), json.dumps(inventory)],
        cwd=tmp_path.parent,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join([str(_provider()), str(tmp_path / "src")])),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "runtime import is outside" in result.stderr
    assert "collection reached" not in result.stderr
