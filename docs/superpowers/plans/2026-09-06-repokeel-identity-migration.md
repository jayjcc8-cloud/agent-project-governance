# RepoKeel Product Identity Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the unreleased v0.5.0 product, plugin, marketplace, release package, repository, and public documentation from Agent Project Governance to RepoKeel while preserving legacy project state, schemas, Skill IDs, and historical APG evidence.

**Architecture:** Separate mutable product/package identity from stable runtime protocol identity. Deliver the code and content migration in PR 1, rename the GitHub repository as a platform action, and canonicalize URLs in a narrow PR 2 before running fresh-install and real-v0.4.1 migration smokes.

**Tech Stack:** JSON plugin manifests, Python 3.9-compatible validation and packaging scripts, `unittest`, GitHub Actions, GitHub CLI/API, Codex plugin CLI.

## Global Constraints

- `PRODUCT_NAME=RepoKeel`; `PRODUCT_SLUG=repokeel`.
- `CATEGORY=Persistent project state for AI coding agents.`
- `CORE_PROMISE=Preserve the state of the work, not the state of the conversation.`
- v0.4.x and earlier remain the historical APG line; unreleased v0.5.0 starts RepoKeel.
- Preserve `.agent-runtime`, existing work-unit formats, authority semantics, legacy schema IDs, `APG_*` historical markers, and all five existing Skill IDs.
- Do not relabel historical APG contracts, trial records, releases, Issues, PRs, or commits.
- `PRODUCT_FUNCTION_CHANGE=NO`; `SKILL_API_RENAME=NO`; `STATE_SCHEMA_MIGRATION=NO`.
- `TAG=NO`; `RELEASE=NO`; `ORGANIZATION_TRANSFER=NO`; local checkout rename is out of scope.
- The old repository slug is permanently reserved after rename and must not be recreated.

---

### Task 1: Lock identity and legacy-state contracts with failing tests

**Files:**
- Create: `tests/test_identity_migration.py`
- Modify: `tests/test_delivery_tools.py`
- Preserve: `docs/apg-v1-contract.md`
- Preserve: `docs/apg-v1-three-task-value-evaluation.md`

**Interfaces:**
- Consumes: current manifest, marketplace, release builder, workspace snapshot, and work-unit CLI.
- Produces: executable identity, package, history, and legacy-state invariants for later tasks.

- [ ] **Step 1: Record immutable historical file hashes**

Run:

```bash
shasum -a 256 docs/apg-v1-contract.md docs/apg-v1-three-task-value-evaluation.md
```

Expected: two hashes saved in the task evidence and unchanged through PR 1.

- [ ] **Step 2: Add failing new-identity tests**

Add assertions that load `.codex-plugin/plugin.json` and
`.agents/plugins/marketplace.json` and require:

```python
self.assertEqual(manifest["name"], "repokeel")
self.assertEqual(manifest["interface"]["displayName"], "RepoKeel")
self.assertEqual(marketplace["name"], "repokeel")
self.assertEqual(marketplace["plugins"][0]["name"], "repokeel")
```

Add an archive assertion requiring every member to begin with `repokeel/` and
tests requiring the release workflow basename `repokeel-${GITHUB_REF_NAME}.zip`.

- [ ] **Step 3: Add failing legacy compatibility tests**

Create a temporary Git repository and legacy `.agent-runtime` fixture through
the current `work_unit.py` CLI. Assert that `resume`, `inspect-workspace`,
`evaluate`, and `resolve-binding` succeed under the candidate and that:

```python
self.assertEqual(snapshot["schema"], "agent-project-governance.workspace-snapshot.v1")
self.assertEqual(before_state_bytes, after_state_bytes)
self.assertEqual(before_state_hash, after_state_hash)
```

Exercise read-only commands only for the no-rewrite assertion. Add explicit
checks that the five Skill directory names are unchanged and the two historical
APG documents still exist.

