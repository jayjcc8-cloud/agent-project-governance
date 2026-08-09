# Agent Project Governance

A deliberately small, skills-only Codex plugin for durable context governance in long-running AI engineering work.

Repository: [github.com/jayjcc8-cloud/agent-project-governance](https://github.com/jayjcc8-cloud/agent-project-governance)

Version 0.2 is a developer preview with two workflows:

- `project-bootstrap` previews and creates missing governance assets without overwriting project policy or installing dependencies.
- `context-governance` checkpoints, resumes, evaluates, binds, migrates, and closes actor-owned work units under `.agent-runtime/`.

## Responsibility model

| Layer | Responsibility |
|---|---|
| Spec Kit | WHAT: constitution, specification, plan, and canonical `tasks.md` |
| Superpowers | HOW: worktrees, TDD, debugging, subagents, review, and verification |
| speckit-superpowers-bridge | Handoff between WHAT and HOW |
| Agent Project Governance | WHEN/HOW TO CONTINUE: isolated runtime memory and advisory lifecycle decisions |

The plugin never creates a competing task plan, copies task lists into runtime state, edits formal artifacts, spawns agents, creates worktrees, or runs converge.

## Project bootstrap

Preview first:

```bash
python3 skills/project-bootstrap/scripts/bootstrap.py plan \
  --project-root /path/to/project
```

Apply only missing files:

```bash
python3 skills/project-bootstrap/scripts/bootstrap.py apply \
  --project-root /path/to/project
```

Existing files are never changed. A differing `AGENTS.md`, `.gitignore`, policy, or ADR file is reported as a conflict for manual reconciliation. Missing Spec Kit, Superpowers, and bridge installations produce copyable instructions but are never installed automatically.

## Context governance

Initialize an actor-owned work unit and record only canonical file paths and hashes:

```bash
python3 skills/context-governance/scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md
```

Checkpoint before compaction or handoff:

```bash
python3 skills/context-governance/scripts/work_unit.py checkpoint \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --summary "Contract tests pass; integration remains." \
  --next-action "Run the pinned integration smoke test."
```

Resume strictly and evaluate an advisory next action:

```bash
python3 skills/context-governance/scripts/work_unit.py resume \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --strict

python3 skills/context-governance/scripts/work_unit.py evaluate \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --event pre-compact \
  --signal repeated-failure
```

The rule engine returns ordered actions such as `RECONCILE`, `UPDATE_SPEC`, `CONVERGE`, `CHECKPOINT`, `DEBUG_REVIEW`, `WORKTREE`, `NEW_THREAD`, or `CONTINUE`. Every recommendation includes a stable reason and `blocking: false`.

## Advisory hooks

Codex discovers `hooks/hooks.json` automatically when the plugin is enabled. Hooks cover `SessionStart`, `PreCompact`, `SubagentStart`, `SubagentStop`, and `Stop`.

Hooks are read-only and advisory:

- They never parse chat transcripts.
- They never checkpoint, continue a turn, block compaction, or perform a recommended action.
- They read a work unit only after the current session has been explicitly bound.
- A subagent never inherits the main session binding.

Review and trust the plugin hooks in Codex before they run. macOS and Linux hooks are supported in 0.2; Windows hook commands remain experimental. The core Python CLI supports Python 3.9+ on macOS, Linux, and Windows.

## Compatibility baseline

The bootstrap health report uses the bridge's published compatibility evidence:

- speckit-superpowers-bridge `1.1.0`
- Spec Kit `0.11.1` verified, `0.8.10` minimum
- Superpowers `6.0.0` verified

Newer versions are reported as `newer_unverified`, not as incompatible. See [the compatibility smoke protocol](docs/compatibility-smoke.md) before expanding the verified matrix.

## Validation

```bash
PYTHONPYCACHEPREFIX=/tmp/apg-pycache python3 -m unittest discover -s tests -v
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
python3 /path/to/skill-creator/scripts/quick_validate.py skills/project-bootstrap
python3 /path/to/skill-creator/scripts/quick_validate.py skills/context-governance
```

Real long-task trials determine whether the project advances to V1. Record recovery time, actor state leaks, and unnoticed authority changes using [the trial template](docs/trials.md).

## License

MIT
