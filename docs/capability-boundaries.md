# Capability boundaries and production posture

Agent Project Governance is a local, advisory context-governance layer. It helps an agent remember where a bounded unit stopped and verify whether declared authorities changed. It is not a planning system or an autonomous orchestrator.

## What it can do

- Preview, check, and add only missing governance scaffolding with `project-bootstrap`; existing project-owned files are never overwritten.
- Create actor-owned local work units under `.agent-runtime/`, checkpoint a concise summary and one next action, resume them, migrate legacy state, and close completed units.
- Track project-relative file authorities and canonical public GitHub Issue/PR authorities by identifier and SHA-256 digest without storing their full contents.
- Detect declared authority drift during explicit `resume`, `evaluate`, `checkpoint`, or `close` operations. Remote checks require authenticated `gh` access.
- Return deterministic, evidence-linked advisory actions such as `RECONCILE`, `CLOSE`, `CHECKPOINT`, `WORKTREE`, or `CONTINUE` without executing them.
- Bind an explicit session/agent pair to one actor/work unit and keep main-task and subagent keys isolated.
- Provide read-only advisory hook context at session start, before compaction, and at stop events. Hooks always allow the host action to continue.

## What it cannot do

- It does not own WHAT: it does not create or edit constitutions, specifications, plans, canonical task lists, Issues, PRs, or ADR decisions.
- It does not own HOW: it does not run implementation, tests, converge, debugging, subagents, new tasks, worktrees, compaction, or handoffs.
- It does not infer actor ownership. A missing or ambiguous binding must be explicitly resolved or treated as unbound.
- It does not persist source contents, task copies, chat transcripts, evaluation results, or telemetry.
- It does not synchronize `.agent-runtime` across machines or recover state that was never checkpointed.
- GitHub Issue/PR `github-v2` authority digests cover review-thread resolution and status-check rollups, but not full comments, Actions logs, or arbitrary linked resources. Those require separate authoritative reads.
- A GitHub transport, permission, or bounded-pagination failure is reported as an unknown authority verdict, never as unchanged evidence. The CLI remains unable to prove freshness until a later explicit check succeeds.
- Advisory hooks do not make network requests and cannot prove remote authority freshness by themselves.
- It cannot guarantee faster recovery. The first controlled EA trial was accurate and isolated but failed the 50% recovery-time improvement threshold.
- It cannot hot-swap an already-running Codex task to a new plugin build. Tasks pin the cache path selected by their host; updates must add an immutable new build before retiring an old one. If an old path disappears unexpectedly, the POSIX Hook launcher fails open without blocking the host action.
- Windows core CLI support does not imply production-ready Windows hooks; Windows hooks remain experimental.

## Production posture

Current status: **developer preview; shadow/advisory production pilot only**.

Safe current use:

- run `project-bootstrap plan/check` in real repositories;
- checkpoint and strict-resume non-secret work units;
- use recommendations as human-reviewed evidence;
- keep hooks advisory and preserve existing Spec Kit/Superpowers/bridge ownership.

Do not yet use the plugin as:

- a deployment or merge gate;
- the sole source of current GitHub review/CI truth;
- an autonomous continuation or delegation controller;
- a substitute for project policy, code review, tests, backups, or access controls.

Promotion beyond shadow use requires repeatable binding resolution, a paired recovery trial meeting the declared effect threshold, an injected authority-drift trial, and the pinned Spec Kit/Superpowers/bridge handoff smoke.

For local plugin iteration, update the cachebuster and run `codex plugin add` directly. Do not run `codex plugin remove` first while any task may still reference the installed cache path. The package validator exercises both the installed adapter path and a simulated missing old path, but only the Codex host can determine when every active task has released a cache reference.
