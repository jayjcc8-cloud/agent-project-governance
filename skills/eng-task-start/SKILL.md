---
name: eng-task-start
description: Explicitly inspect and take over an authorized engineering task by refreshing repository, branch, worktree, dirty-state, and scope evidence. Use for task intake or handoff conflicts, not as an automatic bootstrap or daily reply ritual.
---

# Engineering Task Start

Refresh the facts needed to admit one bounded task without initializing another
governance framework or treating old conversation text as current authority.

## Workflow

1. Identify the current authorization, acceptance source, write/merge/cleanup
   boundaries, and explicit non-goals. A roadmap is not blanket authorization.
2. Read the project entry instructions, current Issue or equivalent authority,
   and only the directly relevant code and contract.
3. Run the packaged read-only workspace inspection from this plugin:

```bash
python3 ../context-governance/scripts/work_unit.py inspect-workspace \
  --project-root /absolute/project/path \
  --target-branch feature/example \
  --base origin/main
```

4. Treat `remote_freshness: NOT_CHECKED_LOCAL_REFS_ONLY` literally. Fetch or
   query a remote only when separately authorized and required; never print a
   credential-bearing remote URL.
5. Reuse the current Issue, PR, branch, and clean physical checkout when safe.
   If the target branch is checked out elsewhere, inspect that checkout and
   establish writer handoff. Never force checkout, delete, blanket-stash, clean,
   or reset unknown work.
6. Unknown dirty work, unexplained local-only commits, divergence, detached or
   unborn state, or an active writer pauses only conflicting writes. Preserve
   the evidence and identify the one required next action.
7. Summarize the goal, completion test, scope, writer, checkout, base, validation
   entry point, review need, and stop condition in the existing Issue or work
   unit. Do not create a second task database.

The snapshot is local observation, not a writer lock, CI result, remote freshness
proof, or merge authorization. See [workspace details](references/workspace.md)
and [asset provenance](references/provenance.md).

## Do not use when

- The user only asks a small explanatory question.
- The task is already active and no handoff or mutable intake fact needs refresh.
- The user asks to initialize governance assets; use `project-bootstrap` instead.
- The current authorization is read-only; this skill never upgrades it to write.
