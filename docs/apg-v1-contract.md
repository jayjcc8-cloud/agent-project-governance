# APG V1 core contract

## Product role

> APG is the execution-continuity and context-support layer for an agent working on real development tasks. It is not the project's source of truth, technical approver, drift detector, or knowledge-governance system.

Current product status:

```text
APG_V1_ACCEPTANCE=PENDING_THREE_REAL_PRODUCT_TASKS
```

Per-task `APG_ACCEPTANCE` evidence does not change this global status. A later V1 acceptance decision requires the completed three-task evidence window and separate authorization.

Repository state and the project's accepted Spec, Issue, PR, Git, and CI artifacts remain authoritative for product work and acceptance. APG may retain identifiers, hashes, a concise checkpoint, and current workspace observations. It does not replace or silently reinterpret those authorities.

## V1 core capabilities

APG V1 has four core capabilities:

1. **Context and task continuity.** Recover the current goal, completed work, verified facts, known blockers, and one next action without requiring a transcript replay or a second task plan.
2. **Task-source realignment.** Recheck declared task sources at explicit recovery points and direct the agent to reconcile when the current source no longer matches its checkpoint. APG does not decide the new product requirement or approve the resulting technical choice.
3. **Worktree boundary.** Report the current checkout, branch, HEAD, cleanliness, target branch occupancy, and known write boundaries without claiming a writer lock or changing the workspace.
4. **Recovery and budget continuity.** Preserve enough bounded handoff context—including used review or repair budget when relevant—to resume from the next useful action instead of repeating completed analysis or resetting an exhausted budget.

These capabilities are advisory. Their output is evidence for the agent and user; it is not product acceptance.

## Authority and acceptance boundary

| Concern | Authority |
|---|---|
| What the product should do | Accepted Spec, Issue, or equivalent project task source |
| What code and history exist | Repository and Git |
| What was proposed and reviewed | PR and review evidence |
| What passed required checks | CI and project-defined validation |
| How the agent continues the current task | APG recovery and boundary evidence |
| What was learned for later reuse | User-approved knowledge workflow outside APG runtime state |

`APG_ACCEPTANCE=PASS` requires evidence from a real product task that:

- APG solved or avoided at least one specific continuity or context problem; and
- APG did not become a blocker to product development.

A successful command, hook, checkpoint, resume, timing threshold, or injected source-change test is insufficient by itself. `APG_IMPACT` must name the product or execution consequence that actually occurred. Statements such as “improved governance quality” or “increased consistency” are not acceptable evidence.

## Non-goals

APG V1 does not:

- become a project fact source or duplicate Spec, Issue, PR, Git, or CI state;
- approve technical conclusions or product acceptance;
- assign product risk levels;
- provide general drift detection or make ADG/drift governance a success condition;
- require multi-agent review for every task;
- continuously curate Obsidian or automatically promote experience into a method, Skill, Spec, or other authority;
- add another planner, task database, hook bus, checkpoint store, orchestration layer, or automation framework.

ADG is not part of the active APG V1 product flow. Existing source-change checks and historical drift experiments may remain for compatibility and evidence, but they do not expand APG into drift governance.

## Existing workflow classification

The 0.5 package retains its five existing Skill entry points. V1 does not require deleting them or running them as a chain.

| Existing entry point | V1 classification |
|---|---|
| `context-governance` | Core carrier for continuity, explicit source realignment, recovery, and bounded handoff state |
| `eng-task-start` | Auxiliary intake helper that can supply current task-source and worktree evidence |
| `project-bootstrap` | Auxiliary, explicit setup and compatibility helper |
| `eng-bounded-delivery` | Auxiliary, explicit delivery guidance; not a V1 core capability |
| `eng-verified-closeout` | Auxiliary, explicit verification guidance; not a V1 core capability |
| Advisory hooks | Optional transport for already-bound recovery context; not a V1 acceptance condition |

Historical recovery-time comparisons, injected authority-change matrices, compatibility smokes, and the five-workflow 0.5 integration remain useful mechanism evidence. They are not the APG V1 product definition or its primary acceptance criteria.

## Knowledge boundary

Knowledge reuse is measured separately from APG acceptance:

- At task start, Codex performs a **Retrieval Checkpoint** using the project's approved knowledge route.
- After product acceptance, Codex performs a **Learning Checkpoint**.
- Codex may write to the Obsidian `收件箱` only when `NEW_KNOWLEDGE=YES` or `UPDATE_NEEDED=YES`, and only under the user's separate repository and knowledge-base authorization.
- APG does not continuously organize Obsidian. A low-frequency APG review may be started separately only after repeated reuse, a knowledge conflict, or a proposal to promote knowledge into a method, Skill, or Spec.

APG stores no knowledge-base contents in `.agent-runtime/` and does not treat a knowledge write as part of product acceptance.

## Initial evidence window

Use [the three-real-task value evaluation](apg-v1-three-task-value-evaluation.md) for the initial observation window. The three tasks should collectively cover ordinary continuation, a real task-source change, and a naturally occurring interruption or new-session recovery. Do not manufacture a failure solely to satisfy the matrix.

After the window, summarize which APG mechanisms demonstrated product value and which did not. This evidence window does not authorize deleting auxiliary capabilities, adding automation, or changing the V1 contract; any such decision is separate work requiring explicit authorization.
