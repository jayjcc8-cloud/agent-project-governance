---
name: project-bootstrap
description: Inspect and establish a repository's local AI project-governance environment without overwriting existing policy. Use when starting or adopting a project, checking Spec Kit, Superpowers, or speckit-superpowers-bridge readiness, previewing governance files, creating a minimal AGENTS.md or ADR area, or diagnosing an incomplete Agent Project Governance setup.
---

# Project Bootstrap

Establish governance without installing dependencies or taking ownership of specifications and tasks.

## Workflow

1. Run a read-only preview first:

```bash
python3 scripts/bootstrap.py plan --project-root /path/to/project
```

2. Review every `create`, `skip`, and `conflict` result. Treat existing files as user-owned. For a brownfield `AGENTS.md`, use the returned hashes and `missing_template_rules` as manual merge guidance; never replace the file.
3. Apply only after the user has authorized repository changes:

```bash
python3 scripts/bootstrap.py apply --project-root /path/to/project
```

4. Run the health check and report dependency warnings separately from file conflicts:

```bash
python3 scripts/bootstrap.py check --project-root /path/to/project
```

Add `--json` when another script or agent consumes the result.

## Boundaries

- Never overwrite or append to an existing file. Report a conflict with deterministic manual reconciliation guidance instead.
- Never install Spec Kit, Superpowers, or the bridge. Return copyable instructions only.
- Never create or edit constitution, spec, plan, tasks, implementation, worktree, or thread state.
- Keep `.agent-runtime/` private and derived. Spec Kit `tasks.md` remains the task source of truth.
- Use [references/compatibility.json](references/compatibility.json) only for local readiness classification; newer upstream versions remain `newer_unverified` until a recorded smoke test passes.
