# RepoKeel V1 Friction Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the two evidence-confirmed RepoKeel V1 friction sources while preserving reviewer independence, exact-HEAD validity, finite repair limits, and recoverable canonical work-unit state.

**Architecture:** Keep the existing `eng-bounded-delivery` contract and `.agent-runtime` work-unit store. Reviewer replacement remains a contract-only continuation of the same review/repair round; checkpoint updates gain material-event labels, a small structured state map, no-op detection before evidence refresh, and deterministic delta output while `resume` remains the full recovery snapshot.

**Tech Stack:** Markdown skill contracts, Python 3.9-compatible standard library, `unittest`, existing atomic JSON state writer.

## Global Constraints

- Historical `REPOKEEL_PRODUCT_VALUE=PARTIAL` and `REPOKEEL_V1_ACCEPTANCE=PASS` are immutable.
- Modify only reviewer continuity, work-unit checkpoint/state semantics, and directly affected tests/docs.
- Do not add a reviewer registry, service, workflow engine, state database, event bus, Hook framework, automation, drift framework, approval layer, hierarchy, cleanup, or unrelated refactor.
- One writer, at most one active independent reviewer, one repair cycle, one Issue, one branch, one worktree, and one final PR.
- `MERGE_AUTHORIZED=NO`; implementation and review may complete, but merge waits for Human Product Owner authorization.
- Preserve schema `0.4` compatibility, actor isolation, atomic writes, authority `matched|changed|unknown`, exact-HEAD invalidation, P0/P1 blocking, P2/P3 backlog treatment, Retrieval/Learning checkpoints, and STOP behavior.

---

### Task 1: Reviewer continuity replacement contract

**Files:**
- Modify: `skills/eng-bounded-delivery/SKILL.md`
- Modify: `skills/eng-bounded-delivery/assets/review.md`
- Modify: `tests/test_skill_contracts.py`
- Modify: `docs/capability-boundaries.md`
- Create: `docs/superpowers/plans/2026-09-06-repokeel-v1-friction-simplification.md`

**Interfaces:**
- Consumes: the existing single primary review and one concentrated repair budget.
- Produces: a documented `REPLACEMENT_BLOCKER_VERIFICATION` path that preserves the same round, findings, acceptance target, scope, severity rules, reviewed target, and repair usage.

- [ ] **Step 1: Add failing contract tests**

Assert that the delivery skill and review template require same-reviewer preference, genuine original-context unavailability, exactly one read-only independent replacement, inherited round/budget/findings/acceptance/scope/severity/target, no current-repair implementation, no second review layer, and a fresh verdict on the exact current HEAD.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 -m unittest tests.test_skill_contracts -v`

Expected: FAIL because the current template does not define replacement stage and inheritance fields.

- [ ] **Step 3: Make the minimum contract changes**

Extend the existing step 6 and `review.md`; do not add code, identity storage, approvals, reviewers, or workflow stages beyond the one replacement continuation.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `python3 -m unittest tests.test_skill_contracts -v`

Expected: PASS.

- [ ] **Step 5: Commit logical change 1**

Commit message: `fix: simplify reviewer continuity fallback`

---

### Task 2: Event-driven checkpoint delta semantics

**Files:**
- Modify: `skills/context-governance/scripts/work_unit.py`
- Modify: `tests/test_work_unit.py`
- Modify: `skills/context-governance/SKILL.md`
- Modify: `skills/context-governance/references/state-schema.md`
- Modify: `skills/context-governance/references/decision-rules.md` only if rule text must reflect tested behavior
- Modify: `docs/capability-boundaries.md`

**Interfaces:**
- Consumes: `checkpoint --work-unit ID --actor ID` plus existing summary, next action, finding, failed-attempt, and authority state.
- Produces: optional `--event MATERIAL_EVENT` and repeatable `--state KEY=VALUE`; checkpoint output `{event, state_changed, state_written, evidence_reread, full_snapshot, delta, revision, checkpoint_sequence}`.
- Preserves: legacy checkpoint invocations by treating an omitted event as `SESSION_HANDOFF`; `resume` continues to return the full canonical checkpoint and current recovery evidence.

- [ ] **Step 1: Add failing state-delta tests**

Cover HEAD, review verdict, finding count, repair usage, unchanged input, matched unchanged evidence, recovery full snapshot, post-recovery no-op, authority-change refresh, legacy checkpoint compatibility, and concurrent identical checkpoints.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_work_unit -v`

Expected: FAIL on missing `--event`/`--state`, full-state checkpoint output, and redundant second write.

- [ ] **Step 3: Implement parsing and deterministic delta helpers**

Add the exact material-event choices from Issue 26, bounded `KEY=VALUE` parsing, prior-state merge, and a stable field-sorted delta. Store the merged map only inside the existing checkpoint object.

- [ ] **Step 4: Implement gated checkpoint mutation**

Build the candidate checkpoint before evidence access; refresh authority evidence only for HEAD/base/authority/finding/review/recovery/handoff events; skip the write when neither canonical checkpoint content nor authority digest changed; otherwise retain the existing lock, sequence, revision, `fsync`, and atomic replacement behavior.

- [ ] **Step 5: Emit delta-only checkpoint output**

Never include the full state in checkpoint output. Emit an empty delta with `state_written=false` for a no-op. Keep `resume` as the explicit full canonical recovery operation.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `python3 -m unittest tests.test_work_unit -v`

Expected: PASS.

- [ ] **Step 7: Update direct documentation**

Document event-driven calls, optional inherited checkpoint fields, structured canonical state, no-op/evidence rules, delta output, recovery exception, and legacy state compatibility without changing frozen V1 conclusions.

- [ ] **Step 8: Run directly affected regression**

Run: `python3 -m unittest tests.test_work_unit tests.test_hooks tests.test_skill_contracts tests.test_delivery_tools -v`

Expected: PASS.

- [ ] **Step 9: Commit logical change 2**

Commit message: `fix: make work-unit updates event-driven`

---

### Task 3: Candidate validation and bounded independent review

**Files:**
- Verify only; repair directly affected files only if one P0/P1 is reproduced.

**Interfaces:**
- Consumes: exact branch HEAD after Tasks 1-2.
- Produces: focused/full/package evidence and one independent read-only reviewer verdict tied to that exact HEAD.

- [ ] **Step 1: Run full local validation**

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 scripts/validate_package.py`

Expected: 0 failures and package `valid: true`.

- [ ] **Step 2: Verify clean exact-HEAD candidate and open one PR**

Record branch HEAD, clean status, diff scope, and create one PR linked to Issue 26 without merging.

- [ ] **Step 3: Run one independent read-only review**

Require the reviewer to verify replacement independence/budget continuity/exact HEAD and event detection/delta/recovery/no-op behavior. P0/P1 blocks; P2/P3 is backlog.

- [ ] **Step 4: Apply at most one concentrated repair if required**

If the HEAD changes, rerun focused/full/package validation and obtain a fresh exact-HEAD verdict from the same reviewer, or one formal replacement only if that reviewer context is genuinely unavailable.

- [ ] **Step 5: Stop at merge authorization gate**

Report `MERGE_RECOMMENDATION=YES` only if all gates pass. Do not merge until `MERGE_AUTHORIZED=YES` is explicitly supplied by the Human Product Owner.
