"""Comparing normalized workflow reports without merging their evidence."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from gh_run_receptor.contracts import schema_id

COMPARISON_SCHEMA = schema_id("comparison", 1)
MAX_LIST_ITEMS = 10
MAX_TEXT_VALUE = 240
REQUIRED_DIMENSIONS = ("metadata", "jobs", "artifact_inventory")


def _identity(report: dict[str, Any]) -> dict[str, Any]:
    subject = report["subject"]
    return {
        "repository": subject["repository"],
        "workflow": subject.get("workflow"),
        "run_id": subject["run_id"],
        "run_attempt": subject["run_attempt"],
        "head_sha": subject.get("head_sha"),
        "url": subject.get("url"),
        "profile": report["receptor"]["profile"],
        "status": report["github"].get("status"),
        "conclusion": report["github"].get("conclusion"),
        "assessment": report["receptor"]["assessment"],
        "completeness": {key: report["completeness"].get(key) for key in REQUIRED_DIMENSIONS},
    }


def _delta(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {
        key: right.get(key, 0) - left.get(key, 0)
        for key in sorted(set(left) | set(right))
        if right.get(key, 0) != left.get(key, 0)
    }


def _named_counts(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get(field) or "(unnamed)") for item in items).items()))


def _state_by_name(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = {}
    for item in items:
        name = str(item.get("name") or "(unnamed)")
        state = str(item.get("conclusion") or item.get("status") or "unknown")
        grouped.setdefault(name, Counter())[state] += 1
    return {name: dict(sorted(counts.items())) for name, counts in sorted(grouped.items())}


def _inventory_changes(
    left: dict[str, int], right: dict[str, int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    added = []
    removed = []
    for name in sorted(set(left) | set(right)):
        change = right.get(name, 0) - left.get(name, 0)
        if change > 0:
            added.append({"name": name, "count": change})
        elif change < 0:
            removed.append({"name": name, "count": -change})
    return added, removed


def _known_total(items: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [item.get(field) for item in items]
    known = [value for value in values if isinstance(value, int) and not isinstance(value, bool)]
    return {
        "known_items": len(known),
        "total_items": len(items),
        "complete": len(known) == len(items),
        "total": sum(known),
    }


def _quantity_change(
    left_items: list[dict[str, Any]], right_items: list[dict[str, Any]], field: str
) -> dict[str, Any]:
    left = _known_total(left_items, field)
    right = _known_total(right_items, field)
    return {
        "left": left,
        "right": right,
        "delta": right["total"] - left["total"] if left["complete"] and right["complete"] else None,
    }


def _job_changes(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_jobs = left["jobs"]
    right_jobs = right["jobs"]
    left_names = _named_counts(left_jobs, "name")
    right_names = _named_counts(right_jobs, "name")
    added, removed = _inventory_changes(left_names, right_names)
    left_states = _state_by_name(left_jobs)
    right_states = _state_by_name(right_jobs)
    state_changes = [
        {"name": name, "left": left_states.get(name, {}), "right": right_states.get(name, {})}
        for name in sorted(set(left_states) | set(right_states))
        if left_states.get(name, {}) != right_states.get(name, {})
    ]
    return {
        "counts": {
            "left": left["job_counts"],
            "right": right["job_counts"],
            "delta": _delta(left["job_counts"], right["job_counts"]),
        },
        "inventory": {
            "left_total": len(left_jobs),
            "right_total": len(right_jobs),
            "added": added,
            "removed": removed,
        },
        "state_changes": state_changes,
        "duration_seconds": _quantity_change(left_jobs, right_jobs, "duration_seconds"),
    }


def _artifact_changes(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_artifacts = left["artifacts"]
    right_artifacts = right["artifacts"]
    left_names = _named_counts(left_artifacts, "name")
    right_names = _named_counts(right_artifacts, "name")
    added, removed = _inventory_changes(left_names, right_names)
    return {
        "interpretation": "inventory_at_capture",
        "left_total": len(left_artifacts),
        "right_total": len(right_artifacts),
        "added": added,
        "removed": removed,
        "size_bytes": _quantity_change(left_artifacts, right_artifacts, "size_bytes"),
    }


def _matrix_units(matrix: dict[str, Any]) -> tuple[str | None, dict[str, dict[str, Any]]]:
    kind = matrix.get("kind")
    if kind == "conda":
        return "platform", {
            str(item.get("name") or "(unnamed)"): {"status": item.get("status")}
            for item in matrix.get("platforms", [])
        }
    if kind == "ci":
        return "role", {
            str(item.get("name") or "(unnamed)"): {"evidence_count": len(item.get("job_ids", []))}
            for item in matrix.get("roles", [])
        }
    if kind in {"docs", "release"}:
        return "phase", {
            str(item.get("name") or "(unnamed)"): {
                "evidence_count": len(item.get("evidence", [])),
                "counts": item.get("counts", {}),
            }
            for item in matrix.get("phases", [])
        }
    return None, {}


def _matrix_changes(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_kind = left["matrix"].get("kind")
    right_kind = right["matrix"].get("kind")
    left_dimension, left_units = _matrix_units(left["matrix"])
    right_dimension, right_units = _matrix_units(right["matrix"])
    comparable = (
        left_kind == right_kind and left_dimension == right_dimension and left_dimension is not None
    )
    if not comparable:
        return {
            "left_kind": left_kind,
            "right_kind": right_kind,
            "comparable": False,
            "dimension": None,
            "added": [],
            "removed": [],
            "changes": [],
        }
    left_names = set(left_units)
    right_names = set(right_units)
    return {
        "left_kind": left_kind,
        "right_kind": right_kind,
        "comparable": True,
        "dimension": left_dimension,
        "added": sorted(right_names - left_names),
        "removed": sorted(left_names - right_names),
        "changes": [
            {"name": name, "left": left_units[name], "right": right_units[name]}
            for name in sorted(left_names & right_names)
            if left_units[name] != right_units[name]
        ],
    }


def _side_sufficient(report: dict[str, Any]) -> bool:
    return bool(report["receptor"].get("evidence_sufficient")) and all(
        report["completeness"].get(key) == "complete" for key in REQUIRED_DIMENSIONS
    )


def compare_reports(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Building a truth-preserving comparison from two normalized reports."""
    left_identity = _identity(left)
    right_identity = _identity(right)
    relation = {
        "same_repository": left_identity["repository"] == right_identity["repository"],
        "same_workflow": left_identity["workflow"] == right_identity["workflow"],
        "same_run": left_identity["run_id"] == right_identity["run_id"]
        and left_identity["repository"] == right_identity["repository"],
        "same_head_sha": left_identity["head_sha"] is not None
        and left_identity["head_sha"] == right_identity["head_sha"],
    }
    jobs = _job_changes(left, right)
    artifacts = _artifact_changes(left, right)
    matrix = _matrix_changes(left, right)
    transition = {
        "status_changed": left_identity["status"] != right_identity["status"],
        "conclusion_changed": left_identity["conclusion"] != right_identity["conclusion"],
        "assessment_changed": left_identity["assessment"] != right_identity["assessment"],
    }
    sufficient = _side_sufficient(left) and _side_sufficient(right)
    changed = any(transition.values()) or any(
        (
            jobs["counts"]["delta"],
            jobs["inventory"]["added"],
            jobs["inventory"]["removed"],
            jobs["state_changes"],
            jobs["duration_seconds"]["delta"] not in (None, 0),
            artifacts["added"],
            artifacts["removed"],
            artifacts["size_bytes"]["delta"] not in (None, 0),
            matrix["added"],
            matrix["removed"],
            matrix["changes"],
        )
    )
    warnings = []
    if not relation["same_head_sha"]:
        warnings.append("source commits differ or a commit identity is unavailable")
    if not relation["same_workflow"]:
        warnings.append("workflow identities differ")
    if not sufficient:
        warnings.append("required metadata, jobs, or artifact inventory evidence is incomplete")
    return {
        "schema": COMPARISON_SCHEMA,
        "assessment": "INCOMPLETE" if not sufficient else ("CHANGED" if changed else "UNCHANGED"),
        "evidence_sufficient": sufficient,
        "left": left_identity,
        "right": right_identity,
        "relation": relation,
        "transition": transition,
        "jobs": jobs,
        "artifacts": artifacts,
        "matrix": matrix,
        "warnings": warnings,
    }


