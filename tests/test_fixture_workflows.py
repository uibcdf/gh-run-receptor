from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_timed_out_fixture_is_manual_bounded_and_inert():
    workflow = ROOT / ".github/workflows/fixture_timed_out.yml"

    assert workflow.read_text(encoding="utf-8") == """\
name: Fixture - timed out

on:
  workflow_dispatch:

permissions: {}

jobs:
  timed-out:
    runs-on: ubuntu-latest
    timeout-minutes: 1
    steps:
      - name: Wait beyond the job timeout
        run: sleep 90
"""