- [ ] **Step 4: Run the focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_identity_migration tests.test_delivery_tools -v
```

Expected: failures name the old package identity and archive prefix; legacy
state assertions pass or expose a real compatibility defect before migration.

- [ ] **Step 5: Commit the contract tests**

```bash
git add tests/test_identity_migration.py tests/test_delivery_tools.py
git commit -m "test: define RepoKeel identity compatibility"
```

---

### Task 2: Migrate manifest, marketplace, release, and validator identity

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `.github/workflows/release.yml`
- Modify: `scripts/package_release.py`
- Modify: `scripts/validate_package.py`

**Interfaces:**
- Consumes: Task 1's identity and archive tests.
- Produces: `PLUGIN_NAME="repokeel"`, `RELEASE_PREFIX="repokeel"`, and explicit `LEGACY_SCHEMA_PREFIX="agent-project-governance"` constants.

- [ ] **Step 1: Change the plugin and marketplace identity**

Set manifest `name` to `repokeel`, author/developer to `RepoKeel contributors`,
display name to `RepoKeel`, and describe persistent project state, recovery,
task-source realignment, Git/worktree evidence, and safe continuation. Set the
marketplace and its single plugin entry to `repokeel`. Keep old repository URLs
until PR 2.

- [ ] **Step 2: Change release identity**

Define `RELEASE_PREFIX = "repokeel"` in `scripts/package_release.py` and use it
for the ZIP root. Update `.github/workflows/release.yml` so the artifact and
checksum names are `repokeel-${GITHUB_REF_NAME}.zip` and
`repokeel-${GITHUB_REF_NAME}.zip.sha256`.

- [ ] **Step 3: Separate product and legacy schema constants**

In `scripts/validate_package.py`, use:

```python
PLUGIN_NAME = "repokeel"
RELEASE_PREFIX = "repokeel"
LEGACY_SCHEMA_PREFIX = "agent-project-governance"
WORKSPACE_SCHEMA = f"{LEGACY_SCHEMA_PREFIX}.workspace-snapshot.v1"
```

Use `PLUGIN_NAME` for manifest and marketplace checks, `RELEASE_PREFIX` for
workflow/archive checks, and `WORKSPACE_SCHEMA` only for the preserved protocol
assertion. Do not modify the snapshot producer's schema string.

- [ ] **Step 4: Run focused tests and verify GREEN**

```bash
python3 -m unittest tests.test_identity_migration tests.test_delivery_tools -v
python3 scripts/validate_package.py
```

Expected: focused tests pass; validation reports `plugin: repokeel`,
`version: 0.5.0`, and `valid: true`.

- [ ] **Step 5: Commit package identity**

```bash
git add .codex-plugin/plugin.json .agents/plugins/marketplace.json .github/workflows/release.yml scripts/package_release.py scripts/validate_package.py
git commit -m "chore: migrate package identity to RepoKeel"
```

---

### Task 3: Productize current documentation without rewriting history

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SUPPORT.md`
- Modify: `SECURITY.md`
- Modify: `CODE_OF_CONDUCT.md`
- Modify: `LICENSE`
- Modify: `docs/README.md`
- Modify: `docs/capability-boundaries.md`
- Create: `docs/migrating-from-apg.md`
- Preserve: `docs/apg-v1-contract.md`
- Preserve: `docs/apg-v1-three-task-value-evaluation.md`
- Preserve: `docs/trial-records/**`
- Preserve: `docs/trials.md`

**Interfaces:**
- Consumes: the approved product copy and compatibility boundary.
- Produces: current RepoKeel public surfaces plus a bounded APG migration guide.

- [ ] **Step 1: Rewrite the README first screen and current product language**

Use the exact name, category, and core promise from Global Constraints. Explain
that sessions are temporary but project state is not. Present the five stable
Skill IDs as RepoKeel workflows, and state accurately:

```text
Current product: RepoKeel
Current candidate: v0.5.0
Latest published legacy preview: APG v0.4.1
V1 acceptance: pending against the frozen APG V1 contract established before the rename.
```

Keep old-slug badges, links, and install commands for the brief pre-rename PR 1
window. Do not call the historical contract a RepoKeel V1 contract.

- [ ] **Step 2: Update current community and product-boundary docs**

