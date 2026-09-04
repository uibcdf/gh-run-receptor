# Changelog

All notable changes to this project will be documented in this file.

## 0.1.0a1 - Unreleased

- Add the first read-only `inspect`, `capture`, and `replay` vertical slice.
- Acquire run, workflow, paginated job, check-run, artifact, and optional log evidence
  through the authenticated GitHub CLI.
- Store immutable evidence members with SHA-256 validation and attempt-aware identities.
- Add distinct `human` and `llm` receptors plus a versioned JSON report.
- Infer the text receptor from terminal interactivity while allowing explicit selection.
- Preserve authoritative GitHub conclusions and provisional exit-code semantics.
- Build an installable, dependency-free Python wheel and a GitHub CLI extension launcher.
- Validate the MVP against a real MolSysMT Conda workflow capture.
