import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_action_metadata_exposes_the_bounded_first_contract():
    source = (ROOT / "action.yml").read_text(encoding="utf-8")

    for input_name in (
        "run-id",
        "repository",
        "profile",
        "capture",
        "report-name",
        "strict-reporter",
    ):
        assert f"  {input_name}:\n" in source
    for output_name in (
        "assessment",
        "github-conclusion",
        "profile",
        "failed-groups",
        "incomplete-groups",
        "report-artifact",
        "report-path",
    ):
        assert f"  {output_name}:\n" in source
    assert 'using: "composite"' in source
    assert "GITHUB_STEP_SUMMARY" not in source
    assert "GH_TOKEN: ${{ github.token }}" in source
    assert "INPUT_STRICT_REPORTER: ${{ inputs['strict-reporter'] }}" in source
    assert "continue-on-error: ${{ inputs['strict-reporter'] != 'true' }}" in source
    assert "steps.reporter.outputs['report-ready'] == 'true'" in source
    assert "inputs.run-id" not in source
    assert "outputs.report-path" not in source


def test_action_metadata_pins_external_actions_to_full_commits():
    source = (ROOT / "action.yml").read_text(encoding="utf-8")
    uses = [line.strip().removeprefix("uses: ") for line in source.splitlines() if "uses:" in line]

    assert uses == [
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7",
        "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6",
    ]
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40} # v[0-9]+", value) for value in uses)
