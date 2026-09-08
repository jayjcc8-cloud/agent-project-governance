# Exceptional handoff — optional recovery cues

Use only for a real handoff/interruption. Skip fields already recoverable from
canonical sources; link those sources instead. This is not a required report.

- Current goal and authorization source:
- Repository, worktree, branch, HEAD, and observed time:
- Known uncommitted or untracked work to preserve:
- Previous writer stopped, active processes, or ownership unknown:
- Current Issue, PR, and normative sources:
- Verified facts and evidence links:
- Unverified assumptions or obsolete directions not to resume:
- Original blocker and review/repair rounds already used:
- Next bounded action:
- Merge, cleanup, and publish authorization, each considered separately:

When missing recovery context needs persistence, encode it with the existing checkpoint `summary`, `findings`,
`failed_attempts`, `next_action`, and structured `state` fields under the
`SESSION_HANDOFF` material event. Preserve inherited review/repair usage and send
only fields that changed; `resume` supplies the full canonical recovery view.
Do not paste full logs, private
paths, credentials, or hidden reasoning. The receiving actor must independently
verify mutable facts before writing; this handoff is not a writer lock.
