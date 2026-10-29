"""Apply the reviewed, exhaustive assertion-scope inventory without import paths."""

import json
from pathlib import Path

import pytest

from gh_run_receptor_tools.test_inventory import audit


def pytest_collection_modifyitems(items):
    root = Path(__file__).resolve().parents[1]
    inventory = json.loads((root / "devtools/test_scopes.json").read_text())
    try:
        audit(root)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error
    for item in items:
        function = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
        node = item.path.relative_to(root).as_posix() + "::" + function
        record = inventory["entries"].get(node)
        if record is None:
            raise pytest.UsageError(f"Unclassified test assertion scope: {node}")
        item.add_marker(getattr(pytest.mark, record["scope"]))
