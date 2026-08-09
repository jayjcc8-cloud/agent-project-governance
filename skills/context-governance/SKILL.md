---
name: context-governance
description: Checkpoint and resume actor-scoped AI work units without creating a second plan. Use for long-running coding tasks before compaction or context clearing, after a crash or new session, when main agents and subagents need isolated runtime memory, or when canonical task/spec files must be checked for changes before work resumes.
---

# Context Governance

Keep runtime memory durable and isolated while leaving formal planning to the project's existing
source of truth. Operate only on `.agent-runtime/work-units/`; never rewrite specs, plans, tasks,
worktrees, or Agent instructions.

## Boundaries

- Treat existing `spec.md`, `plan.md`, `tasks.md`, issues, and equivalent artifacts as authorities.
- Store only authority paths and hashes. Never copy their task lists or maintain competing status.
- Require an explicit work-unit ID and actor ID. Never reuse the main agent's state for a subagent.
- Recommend actions; do not spawn agents, create threads/worktrees, compact context, or change specs.
- Do not install Spec Kit, Superpowers, bridges, or other workflow frameworks.

## Workflow

Use `scripts/work_unit.py` for all state reads and writes. Run it with the Python available in the
environment and pass the user's project root explicitly.

### Start an isolated work unit

Choose a stable work-unit ID and an actor ID describing the actual owner. Add only canonical files as
authorities.

```bash
python scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md
```

Use a distinct ID for every subagent or reviewer, optionally linking it with `--parent-work-unit`.

### Checkpoint before context changes

Record only durable facts: what was verified, failed attempts worth avoiding, and the single next
action. Do not transcribe the conversation or invent new tasks.

```bash
python scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --summary "Adapter contract tests pass; integration test remains." \
  --next-action "Run the pinned bridge smoke test." \
  --finding "Spec Kit tasks.md remains authoritative." \
  --failed-attempt "Do not enable global planning hooks for subagents."
```

### Resume after a new session or crash

Resume with the same actor ID. Use `--strict` when changed or missing authority files must block
automatic continuation.

```bash
python scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict
```

Read the returned checkpoint and authority status. If an authority changed, reconcile it before
continuing. Never overwrite the authority from runtime state.

## State contract

Read [references/state-schema.md](references/state-schema.md) only when changing the script, adding a
consumer, or diagnosing incompatible state. The experiment intentionally supports only `init`,
`checkpoint`, and `resume`.
