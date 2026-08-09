---
name: context-governance
description: Checkpoint, resume, evaluate, bind, migrate, and close actor-scoped AI work units without creating a second plan. Use for long-running coding tasks before compaction or handoff, after a crash or new session, when main agents and subagents need isolated runtime memory, when canonical spec/task files may have changed, or when deciding whether to continue, delegate, converge, promote durable knowledge, or start a new work unit.
---

# Context Governance

Keep runtime memory durable and isolated while leaving formal planning and execution to the project's existing authorities.

## Boundaries

- Treat existing constitution, spec, plan, `tasks.md`, issues, and ADRs as authorities.
- Store only authority paths and hashes. Never copy their task lists or conversation transcripts.
- Require explicit work-unit and actor IDs. Never reuse a main agent binding for a subagent.
- Recommend actions; never spawn agents, create threads/worktrees, compact context, run converge, or change specifications.
- Operate only on `.agent-runtime/`.

## Workflow

Use `scripts/work_unit.py` for every runtime read and write. Pass the project root explicitly.

### Initialize

```bash
python scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md
```

Use a distinct work unit and actor for every subagent or reviewer. Add `--parent-work-unit` only as causal metadata.

### Checkpoint and resume

```bash
python scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --summary "Contract tests pass; integration remains." \
  --next-action "Run the pinned integration smoke test." \
  --finding "Spec Kit tasks.md remains authoritative."

python scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict
```

Reconcile changed authorities before continuing. A read-only resume never upgrades legacy state.

### Evaluate the next governance action

```bash
python scripts/work_unit.py evaluate \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --event pre-compact \
  --signal repeated-failure
```

Treat `primary_action` and `recommendations` as advisory. Read [references/decision-rules.md](references/decision-rules.md) only when changing or diagnosing rule behavior.

### Bind a Codex session

When a SessionStart hook supplies a session ID, bind it only after selecting the correct work unit:

```bash
python scripts/work_unit.py bind \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --session SESSION_ID
```

For a subagent, also pass its `--agent-id` and use a distinct actor/work unit. Use `unbind` with the same identifiers to remove a binding.

### Migrate or close

Use `migrate` for an explicit v0.1 → v0.2 upgrade. `checkpoint` also upgrades legacy state after validation. Use `close --summary ...` only after a current checkpoint; close refuses authority drift and removes matching session bindings.

Read [references/state-schema.md](references/state-schema.md) only when changing the script, adding a consumer, or diagnosing incompatible state.
