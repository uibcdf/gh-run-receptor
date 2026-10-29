"""Loading and evaluating explicit comparison regression policies."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from gh_run_receptor.contracts import require_contract, schema_id
from gh_run_receptor.errors import ContractError, PolicyError

POLICY_SCHEMA = schema_id("comparison-policy", 1)
MAX_POLICY_BYTES = 64 * 1024
BOOLEAN_RULES = {
    "same_repository",
    "same_workflow",
    "same_head_sha",
    "forbid_job_removals",
    "forbid_artifact_removals",
    "forbid_matrix_removals",
    "forbid_matrix_changes",
}
QUANTITY_RULES = {
    "max_job_duration_increase_seconds",
    "max_job_duration_increase_percent",
    "max_artifact_size_increase_bytes",
}
RULES = BOOLEAN_RULES | QUANTITY_RULES | {"candidate_conclusion"}
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")


def _strict_json(data: bytes, path: Path) -> Any:
    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise PolicyError(f"duplicate policy key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise PolicyError(f"non-finite policy number: {value}")

    try:
        return json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=object_without_duplicates,
            parse_constant=reject_constant,
        )
    except UnicodeDecodeError as error:
        raise PolicyError(f"comparison policy is not valid UTF-8: {path}") from error
    except json.JSONDecodeError as error:
        raise PolicyError(f"comparison policy is not valid JSON: {path}: {error.msg}") from error


def validate_policy(value: Any) -> dict[str, Any]:
    """Validating and returning one comparison policy document."""
    try:
        require_contract(value, "comparison-policy")
    except ContractError as error:
        raise PolicyError(str(error)) from error
    if set(value) != {"schema", "rules"} or not isinstance(value["rules"], dict):
        raise PolicyError("comparison policy requires exactly schema and rules objects")
    rules = value["rules"]
    if not rules:
        raise PolicyError("comparison policy requires at least one rule")
    unknown = sorted(set(rules) - RULES)
    if unknown:
        raise PolicyError(f"unsupported comparison policy rules: {', '.join(unknown)}")
    for name in BOOLEAN_RULES & set(rules):
        if rules[name] is not True:
            raise PolicyError(f"comparison policy rule {name!r} must be true when present")
    for name in QUANTITY_RULES & set(rules):
        number = rules[name]
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise PolicyError(f"comparison policy rule {name!r} must be a number")
        if not math.isfinite(number) or number < 0:
            raise PolicyError(f"comparison policy rule {name!r} must be finite and nonnegative")
        if name != "max_job_duration_increase_percent" and not isinstance(number, int):
            raise PolicyError(f"comparison policy rule {name!r} must be an integer")
    conclusion = rules.get("candidate_conclusion")
    if conclusion is not None and (
        not isinstance(conclusion, str)
        or not conclusion
        or len(conclusion) > 50
        or _IDENTIFIER.fullmatch(conclusion) is None
    ):
        raise PolicyError("candidate_conclusion must be a short alphanumeric identifier")
    return value


def load_policy(path: Path) -> dict[str, Any]:
    """Loading a bounded strict JSON comparison policy from a regular file."""
    try:
        if path.is_symlink() or not path.is_file():
            raise PolicyError(f"comparison policy must be a regular non-symlink file: {path}")
        size = path.stat().st_size
        if size > MAX_POLICY_BYTES:
            raise PolicyError(f"comparison policy exceeds the {MAX_POLICY_BYTES}-byte limit")
        data = path.read_bytes()
    except PolicyError:
        raise
    except OSError as error:
        raise PolicyError(f"cannot read comparison policy: {path}: {error}") from error
    return validate_policy(_strict_json(data, path))


def _entry(rule: str, expected: Any, observed: Any) -> dict[str, Any]:
    return {"rule": rule, "expected": expected, "observed": observed}


def evaluate_policy(comparison: dict[str, Any], policy: dict[str, Any] | None) -> dict[str, Any]:
    """Evaluating explicit policy rules against one descriptive comparison."""
    if policy is None:
        return {
            "evaluated": False,
            "assessment": "NOT_EVALUATED",
            "violations": [],
            "unknowns": [],
        }
    validate_policy(policy)
    rules = policy["rules"]
    violations = []
    unknowns = []
    relation = comparison["relation"]
    left = comparison["left"]
    right = comparison["right"]

    identities = {
        "same_repository": (left["repository"], right["repository"]),
        "same_workflow": (left["workflow"], right["workflow"]),
        "same_head_sha": (left["head_sha"], right["head_sha"]),
    }
    for rule in ("same_repository", "same_workflow", "same_head_sha"):
        if rule not in rules:
            continue
        observed = identities[rule]
        if any(value is None for value in observed):
            unknowns.append(_entry(rule, True, None))
        elif not relation[rule]:
            violations.append(_entry(rule, True, list(observed)))

    if "candidate_conclusion" in rules:
        observed = right["conclusion"]
        expected = rules["candidate_conclusion"]
        if observed is None:
            unknowns.append(_entry("candidate_conclusion", expected, None))
        elif observed != expected:
            violations.append(_entry("candidate_conclusion", expected, observed))

    quantities = {
        "max_job_duration_increase_seconds": comparison["jobs"]["duration_seconds"],
        "max_artifact_size_increase_bytes": comparison["artifacts"]["size_bytes"],
    }
    for rule, change in quantities.items():
        if rule not in rules:
            continue
        delta = change["delta"]
        if delta is None:
            unknowns.append(_entry(rule, rules[rule], None))
        elif delta > rules[rule]:
            violations.append(_entry(rule, rules[rule], delta))

    percent_rule = "max_job_duration_increase_percent"
    if percent_rule in rules:
        change = comparison["jobs"]["duration_seconds"]
        baseline = change["left"]["total"]
        delta = change["delta"]
        if delta is None or (baseline == 0 and delta > 0):
            unknowns.append(_entry(percent_rule, rules[percent_rule], None))
        else:
            observed = 0.0 if baseline == 0 else (delta / baseline) * 100
            if observed > rules[percent_rule]:
                violations.append(_entry(percent_rule, rules[percent_rule], observed))

    collections = {
        "forbid_job_removals": comparison["jobs"]["inventory"]["removed"],
        "forbid_artifact_removals": comparison["artifacts"]["removed"],
    }
    for rule, removed in collections.items():
        if rule in rules and removed:
            violations.append(_entry(rule, [], removed))

    matrix_rules = {"forbid_matrix_removals", "forbid_matrix_changes"} & set(rules)
    if matrix_rules and not comparison["matrix"]["comparable"]:
        for rule in sorted(matrix_rules):
            unknowns.append(_entry(rule, [], None))
    else:
        if "forbid_matrix_removals" in rules and comparison["matrix"]["removed"]:
            violations.append(_entry("forbid_matrix_removals", [], comparison["matrix"]["removed"]))
        if "forbid_matrix_changes" in rules and comparison["matrix"]["changes"]:
            violations.append(_entry("forbid_matrix_changes", [], comparison["matrix"]["changes"]))

    assessment = "INCOMPLETE" if unknowns else ("FAIL" if violations else "PASS")
    return {
        "evaluated": True,
        "assessment": assessment,
        "violations": violations,
        "unknowns": unknowns,
    }
