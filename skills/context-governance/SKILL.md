---
name: context-governance
description: Recover existing context only after real context loss, session interruption, handoff, or long-running task resume. Not for ordinary task start, progress, review, or completion.
---

# Context Governance

Exceptional recovery only. Normal tasks use retrieval and conditional learning;
they need no work unit, binding, checkpoint, evaluation, or close operation.
Recover directly from canonical project sources when no prior runtime state is
available. Do not create empty artifacts to satisfy this skill.

## Boundaries

- Treat existing constitution, spec, plan, `tasks.md`, issues, and ADRs as authorities.
- Store only local authority paths or canonical GitHub identifiers and hashes. Never copy authority contents, task lists, or conversation transcripts.
- Require explicit work-unit and actor IDs. Never reuse a main agent binding for a subagent.
- Recommend actions; never spawn agents, create threads/worktrees, compact context, run converge, or change specifications.
- Operate only on `.agent-runtime/`.

## Workflow

Use `scripts/work_unit.py` for every runtime read and write. Pass the project root explicitly.

### Initialize only for a real handoff needing missing context

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

If a recovery record is actually needed, keep its actor isolated. Subagents and reviewers do not require work units merely because they exist.

### Checkpoint and resume

```bash
python3 scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --event SESSION_HANDOFF \
  --summary "Contract tests pass; integration remains." \
  --next-action "Run the pinned integration smoke test."

python3 scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict
```

Reconcile changed authorities before continuing. Explicit resume and evaluate refresh GitHub evidence; advisory hooks never make network requests. A read-only resume never upgrades legacy state.

`resume` returns a recovery contract with current authority evidence, transient git workspace identity, drift identities, completeness, a primary action, and non-persisted diagnostics. GitHub Issue/PR authorities in one work unit are fetched as one composite snapshot. When `completeness` is `complete` and `authority_verdict` is `matched`, treat the checkpoint summary, next action, findings, returned workspace identity, and returned authority evidence as the recovery evidence: do not reread local authorities or query GitHub again for facts already asserted there. Query separately only for material that is absent from both the checkpoint and returned evidence, such as full comments or Actions logs.

Checkpoint only for an actual recovery/handoff need. Do not mirror task start,
HEAD changes, review verdicts, repair progress, merge, or completion into runtime
state. Existing event names remain accepted for older callers. Use links to the
canonical Issue/PR/CI instead of duplicating their state.

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
- Use optional `--state` fields only for missing recovery context, and label the
  update `--event SESSION_HANDOFF`. Do not duplicate current Issue/PR/CI facts.

When resuming an interrupted task with an existing work unit, use that unit and
recheck mutable workspace facts before writing. It must not reset review or
repair budgets. A complete, fresh recovery contract should not trigger duplicate
queries for evidence it already contains. A checkpoint is derived memory, not an
authority, writer lock, task database, or proof that delivery has passed.

### Optional recovery diagnostics

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

Only when an actual recovery needs hook transport, optionally bind the selected work unit:

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

Use the returned work-unit and actor IDs with `resume --strict`. Exit `1` means the current session is not bound; recover directly from authorities. It does not require initialization or binding. Never substitute a delegated source task ID for the current `CODEX_THREAD_ID`, never scan binding files, and never fall back from a subagent's `session + agent-id` key to a main-agent session key.

### Explicit compatibility operations, not task completion

Use `migrate` for an explicit v0.1/v0.2/v0.3 → v0.4 upgrade. `checkpoint` also upgrades legacy state after validation and promotes legacy GitHub digests to the composite projection. Use `close --summary ...` only after a current checkpoint; close refuses authority drift and removes matching session bindings.

Closing a work unit closes local derived memory only. It does not mean the
product was accepted, CI passed, or a pull request was merged.

Read [references/state-schema.md](references/state-schema.md) only when changing the script, adding a consumer, or diagnosing incompatible state.

## Do not use when

- A normal task starts, progresses, receives review, or completes without interruption.
- The only reason is that a main agent, subagent, or reviewer exists.
- Existing Issue/PR/Git/CI facts already answer the question.
