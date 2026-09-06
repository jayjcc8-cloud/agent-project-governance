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
  --event WORK_UNIT_STARTED \
  --summary "Contract tests pass; integration remains." \
  --next-action "Run the pinned integration smoke test." \
  --finding "Spec Kit tasks.md remains authoritative." \
  --state HEAD=abc123 \
  --state T1_REVIEW=PENDING

python3 scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --event REVIEW_VERDICT_CHANGED \
  --clear-findings \
  --state T1_REVIEW=PASS \
  --state BLOCKING_FINDINGS=0

python3 scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict
```

Reconcile changed authorities before continuing. Explicit resume and evaluate refresh GitHub evidence; advisory hooks never make network requests. A read-only resume never upgrades legacy state.

`resume` returns a recovery contract with current authority evidence, transient git workspace identity, drift identities, completeness, a primary action, and non-persisted diagnostics. GitHub Issue/PR authorities in one work unit are fetched as one composite snapshot. When `completeness` is `complete` and `authority_verdict` is `matched`, treat the checkpoint summary, next action, findings, returned workspace identity, and returned authority evidence as the recovery evidence: do not reread local authorities or query GitHub again for facts already asserted there. Query separately only for material that is absent from both the checkpoint and returned evidence, such as full comments or Actions logs.

Checkpoint updates are event-driven. Use `--event` only for an actual material
change: work-unit start/close; authority, HEAD, or base change; product decision;
finding open/close; review start/verdict/reviewer replacement; repair
start/budget/completion; recovery/handoff; or merge/post-merge progress. The
omitted-event default remains `SESSION_HANDOFF` only for compatibility with older
callers; it is not an ordinary-progress event.

The first checkpoint requires `--summary` and `--next-action`. Later checkpoints
inherit omitted summary, next action, findings, failed attempts, and structured
`--state KEY=VALUE` entries, so callers send only the material delta. Use
`--clear-findings` when the current finding set becomes empty. A changed
checkpoint writes the full canonical state atomically but reports only a stable
`delta`; an unchanged checkpoint reports `state_written: false`, no full status,
and skips evidence reads except for declared evidence/recovery/handoff events.
Do not reconstruct current state by replaying deltas: use `resume` for the full
canonical recovery snapshot.

Treat `authority_verdict` as three-valued: `matched`, `changed`, or `unknown`. Remote transport/permission failure returns `completeness: unavailable` and exit `2`; bounded pagination overflow returns `completeness: incomplete` and exit `1`. Neither condition is drift, and neither may be treated as a successful freshness check. Reconcile the evidence path before continuing.

### Handoff without another store

Use the existing checkpoint fields and [assets/handoff.md](assets/handoff.md)
before a writer, task, or session handoff. Keep the derived record short:

- Put the current goal, authorization source, worktree, branch, and HEAD in `summary`.
- Put known uncommitted work, verified facts, the original blocker, and review
  rounds already used in `findings` or `failed_attempts` as appropriate.
- Put exactly one next bounded action in `next_action`.
- Record current machine-readable fields such as HEAD, review verdict, open
  finding count, and repair usage with `--state`, and label the update
  `--event SESSION_HANDOFF`.

A new session must resume the same actor-owned work unit and independently
recheck mutable workspace facts before writing. It must not reset review or
repair budgets. A complete, fresh recovery contract should not trigger duplicate
queries for evidence it already contains. A checkpoint is derived memory, not an
authority, writer lock, task database, or proof that delivery has passed.

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

Closing a work unit closes local derived memory only. It does not mean the
product was accepted, CI passed, or a pull request was merged.

Read [references/state-schema.md](references/state-schema.md) only when changing the script, adding a consumer, or diagnosing incompatible state.
