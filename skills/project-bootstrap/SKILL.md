---
name: project-bootstrap
description: Explicitly initialize or compatibility-check a repository's AI governance setup without overwriting existing policy. Use only when the user asks to bootstrap, initialize, or inspect governance assets; do not use for ordinary task intake or every existing-project handoff.
---

# Project Bootstrap

Establish governance without installing dependencies or taking ownership of specifications and tasks.

## Workflow

1. Select a profile. `existing-project` is the default and does not require or
   probe Spec Kit, Superpowers, or the bridge. Use `spec-kit-stack` only when
   that full framework combination was explicitly selected.
2. Run a read-only preview first:

```bash
python3 scripts/bootstrap.py plan --project-root /path/to/project \
  --profile existing-project
```

3. Review every `create`, `skip`, `user_owned`, `not_applicable`, and `conflict`
   result. Treat existing files as user-owned. For a brownfield `AGENTS.md`, use
   the returned hashes and `missing_template_rules` only as manual guidance.
4. Apply only after the user has authorized repository changes:

```bash
python3 scripts/bootstrap.py apply --project-root /path/to/project \
  --profile existing-project
```

5. Run the health check and report core readiness separately from optional
   framework compatibility:

```bash
python3 scripts/bootstrap.py check --project-root /path/to/project \
  --profile existing-project
```

Add `--json` when another script or agent consumes the result.

To recover the pre-0.5 full-stack behavior, pass `--profile spec-kit-stack`
explicitly to `plan`, `check`, or `apply`.

## Boundaries

- Never overwrite or append to an existing file. Report a conflict with deterministic manual reconciliation guidance instead.
- Never install Spec Kit, Superpowers, or the bridge. Return copyable instructions only.
- Never create or edit constitution, spec, plan, tasks, implementation, worktree, or thread state.
- Keep `.agent-runtime/` private and derived. Spec Kit `tasks.md` remains the task source of truth.
- Use [references/compatibility.json](references/compatibility.json) only for local readiness classification; newer upstream versions remain `newer_unverified` until a recorded smoke test passes.
- `ready` means only that the selected bootstrap profile has no bootstrap blocker;
  it does not prove code correctness, CI success, current remote freshness, or merge authorization.
