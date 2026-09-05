---
name: eng-verified-closeout
description: Explicitly verify the current candidate, CI, distributable artifact, merge, and authorized cleanup before making completion claims. Use for closeout, not to grant merge, publish, deletion, or installation authority.
---

# Verified Engineering Closeout

Keep `implemented`, `locally tested`, `reviewed`, `CI passed`, `merged`, and
`merged-main verified` as distinct facts.

## Workflow

1. Read the repository's canonical validation entry points and current candidate
   HEAD. Record whether the working tree has uncommitted changes; dirty-tree tests
   do not prove a clean commit.
2. Run the necessary focused checks, then the complete required suite. Do not use
   an old SHA, skipped job, configuration value, or source-only test as evidence
   for the current candidate.
3. When distribution is in scope, build the current artifact and exercise it from
   outside the source checkout, including packaged references and shared helpers.
4. For CI, verify the event, head SHA, required jobs, and their actual conclusions.
   Remote unavailability is unknown, not passed or drifted.
5. Confirm the independent review verdict and any original-blocker verification.
   Candidate changes invalidate only the evidence affected by those changes.
6. Merge only with explicit authorization and when acceptance, current CI, and
   review are all passing. Re-read the PR head immediately before merge and use an
   expected-head guard when supported. Never force push or bypass checks.
7. After merge, verify the actual target-branch SHA and required main checks. If
   they remain pending, report pending and preserve the exact run identifier.
8. Clean only this task's explicitly authorized branch, worktree, or temporary
   artifacts after checking PR state, final reviewed head, later unique commits,
   dirty/untracked work, and ignored data. Squash merges require PR plus patch/tree
   evidence; `git branch --merged` alone is insufficient.

A local `work-unit close` ends derived memory only; it is not product acceptance.
The skill never publishes, installs a plugin, changes hooks, or begins a successor.

## Do not use when

- No completion, merge, evidence, packaging, or cleanup claim is being evaluated.
- The user asks only for implementation progress and the candidate is not ready.
- Required authority is absent; report the missing precondition instead.
- The next roadmap item has not been separately authorized.
