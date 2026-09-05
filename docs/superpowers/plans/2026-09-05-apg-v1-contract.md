# APG V1 Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reclassify APG around a four-capability V1 continuity contract and add a three-real-task product-value acceptance template without changing runtime behavior.

**Architecture:** Keep repository, GitHub, specifications, Issues, PRs, and CI authoritative. Define APG as an advisory execution-continuity layer, retain the five existing skills as compatible core or auxiliary entry points, and move historic drift and timing experiments outside V1 acceptance. Keep knowledge capture explicitly outside APG runtime ownership.

**Tech Stack:** Markdown documentation and existing JSON plugin metadata; Python unittest and repository package validation for verification.

## Global Constraints

- Modify only the APG repository.
- Do not change ADG or EA.
- Do not delete auxiliary skills, historic workflows, drift implementation, or compatibility behavior.
- Do not add governance layers, automation frameworks, knowledge-base integration, or migrations.
- Record implementation conflicts as findings instead of expanding scope.

---

### Task 1: APG V1 core contract and legacy reclassification

**Files:**
- Create: `docs/apg-v1-contract.md`
- Modify: `README.md`
- Modify: `docs/capability-boundaries.md`
- Modify: `.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: the user-approved four-capability V1 definition and existing five-skill package surface.
- Produces: one canonical contract linked from repository entry points, with core and auxiliary capabilities distinguished without runtime deletion.

- [x] **Step 1:** Write the normative V1 role, authority boundaries, four core capabilities, non-goals, auxiliary-skill classification, ADG exclusion, and weak knowledge checkpoint boundary in `docs/apg-v1-contract.md`.
- [x] **Step 2:** Revise README and capability-boundary language so recovery timing and drift experiments remain historical evidence rather than V1 success criteria.
- [x] **Step 3:** Revise plugin descriptions to advertise continuity and recovery as the product core while preserving the existing five skill entry points.

### Task 2: Three-real-task value acceptance template

**Files:**
- Create: `docs/apg-v1-three-task-value-evaluation.md`
- Modify: `docs/trials.md`

**Interfaces:**
- Consumes: the V1 acceptance rule and approved APG and knowledge fields.
- Produces: one reusable record for Task A, Task B, and Task C plus a final retain/remove/automate decision review.

- [x] **Step 1:** Add per-task fields for continuity, product result, concrete APG impact, overhead, avoided rework, and separate knowledge reuse evidence.
- [x] **Step 2:** Encode that `APG_ACCEPTANCE=PASS` requires a concrete continuity/context problem solved or avoided and no product-development blockage.
- [x] **Step 3:** Add three-task coverage guidance and final questions about recurrence without APG, overhead, and mechanisms with no demonstrated value.
- [x] **Step 4:** Reclassify prior trial records in `docs/trials.md` as historical mechanism evidence and link the new V1 value template.

### Task 3: Verification and bounded closeout

**Files:**
- Verify: all modified documentation and `.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: a validated documentation-only candidate and an explicit finding list for any runtime conflict.

- [x] **Step 1:** Search for stale statements that still make five workflows, drift governance, or recovery-time thresholds the V1 product definition.
- [x] **Step 2:** Validate JSON syntax and local Markdown links.
- [x] **Step 3:** Run `PYTHONPYCACHEPREFIX=/tmp/apg-v1-final-pycache python3 -m unittest discover -s tests -v`; expect `Ran 75 tests` and `OK`.
- [x] **Step 4:** Run `python3 scripts/validate_package.py`; expect `package validation: PASS`.
- [x] **Step 5:** Inspect the final diff and commit only the bounded documentation and metadata changes on `codex/apg-v1-contract`.
