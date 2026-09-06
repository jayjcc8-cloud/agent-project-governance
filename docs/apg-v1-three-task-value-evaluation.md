# APG V1 three-real-task value evaluation

Use this document once for the initial three-task observation window. Copy the per-task record for Task A, Task B, and Task C. Record concise evidence, not chat transcripts, secrets, or source-file contents.

The global product status remains:

```text
APG_V1_ACCEPTANCE=PENDING_THREE_REAL_PRODUCT_TASKS
```

The per-task `APG_ACCEPTANCE` field below records evidence for the window; it does not promote the global status.

The three tasks are an initial decision window, not a permanent governance requirement. Prefer work that already belongs on the product roadmap:

- **Task A — ordinary continuation:** observe whether APG helps or impedes normal product delivery.
- **Task B — real task-source change:** observe whether APG causes correct realignment to a changed Issue, Spec, or equivalent authority.
- **Task C — natural interruption or new session:** observe whether APG restores useful context without replaying completed work. Do not manufacture a disruption solely for the evaluation.

A single task may cover more than one condition. Complete the window with three materially different product tasks.

## Allowed values

Use `PASS | FAIL | NOT_OBSERVED` for capability observations, `LOW | MEDIUM | HIGH` for `APG_OVERHEAD`, and `YES | NO | UNKNOWN` for binary evidence unless a field explicitly asks for concrete text.

`APG_ACCEPTANCE=PASS` is allowed only when APG solved or avoided at least one specific continuity or context problem and did not block product development. Mechanism health alone never passes this gate.

## Per-task record

```text
APG_MODE=APG_ONLY

TASK_ID=
TASK_KIND=ORDINARY_CONTINUATION | TASK_SOURCE_CHANGE | NATURAL_RECOVERY
TASK_SOURCE=
TASK_SOURCE_CHANGED=YES | NO

RETRIEVAL_CHECKPOINT=

CONTEXT_RECOVERY=PASS | FAIL | NOT_OBSERVED
TASK_SOURCE_REALIGNMENT=PASS | FAIL | NOT_OBSERVED
WORKTREE_BOUNDARY=PASS | FAIL | NOT_OBSERVED
BUDGET_CONTINUITY=PASS | FAIL | NOT_OBSERVED

PRODUCT_TASK_RESULT=

APG_IMPACT=
APG_OVERHEAD=LOW | MEDIUM | HIGH
REWORK_AVOIDED=YES | NO | UNKNOWN
APG_BLOCKED_PRODUCT_WORK=YES | NO

LEARNING_CHECKPOINT=
FOUND=YES | NO
USED=YES | NO
UNDERSTOOD=YES | NO | UNKNOWN
UPDATE_NEEDED=YES | NO
NEW_KNOWLEDGE=YES | NO
IMPACT=

OBSIDIAN_INBOX_WRITE=YES | NO
OBSIDIAN_WRITE_REASON=NEW_KNOWLEDGE | UPDATE_NEEDED | NOT_APPLICABLE

ADG_USED=NO
DRIFT_GOVERNANCE_USED=NO

APG_ACCEPTANCE=PASS | FAIL
APG_ACCEPTANCE_EVIDENCE=
```

## Evidence rules

- `PRODUCT_TASK_RESULT` records the product outcome and its project-defined acceptance evidence. APG cannot supply or override that evidence.
- `APG_IMPACT` describes what concretely changed because APG was present. For example: “After a new session, the agent reused the already-verified API contract and continued with result restoration without repeating contract analysis.” Abstract claims such as “improved governance quality” are invalid.
- `APG_OVERHEAD` includes time and attention spent creating, recovering, or reconciling APG context. Precise token accounting is not required.
- `REWORK_AVOIDED=YES` requires a plausible, named duplicate action or wrong continuation that did not occur because of APG evidence. Use `UNKNOWN` when the counterfactual cannot be supported.
- `BUDGET_CONTINUITY` concerns preservation of bounded review or repair history and the next action. It does not claim exact token savings.
- `OBSIDIAN_INBOX_WRITE=YES` is permitted only when `NEW_KNOWLEDGE=YES` or `UPDATE_NEEDED=YES`. The write remains a separate Codex action under the knowledge-base authorization; APG does not perform it.
- `ADG_USED` and `DRIFT_GOVERNANCE_USED` remain `NO` throughout this V1 window.

## Three-task summary

| Field | Task A | Task B | Task C |
|---|---|---|---|
| Product task/result |  |  |  |
| Concrete APG impact |  |  |  |
| APG overhead |  |  |  |
| Rework avoided |  |  |  |
| Product work blocked |  |  |  |
| Task acceptance |  |  |  |

Coverage check:

```text
ORDINARY_CONTINUATION_OBSERVED=YES | NO
REAL_TASK_SOURCE_CHANGE_OBSERVED=YES | NO
NATURAL_RECOVERY_OBSERVED=YES | NO
```

If natural recovery does not occur during the window, record `NATURAL_RECOVERY_OBSERVED=NO`; do not create an artificial disaster. The final decision must state that this evidence remains missing.

## Final decision review

Answer these questions with references to the three task records:

1. Without APG, what specific problem would likely have recurred?
2. What overhead did APG add to avoid or contain those problems?
3. Which APG mechanisms never demonstrated product value?

Then record the evidence summary:

```text
APG_V1_EVIDENCE_REVIEW=COMPLETE | INCOMPLETE
DEMONSTRATED_VALUE=
NO_DEMONSTRATED_VALUE=
MISSING_EVIDENCE=
DECISION_EVIDENCE=
NEXT_DECISION=SEPARATE_AUTHORIZATION_REQUIRED
```

Completing this evidence review does not change `APG_V1_ACCEPTANCE=PENDING_THREE_REAL_PRODUCT_TASKS`. Do not delete auxiliary capabilities, restart ADG, add automation, or expand APG governance without separate authorization.