Change present-tense product references to RepoKeel and retain genuine domain
uses of “governance”, including governance authority and policy. Update the
copyright holder to `RepoKeel contributors`.

- [ ] **Step 3: Add the migration guide**

`docs/migrating-from-apg.md` must distinguish:

```text
v0.4.x and earlier: Agent Project Governance / agent-project-governance
v0.5.0 and later: RepoKeel / repokeel
```

Document explicit old-plugin removal/new-plugin installation, project-state
compatibility, preserved schemas and Skill IDs, no automatic plugin identity
upgrade, no runtime-state rewrite, and the permanently reserved old repo slug.

- [ ] **Step 4: Audit classifications instead of replacing all strings**

Run:

```bash
rg -n -I -e 'Agent Project Governance' -e 'agent-project-governance' -e '\bAPG\b' -e 'APG_' -e 'apg-' -e 'governance' .
```

Classify every remaining hit as `STABLE_PROTOCOL_ID`, `HISTORICAL_EVIDENCE`,
`DOMAIN_TERMINOLOGY`, or an intentionally temporary old repository URL.

- [ ] **Step 5: Prove history remained unchanged**

Re-run the two historical SHA-256 hashes and verify no diff under
`docs/trial-records/`, the two APG V1 documents, or `docs/trials.md`.

- [ ] **Step 6: Run all tests and commit docs**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
git diff --check
git add README.md CONTRIBUTING.md SUPPORT.md SECURITY.md CODE_OF_CONDUCT.md LICENSE docs
git commit -m "docs: introduce RepoKeel product identity"
```

Expected: all tests and package validation pass; preserved history has no diff.

---

### Task 4: Deliver PR 1 through independent review

**Files:**
- Review: all changes from frozen base through the PR head.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: merged `main` whose code identity is RepoKeel while the GitHub slug is temporarily unchanged.

- [ ] **Step 1: Push and open PR 1**

Push `codex/22-repokeel-identity-migration` and open
`chore: migrate APG product identity to RepoKeel`, linked to #22. State the
breaking plugin-identity boundary and `TAG=NO`, `RELEASE=NO`.

- [ ] **Step 2: Run independent review**

The reviewer must check current product branding, package identity, legacy
state/schema compatibility, historical evidence preservation, and absence of
product behavior changes. Required result:

```text
INDEPENDENT_REVIEW=PASS
BLOCKING_FINDINGS=0
```

- [ ] **Step 3: Verify exact-head CI and squash-merge**

Require every configured CI check at the reviewed head to pass and every review
thread to be resolved. Squash-merge with expected-head protection. Then run
merged-main tests, package validation, and CI before the platform rename.

---

### Task 5: Rename and verify the GitHub repository

**Files:**
- Platform metadata only; no source-file edit.

**Interfaces:**
- Consumes: merged PR 1.
- Produces: `jayjcc8-cloud/repokeel`, a working old-slug redirect, preserved GitHub state, and updated local remotes/topics.

- [ ] **Step 1: Capture pre-rename metadata**

Record repository ID, Issues and Discussions availability, default branch,
rulesets, Actions, Releases, open #22, and tag/release list. Confirm no active
task depends on changing the local checkout path.

- [ ] **Step 2: Rename the repository**

Use the GitHub repository settings/API to rename only the repository to
`repokeel`. Do not create an organization and do not recreate the old slug.

- [ ] **Step 3: Update remotes and topics**

Set all registered worktree remotes to the canonical RepoKeel URL. Replace topic
`agent-governance` with `project-state`; retain `ai-agents`, `coding-agents`,
`ai-engineering`, `context-management`, `developer-tools`, `codex`, and `python`.
Set the description to `Persistent project state for AI coding agents.`

- [ ] **Step 4: Verify preservation and redirect**

Verify repository ID is unchanged, #22 is open, Discussions/rulesets/Actions/
Releases/default branch remain intact, fetch/push use the new remote, and an HTTP
request to the old repository URL redirects to the new canonical URL.

---

### Task 6: Canonicalize RepoKeel URLs in PR 2

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SUPPORT.md`
- Modify: `SECURITY.md`
- Modify: `CODE_OF_CONDUCT.md`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `.github/ISSUE_TEMPLATE/config.yml`

