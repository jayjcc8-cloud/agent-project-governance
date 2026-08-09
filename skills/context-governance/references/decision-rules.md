# Deterministic Decision Rules

`evaluate` emits ordered advisory actions without a numeric health score.

| Priority | Evidence | Action |
|---:|---|---|
| 1 | Authority digest or existence changed | `RECONCILE` |
| 2 | `goal-changed` | `UPDATE_SPEC` |
| 3 | `implementation-drift` | `CONVERGE` |
| 4 | `feature-complete` | `CLOSE` |
| 5 | pre-compact, stop, or `context-noisy` | `CHECKPOINT` |
| 6 | `repeated-failure` | `DEBUG_REVIEW` |
| 7 | `durable-decision` | `PROMOTE_ADR` |
| 8 | `durable-agent-rule` | `PROMOTE_AGENTS` |
| 9 | `independent-work` | `WORKTREE` |
| 10 | `new-work-unit` | `NEW_THREAD` |
| 11 | `exploration-heavy` | `SUBAGENT` |
| 12 | `handoff-required` | `HANDOFF` |
| 13 | checkpoint followed by compaction | `COMPACT` |
| 14 | session start | `RESUME` |
| 15 | no trigger | `CONTINUE` |

Duplicate actions are collapsed. Every recommendation includes a stable `reason_code` and `blocking: false`. The first sorted action becomes `primary_action`.
