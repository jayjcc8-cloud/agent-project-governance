# Capability boundaries and production posture

Agent Project Governance is a local, advisory execution-continuity and context-support layer. It helps an agent continue a real development task, realign to a changed declared task source, preserve worktree boundaries, and recover bounded context. It is not a project fact source, technical approver, drift detector, knowledge-governance system, planning system, or autonomous orchestrator.

The normative product boundary is the [APG V1 core contract](apg-v1-contract.md). Existing 0.5 workflow entry points and historic experiments remain available, but auxiliary mechanism breadth is not the V1 product definition.

## What it can do

- Preview, check, and add only profile-approved missing governance scaffolding with `project-bootstrap`; existing project-owned files are never overwritten. The default `existing-project` profile treats unselected framework dependencies and ADR conventions as not applicable.
- Inspect local Git/worktree task-intake evidence without creating runtime state, fetching, checking out, cleaning, or claiming exclusive writer ownership.
- Create actor-owned local work units under `.agent-runtime/`, checkpoint a concise summary and one next action, resume them, migrate legacy state, and close completed units.
- Carry a short handoff in existing checkpoint fields, including known dirty work, original blockers, used review rounds, verified facts, and one next bounded action.
- Provide explicit-invocation guidance for one bounded implementation/review loop and evidence-based closeout without adding another planner, task store, CI engine, or dispatcher.
- Track project-relative file authorities and canonical public GitHub Issue/PR authorities by identifier and SHA-256 digest without storing their full contents.
- Detect declared authority drift during explicit `resume`, `evaluate`, `checkpoint`, or `close` operations. Remote checks require authenticated `gh` access.
- Return deterministic, evidence-linked advisory actions such as `RECONCILE`, `CLOSE`, `CHECKPOINT`, `WORKTREE`, or `CONTINUE` without executing them.
- Bind an explicit session/agent pair to one actor/work unit and keep main-task and subagent keys isolated.
- Provide read-only advisory hook context at session start, before compaction, and at stop events. Hooks always allow the host action to continue.

These mechanisms support four V1 outcomes: context/task continuity, task-source realignment, worktree boundaries, and recovery/budget continuity. Bootstrap, delivery, closeout, hook transport, timing measurements, and injected change matrices are auxiliary support or historical evidence.

## What it cannot do

- It does not own WHAT: it does not create or edit constitutions, specifications, plans, canonical task lists, Issues, PRs, or ADR decisions.
- It does not approve technical conclusions, product acceptance, or product risk levels.
- It does not own HOW: it does not run implementation, tests, converge, debugging, subagents, new tasks, worktrees, compaction, or handoffs.
- It does not infer actor ownership. A missing or ambiguous binding must be explicitly resolved or treated as unbound.
- It does not persist source contents, task copies, chat transcripts, evaluation results, or telemetry.
- It cannot prove that a local checkout has one writer. Workspace snapshots are observations, not locks, and local `origin/*` refs do not prove current remote state.
- It does not synchronize `.agent-runtime` across machines or recover state that was never checkpointed.
- GitHub Issue/PR `github-v2` authority digests cover review-thread resolution and status-check rollups, but not full comments, Actions logs, or arbitrary linked resources. Those require separate authoritative reads.
- A GitHub transport, permission, or bounded-pagination failure is reported as an unknown authority verdict, never as unchanged evidence. The CLI remains unable to prove freshness until a later explicit check succeeds.
- Advisory hooks do not make network requests and cannot prove remote authority freshness by themselves.
- It cannot guarantee faster recovery in every environment. The v0.4 forward test met the predeclared original-baseline threshold with a 53.412% median improvement, but the same-day comparison improved 39.175% and one remote-unavailable tail sample required a safe fallback.
- It cannot hot-swap an already-running Codex task to a new plugin build. Tasks pin the cache path selected by their host, and Codex CLI `plugin add` may garbage-collect older cache directories. If an old path disappears unexpectedly, the POSIX Hook launcher fails open without blocking the host action, but the project cannot guarantee uninterrupted Hook execution during an update.
- Windows core CLI support does not imply production-ready Windows hooks; Windows hooks remain experimental.
- It does not provide general drift governance, depend on ADG, continuously manage Obsidian, or automatically promote knowledge into a method, Skill, or Spec.

## Production posture

Current status: **unreleased 0.5 developer-preview candidate; shadow/advisory production pilot only**.

Safe current use:

- run `project-bootstrap plan/check` in real repositories;
- explicitly invoke `eng-task-start`, `eng-bounded-delivery`, or `eng-verified-closeout` for a scoped human-reviewed task;
- checkpoint and strict-resume non-secret work units;
- use recommendations as human-reviewed evidence;
- keep hooks advisory and preserve existing Spec Kit/Superpowers/bridge ownership.

Do not yet use the plugin as:

- a deployment or merge gate;
- the sole source of current GitHub review/CI truth;
- an autonomous continuation or delegation controller;
- an automatic trigger chain requiring every task to run all five skills;
- a substitute for project policy, code review, tests, backups, or access controls.

Repeatable binding resolution, the predeclared original-baseline recovery threshold, the injected authority-change matrix, and the pinned Spec Kit/Superpowers/bridge handoff smoke passed on 2026-08-20. These results support a limited human-reviewed advisory pilot and remain historical mechanism evidence. They do not establish APG V1 product value.

The current status is `APG_V1_ACCEPTANCE=PENDING_THREE_REAL_PRODUCT_TASKS`. V1 evidence is collected on three real product tasks with [the value evaluation template](apg-v1-three-task-value-evaluation.md). A per-task pass requires one concrete continuity/context problem solved or avoided and no product-development blockage; it does not promote the global status. ADG or drift governance is not part of the evaluation. Promotion to blocking control or autonomous continuation is outside the V1 contract rather than a presumed next maturity step.

For local plugin iteration, wait until every task using the installed plugin has ended before running `codex plugin add`. Do not rely on cachebuster SemVer alone to retain old directories, and never run `codex plugin remove` while a task may reference an installed path. The package validator exercises both the installed adapter path and a simulated missing old path, but only the Codex host can determine when every active task has released a cache reference.
