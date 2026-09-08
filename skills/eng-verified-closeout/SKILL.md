---
name: eng-verified-closeout
description: Check for reusable learning once after a real task is accepted. Write only new or corrected knowledge; use project-owned evidence for delivery, not a second closeout process.
---

# Task Completion — Conditional Learning

Use the project's acceptance evidence; RepoKeel does not run another acceptance
or approval stage. Perform this check once after task acceptance:

```text
NEW_KNOWLEDGE=YES|NO
UPDATE_NEEDED=YES|NO
```

Only `NEW_KNOWLEDGE=YES` or `UPDATE_NEEDED=YES` permits a write/update using the
user's authorized knowledge route. Otherwise `KNOWLEDGE_WRITE=SKIPPED` and stop.
Do not create a completion report, empty summary, knowledge report, context
manifest, or duplicate evidence package. Reference existing Issue/PR/Git/CI facts.
Do not create or close a runtime work unit for normal completion.

Refine, merge, promote, or convert knowledge into a method, skill, or spec only
when actual reuse in another real task supports it. Apparent importance alone is
not sufficient. Existing knowledge remains readable; no historical rewrite or
bulk migration is required.

Project-owned validation, CI, review, merge, release, and cleanup rules continue
to apply. This skill adds no mandatory validation suite or review round and grants
no merge, publication, installation, or deletion authority.

## Do not use when

- The real task has not yet been accepted/completed.
- This task's learning check has already been performed.
- There is no real task, only a routine request for status.
