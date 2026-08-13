# Agent Project Governance

A deliberately small, skills-only Codex plugin for durable context governance in long-running AI engineering work.

Repository: [github.com/jayjcc8-cloud/agent-project-governance](https://github.com/jayjcc8-cloud/agent-project-governance)

Version 0.4 is a developer preview with two workflows:

- `project-bootstrap` previews and creates missing governance assets without overwriting project policy or installing dependencies.
- `context-governance` checkpoints, resumes, evaluates, binds, resolves bindings, migrates, and closes actor-owned work units under `.agent-runtime/`.

## Responsibility model

| Layer | Responsibility |
|---|---|
| Spec Kit | WHAT: constitution, specification, plan, and canonical `tasks.md` |
| Superpowers | HOW: worktrees, TDD, debugging, subagents, review, and verification |
| speckit-superpowers-bridge | Handoff between WHAT and HOW |
| Agent Project Governance | WHEN/HOW TO CONTINUE: isolated runtime memory and advisory lifecycle decisions |

The plugin never creates a competing task plan, copies task lists into runtime state, edits formal artifacts, spawns agents, creates worktrees, or runs converge.

See [capability boundaries and production posture](docs/capability-boundaries.md) for the explicit supported/unsupported matrix and current shadow-pilot restriction.

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

For brownfield `AGENTS.md` files, JSON output includes existing/template digests and the missing minimal governance rules. This is merge guidance only; `apply` still never edits the user-owned file.

## Context governance

Initialize an actor-owned work unit and record only canonical authority identifiers and hashes:

```bash
python3 skills/context-governance/scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md
```

GitHub Issues and PRs can also be tracked without persisting their contents:

```bash
python3 skills/context-governance/scripts/work_unit.py init \
  --project-root /path/to/project \
  --work-unit feature-001 \
  --actor main \
  --authority tasks specs/001-feature/tasks.md \
  --github-authority issue https://github.com/OWNER/REPO/issues/123 \
  --github-authority implementation https://github.com/OWNER/REPO/pull/456
```

Remote checks use one authenticated GitHub GraphQL snapshot per work unit. The `github-v2` digest includes Issue/PR governance fields plus PR review-thread resolution and check rollups. Only canonical identifiers, projection versions, and SHA-256 digests are stored; current normalized evidence appears only in explicit command output, and hooks never perform network requests.

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

`resume` returns a recovery contract with completeness, drift identities, normalized authority evidence, a primary action, and per-command diagnostics. When the contract is complete, consumers should not repeat GitHub reads for fields already returned.

The rule engine returns ordered actions such as `RECONCILE`, `UPDATE_SPEC`, `CONVERGE`, `CHECKPOINT`, `DEBUG_REVIEW`, `WORKTREE`, `NEW_THREAD`, or `CONTINUE`. Every recommendation includes a stable reason and `blocking: false`.

Resolve a binding for the current Codex task without scanning runtime files or guessing actor ownership:

```bash
python3 skills/context-governance/scripts/work_unit.py resolve-binding \
  --project-root /path/to/project \
  --session "$CODEX_THREAD_ID"
```

The command is read-only. It returns `0` with the exact binding, `1` when no active binding exists, and `2` for invalid state or input. Subagents must also pass their own `--agent-id`; resolution never falls back to a main-agent binding.

## Advisory hooks

Codex discovers `hooks/hooks.json` automatically when the plugin is enabled. Hooks cover `SessionStart`, `PreCompact`, `SubagentStart`, `SubagentStop`, and `Stop`.

Hooks are read-only and advisory:

- They never parse chat transcripts.
- They never checkpoint, continue a turn, block compaction, or perform a recommended action.
- They read a work unit only after the current session has been explicitly bound.
- A subagent never inherits the main session binding.
- The POSIX launcher fails open when its pinned plugin directory or Python adapter is unavailable, so a retired build cannot block Stop or compaction.

Review and trust the plugin hooks in Codex before they run. macOS and Linux hooks are supported in 0.4; Windows hook commands remain experimental. The core Python CLI supports Python 3.9+ on macOS, Linux, and Windows.

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

For local development updates, treat every cachebuster build as immutable. Add the new build before retiring an old one, and never run `codex plugin remove` while a task may still reference the installed cache path. Existing Codex tasks keep using their pinned build until they end; new tasks select the newly added build. Release validation executes the Hook launcher from the packaged ZIP and also simulates a missing retired build.

## Public installation and releases

Add the public GitHub marketplace pinned to this release, then install the plugin:

```bash
codex plugin marketplace add jayjcc8-cloud/agent-project-governance --ref v0.4.0
codex plugin add agent-project-governance@agent-project-governance
```

The repository marketplace is pinned to the same tag as the plugin manifest. Pushing `v0.4.0` runs the release workflow, validates Python 3.9 syntax and package invariants, executes all tests, and publishes a deterministic ZIP plus SHA-256 to GitHub Releases. This public GitHub distribution is separate from submission to OpenAI's universal Plugins Directory.

## License

MIT
