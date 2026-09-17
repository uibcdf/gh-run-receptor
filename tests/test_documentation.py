import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"

PAGES = (
    "installation",
    "usage",
    "profiles",
    "embedded-reporting",
    "configuration",
    "contracts",
    "security",
    "limitations",
    "benchmarks",
)


def test_public_documentation_navigation_is_complete():
    index = (DOCS / "index.md").read_text(encoding="utf-8")

    for page in PAGES:
        assert (DOCS / f"{page}.md").is_file()
        assert re.search(rf"^{re.escape(page)}$", index, flags=re.MULTILINE)

    assert "devguide" not in PAGES
    assert "without hiding failures or uncertainty" in " ".join(index.split())


def test_documentation_dependencies_are_optional_and_version_bounded():
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = configuration["project"]
    docs = project["optional-dependencies"]["docs"]

    assert project["dependencies"] == []
    assert docs == [
        "myst-parser>=4,<5",
        "sphinx>=8,<10",
        "sphinx-rtd-theme>=3,<4",
    ]
    assert project["urls"]["Documentation"] == "https://uibcdf.github.io/gh-run-receptor/"


def test_pages_workflow_separates_read_only_build_from_deployment_permissions():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "push:" in source
    assert "pull_request:" in source
    assert "permissions: {}" in source
    assert "contents: read" in source
    assert "pages: write" in source
    assert "id-token: write" in source
    assert "if: github.event_name != 'pull_request'" in source
    assert "timeout-minutes: 10" in source
    assert "timeout-minutes: 5" in source
    assert "sphinx-build -W --keep-going -b html docs docs/_build/html" in source
    assert "persist-credentials: false" in source


def test_pages_workflow_pins_every_external_action():
    source = WORKFLOW.read_text(encoding="utf-8")
    actions = [
        line.strip().removeprefix("- ").removeprefix("uses: ")
        for line in source.splitlines()
        if "uses:" in line
    ]

    assert actions == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7",
        "actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa # v3",
        "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4",
    ]
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40} # v[0-9]+", action) for action in actions)
