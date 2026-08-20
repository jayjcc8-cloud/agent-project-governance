---
name: context-governance
description: Checkpoint, resume, evaluate, bind, resolve bindings, migrate, and close actor-scoped AI work units without creating a second plan. Use for long-running coding tasks before compaction or handoff, after a crash or new session, when main agents and subagents need isolated runtime memory, when canonical local files or GitHub Issues/PRs may have changed, or when deciding whether to continue, delegate, converge, promote durable knowledge, or start a new work unit.
---

# Context Governance

Keep runtime memory durable and isolated while leaving formal planning and execution to the project's existing authorities.

## Boundaries

- Treat existing constitution, spec, plan, `tasks.md`, issues, and ADRs as authorities.
- Store only local authority paths or canonical GitHub identifiers and hashes. Never copy authority contents, task lists, or conversation transcripts.
- Require explicit work-unit and actor IDs. Never reuse a main agent binding for a subagent.
- Recommend actions; never spawn agents, create threads/worktrees, compact context, run converge, or change specifications.
- Operate only on `.agent-runtime/`.

## Workflow

Use `scripts/work_unit.py` for every runtime read and write. Pass the project root explicitly.

### Initialize

```bash
python3 scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md
```

Add a GitHub Issue or PR authority only with its canonical public URL. The command uses authenticated `gh api` access, normalizes stable governance fields, and stores only the identifier and SHA-256:

```bash
python3 scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md \
  --github-authority issue https://github.com/OWNER/REPO/issues/123
```

Use a distinct work unit and actor for every subagent or reviewer. Add `--parent-work-unit` only as causal metadata.

### Checkpoint and resume

```bash
python3 scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --summary "Contract tests pass; integration remains." \
  --next-action "Run the pinned integration smoke test." \
  --finding "Spec Kit tasks.md remains authoritative."

python3 scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict
```

Reconcile changed authorities before continuing. Explicit resume and evaluate refresh GitHub evidence; advisory hooks never make network requests. A read-only resume never upgrades legacy state.

`resume` returns a recovery contract with current authority evidence, transient git workspace identity, drift identities, completeness, a primary action, and non-persisted diagnostics. GitHub Issue/PR authorities in one work unit are fetched as one composite snapshot. When `completeness` is `complete` and `authority_verdict` is `matched`, treat the checkpoint summary, next action, findings, returned workspace identity, and returned authority evidence as the recovery evidence: do not reread local authorities or query GitHub again for facts already asserted there. Query separately only for material that is absent from both the checkpoint and returned evidence, such as full comments or Actions logs.

Treat `authority_verdict` as three-valued: `matched`, `changed`, or `unknown`. Remote transport/permission failure returns `completeness: unavailable` and exit `2`; bounded pagination overflow returns `completeness: incomplete` and exit `1`. Neither condition is drift, and neither may be treated as a successful freshness check. Reconcile the evidence path before continuing.

### Evaluate the next governance action

```bash
python3 scripts/work_unit.py evaluate \
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
python3 scripts/work_unit.py bind \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --session SESSION_ID
```

For a subagent, also pass its `--agent-id` and use a distinct actor/work unit. Use `unbind` with the same identifiers to remove a binding.

During an already-running Codex session, resolve only the current session's explicit binding before resume:

```bash
python3 scripts/work_unit.py resolve-binding \
  --project-root /path/to/project \
  --session "$CODEX_THREAD_ID"
```

Use the returned work-unit and actor IDs with `resume --strict`. Exit `1` means the current session is not bound, so recover directly from authorities or bind it explicitly. Never substitute a delegated source task ID for the current `CODEX_THREAD_ID`, never scan binding files, and never fall back from a subagent's `session + agent-id` key to a main-agent session key.

### Migrate or close

Use `migrate` for an explicit v0.1/v0.2/v0.3 → v0.4 upgrade. `checkpoint` also upgrades legacy state after validation and promotes legacy GitHub digests to the composite projection. Use `close --summary ...` only after a current checkpoint; close refuses authority drift and removes matching session bindings.

Read [references/state-schema.md](references/state-schema.md) only when changing the script, adding a consumer, or diagnosing incompatible state.
