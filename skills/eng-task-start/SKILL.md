---
name: eng-task-start
description: Retrieve knowledge directly relevant to a real task start. Use once at task intake, not for every reply or ordinary continuation. Existing project authority controls development.
---

# Task Start — Retrieve

Search once through the project's approved knowledge route for contracts, known
issues, decisions, existing solutions, or reusable knowledge that can affect this
real task. Bound the search to the task; do not scan the whole knowledge base.

Report in the current task conversation only:

```text
RETRIEVAL_USED=YES|NO
REUSED_KNOWLEDGE=<references or NONE>
```

If nothing relevant exists, report `REUSED_KNOWLEDGE=NONE` and proceed immediately.
No hit is not a blocker. Execute the user's task under its existing project rules.
Do not initialize/bind a work unit, generate a manifest, copy the task, or record
that this checkpoint ran. No recovery artifact is required for a normal task.

For a real handoff conflict only, the existing read-only workspace inspector is
available; it is not a required intake step:

```bash
python3 ../context-governance/scripts/work_unit.py inspect-workspace \
  --project-root /absolute/project/path
```

This observation is not a writer lock, remote freshness proof, CI verdict, or
merge authorization. Preserve unknown work and obey the project's write rules.
See [workspace details](references/workspace.md) and
[asset provenance](references/provenance.md) only when that inspection is needed.

## Do not use when

- The task is already active and no new task has started.
- The user asks a small explanatory question with no relevant project knowledge.
- The request is setup; bootstrap is an explicit compatibility helper.
- Real context loss or handoff needs recovery; use `context-governance` then.
