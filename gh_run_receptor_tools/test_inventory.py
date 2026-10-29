"""Audit the complete source assertion inventory with explicit repository input."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


def current_assertions(root: Path) -> dict:
    """Describe current functions without choosing their execution claims."""
    result = {}
    for path in sorted((root / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                key = path.relative_to(root).as_posix() + "::" + node.name
                assertions = []
                for statement in ast.walk(node):
                    if isinstance(statement, ast.Assert):
                        expression = ast.get_source_segment(text, statement)
                        assertions.append(
                            {
                                "line": statement.lineno,
                                "expression": expression,
                                "sha256": hashlib.sha256(expression.encode()).hexdigest(),
                            }
                        )
                result[key] = {
                    "current_assertions": assertions,
                    "parameterization": [
                        ast.get_source_segment(text, d) for d in node.decorator_list
                    ],
                }
    return result


def record_current(root: Path) -> None:
    """Record reviewed changes; never infer scopes or remove historical assertions."""
    path = root / "devtools/test_scopes.json"
    document = json.loads(path.read_text())
    current = current_assertions(root)
    if set(current) != set(document["entries"]):
        raise ValueError("Classify missing/stale functions explicitly before recording assertions")
    for key, snapshot in current.items():
        document["entries"][key].update(snapshot)
    path.write_text(json.dumps(document, indent=2) + "\n")


def audit(root: Path) -> dict:
    document = json.loads((root / "devtools/test_scopes.json").read_text())
    if document["schema"] != "gh-run-receptor.test-scopes@1":
        raise ValueError("Unsupported test scope inventory")
    expected = document["entries"]
    discovered = {}
    for path in sorted((root / "tests").glob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                key = path.relative_to(root).as_posix() + "::" + node.name
                discovered[key] = sum(isinstance(a, ast.Assert) for a in ast.walk(node))
    if set(discovered) != set(expected):
        raise ValueError("Test scope inventory has missing or stale functions")
    counts = dict.fromkeys(("product", "tooling", "integration"), 0)
    snapshots = current_assertions(root)
    for key, count in discovered.items():
        record = expected[key]
        if record["scope"] not in counts or not record["reason"]:
            raise ValueError(f"Test lacks a reviewed scope/rationale: {key}")
        if count < record["minimum_assertions"] or count < len(record["baseline_assertions"]):
            raise ValueError(f"A preserved test lost assertions: {key}")
        if snapshots[key]["current_assertions"] != record["current_assertions"] or (
            snapshots[key]["parameterization"] != record["parameterization"]
        ):
            raise ValueError(f"Review changed assertions/parameterization explicitly: {key}")
        counts[record["scope"]] += 1
    return {"state": "verified-inventory", "functions": len(discovered), "scopes": counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--record-current", action="store_true")
    args = parser.parse_args()
    if args.record_current:
        record_current(args.root.resolve())
    print(json.dumps(audit(args.root.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
