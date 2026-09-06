# Agent Project Governance

A deliberately small, skills-only Codex plugin for execution continuity and context support in long-running AI engineering work.

Repository: [github.com/jayjcc8-cloud/agent-project-governance](https://github.com/jayjcc8-cloud/agent-project-governance)

Version 0.5 is an unreleased developer-preview candidate that retains five focused workflow entry points:

- `project-bootstrap` explicitly initializes or compatibility-checks governance assets.
- `context-governance` checkpoints, resumes, hands off, binds, and closes actor-owned work units under `.agent-runtime/`.
- `eng-task-start` refreshes local Git/worktree and authorization facts for ordinary task intake.
- `eng-bounded-delivery` keeps implementation and one independent review inside the current task contract.
- `eng-verified-closeout` verifies the current candidate, CI, package, merge, and authorized cleanup as separate facts.

These entry points are not a required chain and do not define the V1 product boundary. The [APG V1 core contract](docs/apg-v1-contract.md) limits the product core to context/task continuity, task-source realignment, worktree boundaries, and recovery/budget continuity. Bootstrap, bounded delivery, verified closeout, advisory hooks, and historic drift or timing experiments remain auxiliary or compatibility evidence.

## Responsibility model

| Layer | Responsibility |
|---|---|
| Spec Kit | WHAT: constitution, specification, plan, and canonical `tasks.md` |
| Superpowers | HOW: worktrees, TDD, debugging, subagents, review, and verification |
| speckit-superpowers-bridge | Handoff between WHAT and HOW |
| Agent Project Governance | HOW TO CONTINUE: task continuity, task-source realignment, worktree-boundary evidence, and recovery/budget continuity |

The plugin never creates a competing task plan, copies task lists into runtime state, edits formal artifacts, approves technical conclusions, spawns agents, creates worktrees, or runs converge. GitHub, the repository, accepted Specs, Issues, PRs, and CI remain the product facts and acceptance sources.

See [capability boundaries and production posture](docs/capability-boundaries.md) for the explicit supported/unsupported matrix and current shadow-pilot restriction.

## Project bootstrap

Preview first:

```bash
python3 skills/project-bootstrap/scripts/bootstrap.py plan \
  --project-root /path/to/project \
  --profile existing-project
```

Apply only missing files:

```bash
python3 skills/project-bootstrap/scripts/bootstrap.py apply \
  --project-root /path/to/project \
  --profile existing-project
```

`existing-project` is the default. It does not probe or require Spec Kit,
Superpowers, or the bridge; those dependencies are `not_applicable`. Existing
files are user-owned and never changed. Missing ADR conventions are not a task
intake blocker, and `ready` does not assert code correctness, CI success, remote
freshness, or merge authorization.

For brownfield `AGENTS.md` files, JSON output includes existing/template digests and the missing minimal governance rules. This is merge guidance only; `apply` still never edits the user-owned file.

Projects that explicitly selected the former full framework combination retain
the 0.4 compatibility and asset gate by passing `--profile spec-kit-stack` to
`plan`, `check`, or `apply`. No profile installs a dependency.

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

`resume` returns a recovery contract with completeness, a three-valued `matched | changed | unknown` authority verdict, drift identities, normalized evidence, a primary action, and per-command diagnostics. Unavailable or incomplete remote evidence is never reported as matched and is never written to state. When the contract is complete, consumers should not repeat GitHub reads for fields already returned.

The rule engine returns ordered actions such as `RECONCILE`, `UPDATE_SPEC`, `CONVERGE`, `CHECKPOINT`, `DEBUG_REVIEW`, `WORKTREE`, `NEW_THREAD`, or `CONTINUE`. Every recommendation includes a stable reason and `blocking: false`.

Resolve a binding for the current Codex task without scanning runtime files or guessing actor ownership:

```bash
python3 skills/context-governance/scripts/work_unit.py resolve-binding \
  --project-root /path/to/project \
  --session "$CODEX_THREAD_ID"
```

The command is read-only. It returns `0` with the exact binding, `1` when no active binding exists, and `2` for invalid state or input. Subagents must also pass their own `--agent-id`; resolution never falls back to a main-agent binding.

Inspect a checkout without creating a work unit or binding:

```bash
python3 skills/context-governance/scripts/work_unit.py inspect-workspace \
  --project-root /path/to/project \
  --target-branch feature/example \
  --base origin/main
```

This read-only local snapshot uses NUL-delimited Git output, excludes
`.agent-runtime` from dirty-state admission, detects worktree occupancy and HEAD
movement, and reports detached/unborn or unavailable-ref states. It never fetches
or claims exclusive writer ownership; local remote-tracking refs are explicitly
reported as not freshness-checked. `resume` keeps its existing compact
`checked/head/clean` workspace shape through a thin adapter to the same helper.

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
python3 /path/to/skill-creator/scripts/quick_validate.py skills/eng-task-start
python3 /path/to/skill-creator/scripts/quick_validate.py skills/eng-bounded-delivery
python3 /path/to/skill-creator/scripts/quick_validate.py skills/eng-verified-closeout
```

The repository validator checks exactly these five skills, their local references,
the explicit-only policy for the three new entry points, Python 3.9 syntax, Hook
fail-open behavior, and the shared workspace helper from outside the source tree.
Real Codex/Claude loading, automatic triggering, and multi-skill host behavior
remain `NOT_RUN` for this source integration.

Real product tasks determine whether APG V1 demonstrates value. The current product status is `APG_V1_ACCEPTANCE=PENDING_THREE_REAL_PRODUCT_TASKS`. Per-task `APG_ACCEPTANCE=PASS` requires APG to solve or avoid a concrete continuity/context problem without blocking product development; mechanism health, recovery timing, and injected source-change tests cannot pass that gate alone or promote the global status. Use [the three-real-task value evaluation](docs/apg-v1-three-task-value-evaluation.md). The older recovery and drift records remain historical mechanism evidence in [the trial index](docs/trials.md).

For local development updates, treat every cachebuster build as immutable. Do not update an installed plugin while any task may still reference its current cache path: Codex CLI `plugin add` was observed removing older cache directories even without a preceding `plugin remove`. Existing tasks cannot be hot-swapped and may call their pinned Hook path later. Update only after those tasks end, or preserve and explicitly verify every pinned cache path before resuming them. Release validation executes the Hook launcher from the packaged ZIP and simulates a missing retired build, but fail-open behavior is not uninterrupted cache retention.

## Public installation and releases

The source metadata is prepared for a future authorized `v0.5.0` prerelease. This
integration does not create that tag, publish a release, or install a plugin.
After a maintainer separately authorizes and publishes the tag, the intended
installation commands are:

```bash
codex plugin marketplace add jayjcc8-cloud/agent-project-governance --ref v0.5.0
codex plugin add agent-project-governance@agent-project-governance
```

The repository marketplace is pinned to the same version as the plugin manifest.
Pushing an authorized version tag runs the existing release workflow, validates
Python 3.9 syntax and package invariants, executes all tests, and publishes a
deterministic ZIP plus a portable SHA-256 file. Historical tags and artifacts are
not moved or replaced. Public GitHub distribution remains separate from OpenAI's
universal Plugins Directory.

## License

MIT
