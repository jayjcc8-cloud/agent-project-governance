# Agent Project Governance

- Treat Spec Kit specifications, plans, and `tasks.md` as canonical project truth.
- Use Superpowers and the Spec Kit–Superpowers bridge for implementation discipline and handoff.
- Store only derived runtime memory under `.agent-runtime/`; never copy task lists into runtime state.
- Give every main agent, subagent, and reviewer a distinct actor-owned work unit.
- Checkpoint before context compaction or handoff, and reconcile changed authority files before resuming.
- Promote durable architecture decisions to `docs/adr/` and durable agent rules to this file.