def render_json(comparison: dict[str, Any]) -> str:
    """Rendering deterministic comparison JSON."""
    return json.dumps(comparison, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _safe(value: Any) -> str:
    text = " ".join(str(value).split())
    return text[:MAX_TEXT_VALUE] + ("..." if len(text) > MAX_TEXT_VALUE else "")


def _items(values: list[Any], *, key: str | None = None) -> str:
    selected = values[:MAX_LIST_ITEMS]
    rendered = ",".join(_safe(item[key] if key else item) for item in selected)
    if len(values) > MAX_LIST_ITEMS:
        rendered += f",...+{len(values) - MAX_LIST_ITEMS}"
    return rendered or "none"


def _duration_text(change: dict[str, Any]) -> str:
    delta = change["delta"]
    left = change["left"]
    right = change["right"]
    suffix = f" delta={delta:+d}s" if delta is not None else " delta=?"
    left_text = f"{left['total']}s({left['known_items']}/{left['total_items']})"
    right_text = f"{right['total']}s({right['known_items']}/{right['total_items']})"
    return f"{left_text}->{right_text}{suffix}"


def render_llm(comparison: dict[str, Any]) -> str:
    """Rendering a bounded comparison for language-model consumption."""
    left = comparison["left"]
    right = comparison["right"]
    relation = comparison["relation"]
    jobs = comparison["jobs"]
    artifacts = comparison["artifacts"]
    count_delta = json.dumps(jobs["counts"]["delta"], sort_keys=True, separators=(",", ":"))
    jobs_added = _items(jobs["inventory"]["added"], key="name")
    jobs_removed = _items(jobs["inventory"]["removed"], key="name")
    artifacts_added = _items(artifacts["added"], key="name")
    artifacts_removed = _items(artifacts["removed"], key="name")
    lines = [
        f"{comparison['assessment']} compare {_safe(left['repository'])} "
        f"run={left['run_id']} attempt={left['run_attempt']} -> "
        f"{_safe(right['repository'])} run={right['run_id']} "
        f"attempt={right['run_attempt']}",
        f"identity same_run={str(relation['same_run']).lower()} "
        f"same_commit={str(relation['same_head_sha']).lower()} "
        f"sha={_safe(left['head_sha'])}->{_safe(right['head_sha'])}",
        f"result status={_safe(left['status'])}->{_safe(right['status'])} "
        f"conclusion={_safe(left['conclusion'])}->{_safe(right['conclusion'])} "
        f"receptor={_safe(left['assessment'])}->{_safe(right['assessment'])}",
        f"jobs counts={count_delta} state_changes={len(jobs['state_changes'])} "
        f"added={jobs_added} removed={jobs_removed}",
        f"duration {_duration_text(jobs['duration_seconds'])}",
        f"artifacts observation=inventory_at_capture "
        f"count={artifacts['left_total']}->{artifacts['right_total']} "
        f"added={artifacts_added} removed={artifacts_removed}",
    ]
    matrix = comparison["matrix"]
    if matrix["comparable"]:
        lines.append(
            f"matrix kind={_safe(matrix['left_kind'])} dimension={matrix['dimension']} "
            f"added={_items(matrix['added'])} removed={_items(matrix['removed'])} "
            f"changes={len(matrix['changes'])}"
        )
    else:
        lines.append(
            f"matrix comparable=false "
            f"kind={_safe(matrix['left_kind'])}->{_safe(matrix['right_kind'])}"
        )
    lines.extend(f"warning: {_safe(item)}" for item in comparison["warnings"][:MAX_LIST_ITEMS])
    return "\n".join(lines) + "\n"


def render_human(comparison: dict[str, Any]) -> str:
    """Rendering an explanatory but bounded comparison for a person."""
    left = comparison["left"]
    right = comparison["right"]
    jobs = comparison["jobs"]
    artifacts = comparison["artifacts"]
    jobs_added = _items(jobs["inventory"]["added"], key="name")
    jobs_removed = _items(jobs["inventory"]["removed"], key="name")
    artifacts_added = _items(artifacts["added"], key="name")
    artifacts_removed = _items(artifacts["removed"], key="name")
    lines = [
        f"Workflow comparison: {comparison['assessment']}",
        f"Left:  {left['repository']} run {left['run_id']} "
        f"attempt {left['run_attempt']} ({left['head_sha']})",
        f"Right: {right['repository']} run {right['run_id']} "
        f"attempt {right['run_attempt']} ({right['head_sha']})",
        f"Result: {left['conclusion']} / {left['assessment']} -> "
        f"{right['conclusion']} / {right['assessment']}",
        f"Known job duration: {_duration_text(jobs['duration_seconds'])}",
        f"Changed job states: {len(jobs['state_changes'])}; "
        f"added: {jobs_added}; removed: {jobs_removed}",
        f"Artifact inventory at capture: "
        f"{artifacts['left_total']} -> {artifacts['right_total']}; "
        f"added: {artifacts_added}; removed: {artifacts_removed}",
    ]
    lines.extend(f"Warning: {_safe(item)}" for item in comparison["warnings"][:MAX_LIST_ITEMS])
    return "\n".join(lines) + "\n"


def exit_code(comparison: dict[str, Any]) -> int:
    """Returning 4 only when required comparison evidence is incomplete."""
    return 0 if comparison.get("evidence_sufficient") else 4
