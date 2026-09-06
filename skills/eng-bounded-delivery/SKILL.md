---
name: eng-bounded-delivery
description: Explicitly implement or review one authorized software increment with a bounded primary-review and repair loop. Use for scoped delivery, not for repository-wide audits, a new planning system, or automatic follow-on work.
---

# Bounded Engineering Delivery

Use the project's current Issue, specification, tests, CI, and engineering tools.
Do not create another task plan, review state machine, dispatcher, or ledger.

## Delivery

1. Restate one acceptance goal, scope, non-goals, current writer, and stopping
   conditions from the existing authority. Do not expand a task to its roadmap.
2. Add the smallest failing behavior test before a behavior change, then make the
   minimum implementation pass. Focused tests, debugging, formatting, and
   checkpoint commits are normal work, not formal review rounds.
3. Keep one writer. Use scripts and CI for deterministic facts. Do not duplicate
   existing TDD, debugger, worktree, or orchestration engines inside this skill.
4. After the complete candidate is locally verified, request one independent,
   read-only primary review using [the review contract](assets/review.md).
5. A blocker must identify a reachable path, concrete reproduction or trace, the
   violated acceptance criterion or direct risk, and a minimal test or fix.
6. If blocked, make one concentrated repair for all qualifying blockers. The
   same reviewer is preferred for one verification limited to those blockers and
   direct regressions. When that reviewer's context is genuinely unavailable,
   one replacement reviewer may continue the same verification round without a
   Product Owner exception. The replacement inherits the review round, repair
   budget, existing findings, acceptance criteria, reviewed target, scope, and
   severity rules; none is reset. The replacement must be independent from the
   writer, must have read-only permissions, and must confirm that they did not
   implement the current repair. This is not a second review layer, and at most
   one independent reviewer may be active. A replacement is not allowed merely
   because the existing verdict is inconvenient or blocking.
7. If an original blocker remains, keep the candidate unmerged. Budget exhaustion
   never converts failure into approval. Record non-catastrophic out-of-scope
   discoveries in the existing backlog without starting them.

Every verdict applies only to the current exact HEAD. Any HEAD change invalidates
the earlier verdict and requires fresh verification; reviewer replacement never
permits a verdict for an older commit to be reused.

Authorization to implement does not imply permission to merge, publish, delete,
install, or change host settings. Domain-specific patterns are available only
when directly relevant in [domain patterns](references/domain-patterns.md).

## Do not use when

- The user requested only an explanation, plan, or read-only status report.
- There is no authorized implementation increment or acceptance source.
- The request is to audit an entire repository or invent a general evaluator.
- A completed task would be followed only because it appears on a roadmap.