**Interfaces:**
- Consumes: renamed GitHub repository and redirect verification.
- Produces: canonical `github.com/jayjcc8-cloud/repokeel` URLs, metadata, badges, and install commands.

- [ ] **Step 1: Create a fresh branch from renamed `origin/main`**

Create `docs/22-repokeel-canonical-urls` in a clean isolated worktree. Do not
reuse PR 1's branch.

- [ ] **Step 2: Replace only current canonical URLs**

Update badges, support/security links, manifest homepage/repository, marketplace
source URL, Issue Form contact links, and Quick Start:

```bash
codex plugin marketplace add jayjcc8-cloud/repokeel --ref v0.5.0
codex plugin add repokeel@repokeel
```

Do not edit historical evidence solely to replace old URLs.

- [ ] **Step 3: Validate, review, and merge PR 2**

Run all tests and package validation, independently review the small URL-only
diff, require PR CI at the reviewed head, squash-merge with expected-head
protection, and require merged-main CI.

---

### Task 7: Run installed-host migration gates

**Files:**
- No repository source changes unless a smoke exposes a defect, in which case reopen the relevant PR cycle.
- Evidence: comment on GitHub Issue #22.

**Interfaces:**
- Consumes: merged canonical RepoKeel `main`, published legacy APG `v0.4.1`, and current supported Codex plugin lifecycle commands.
- Produces: evidence for fresh install and APG-to-RepoKeel state compatibility.

- [ ] **Step 1: Build and validate the candidate outside the checkout**

Create a deterministic `repokeel-v0.5.0.zip`, validate the extracted package,
and use isolated temporary host/project directories. Do not publish it.

- [ ] **Step 2: Run the fresh RepoKeel path**

With no APG installation, install the RepoKeel candidate through the supported
local plugin flow, then bootstrap, initialize/checkpoint a work unit, resume it,
and validate the installed package. Require `FRESH_INSTALL_SMOKE=PASS`.

- [ ] **Step 3: Create real v0.4.1 state**

Install the actual `v0.4.1` APG release in a separate isolated host, create and
checkpoint a work unit, bind a test session, capture every runtime file hash,
and record the authority verdict.

- [ ] **Step 4: End APG lifecycle and install the candidate**

Require `APG_ACTIVE_SESSIONS=0` and `OLD_TASKS_FINISHED=YES`, remove APG using
the supported plugin removal flow, install RepoKeel, then run resume,
inspect-workspace, evaluate, and resolve-binding against the same project.

- [ ] **Step 5: Prove compatibility**

Require:

```text
OLD_STATE_READ=PASS
STATE_HASHES_UNCHANGED=YES
AUTHORITY_SEMANTICS_UNCHANGED=YES
APG_TO_REPOKEEL_MIGRATION_SMOKE=PASS
```

Any state rewrite, failed legacy read, or semantic change reopens implementation
and review; it cannot be waived as a branding-only defect.

---

### Task 8: Close migration without releasing

**Files:**
- Evidence: GitHub Issue #22 and repository settings.

**Interfaces:**
- Consumes: all prior gates.
- Produces: `REPOKEEL_IDENTITY_MIGRATION=PASS` and `REPOKEEL_V0_5_RELEASE_READY=YES` with no tag/release.

- [ ] **Step 1: Run final audit**

Confirm remote branches, worktree registrations, clean `main`, repository name,
canonical URLs/topics/description, unchanged historical releases, and absence of
new tags/releases. Re-run unit tests and package validation on merged `main`.

- [ ] **Step 2: Record the Definition of Done**

Comment the complete #22 DoD with exact PRs, SHAs, CI runs, smoke evidence,
legacy hashes, redirect result, and `NEW_TAG=NO`, `NEW_RELEASE=NO`.

- [ ] **Step 3: Close the work unit and Issue**

Checkpoint and close `repokeel-identity-migration-001`, remove only worktrees
whose cleanup Gate is proven, close #22 as completed, and leave release creation
for a separate explicit authorization.
