# Primary review contract

- Task and acceptance source:
- Reviewed target, current exact HEAD, and directly relevant diff:
- Independent reviewer context and read-only permissions:
- Stage: `PRIMARY`, `ORIGINAL_BLOCKER_VERIFICATION`, or `REPLACEMENT_BLOCKER_VERIFICATION`:
- Writer-provided test commands and results to verify independently:

For `REPLACEMENT_BLOCKER_VERIFICATION`, record and verify:

- Original reviewer context is genuinely unavailable:
- This is one replacement reviewer continuing the same verification round and
  not a second review layer:
- Inherited review round and existing findings:
- Inherited repair budget and usage:
- Unchanged acceptance criteria, reviewed target, scope, and severity rules:
- Independent from the primary writer, read-only, and did not implement the
  current repair:

Same-reviewer continuity is preferred, not absolutely required. Replacement is
not allowed because a verdict is inconvenient, a blocker was found, or another
opinion is wanted. Original-reviewer unavailability alone does not require a
Product Owner exception.

Return exactly one verdict: `PASS` or `BLOCKED`.

A blocker must include the reachable file or behavior, a concrete reproduction or
trace, the violated acceptance criterion or direct risk, and the smallest useful
regression test or repair direction. Label other observations `NON-BLOCKING`.
Do not expand into future roadmap work or start another primary review.
Give the verdict independently for the current exact HEAD. A prior verdict is
invalid after any HEAD change.
