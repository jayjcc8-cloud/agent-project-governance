# Agent Project Governance

An independent, deliberately small experiment for durable context governance in long-running AI
engineering work.

Version 0.1 validates only three capabilities:

1. actor-scoped work-unit isolation;
2. atomic checkpoints before context changes;
3. artifact-aware resume after a new session or crash.

It does not create specifications, plans, tasks, worktrees, threads, or subagents. Existing systems
such as Spec Kit and Superpowers remain responsible for those concerns. Canonical artifacts are
referenced by path and digest; `.agent-runtime/` is private derived state, never a second task source.

## Experiment success criteria

The project advances beyond 0.1 only if real long-task trials show lower recovery time, fewer actor
state leaks, or fewer unnoticed authority changes than the same workflow without this plugin.

## Local validation

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
python3 /path/to/skill-creator/scripts/quick_validate.py skills/context-governance
```
