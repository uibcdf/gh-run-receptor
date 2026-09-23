import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_support_metadata_matches_the_authorized_transition():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["requires-python"] == ">=3.11,<3.15"
    assert project["dependencies"] == []
    assert {
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    } <= set(project["classifiers"])


def test_suite_policy_caller_pins_current_release():
    workflow = (ROOT / ".github" / "workflows" / "molsyssuite-policy.yml").read_text(
        encoding="utf-8"
    )

    assert "check-python-repository.yaml@policy-v1.4.9" in workflow
