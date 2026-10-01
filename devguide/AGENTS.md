# Developer guide instructions

These rules apply within `devguide/` and refine the repository guide.

- Treat `README.md` as the current checkpoint and keep its reading order and coverage
  table current.
- Read current normative documents and pending queue indexes when onboarding. Do not read
  archived reports recursively; the archive summary is sufficient unless a concrete
  question or current document identifies a relevant historical report.
- Follow `reporting_protocol.md` for every pending or archived bug and proposal report.
- Open the GitHub issue before creating its report. Keep analysis in the report and public
  state in the issue.
- Never edit generated index content by hand. Run `devtools/scripts/devguide_index.py`.
- Preserve archived reports as historical evidence. Append a dated correction when a
  historical claim was never true.

## Durable working instructions

Read [../AGENTS.md](../AGENTS.md), [reporting_protocol.md](reporting_protocol.md)
and [the common policy](../MOLSYSSUITE_GUIDE.md#durable-working-instructions).
Keep technical findings in owning issues, tests and maintained documents. Place
only accepted lasting actions specific to this directory here; repository-wide
actions belong at root. Read current guidance and relevant active queues first;
use archive indexes for orientation and open historical records for a stated
question. Follow the local reporting protocol for actual queue/archive layouts,
index regeneration, offline gates and synchronization with owning GitHub issues.
Archive and index resolved records in the same change; append dated corrections
to archived claims instead of rewriting history.
