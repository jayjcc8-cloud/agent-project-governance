# Agent Project Governance

- Treat the project's already accepted specifications, plans, issue tracker, and other declared task sources as authoritative; bootstrap must not create or replace project authority.
- Store only derived runtime memory under `.agent-runtime/`; never copy task lists into runtime state.
- Give every main agent, subagent, and reviewer a distinct actor-owned work unit.
- Checkpoint before context compaction or handoff, and reconcile changed authority files before resuming.
- Promote durable architecture decisions and agent rules only through the project's existing conventions.
