# RepoKeel Product Identity Migration Design

**Authority:** GitHub Issue #22, `REPOKEEL-IDENTITY-MIGRATION-001`

**Frozen base:** `b2287cc3321951717380ddeca6fc690e06297e85`

## Decision

Agent Project Governance becomes RepoKeel at the unreleased `v0.5.0`
boundary. Releases through `v0.4.1` remain the historical APG line. The new
plugin ID is `repokeel`; an installed APG plugin does not automatically become
RepoKeel, so this is an explicit v0.x identity migration.

```text
PRODUCT_NAME=RepoKeel
PRODUCT_SLUG=repokeel
CATEGORY=Persistent project state for AI coding agents.
CORE_PROMISE=Preserve the state of the work, not the state of the conversation.
```

APC is retired and is not an intermediate identity.

## Scope

The public product, plugin manifest, marketplace identity, release artifact,
archive root, current documentation, repository metadata, and canonical URLs
move to RepoKeel. The repository moves to `jayjcc8-cloud/repokeel` between two
pull requests.

This migration changes no product behavior, Skill API, state schema, runtime
directory, release tag, or published release. It does not rename the local
checkout or transfer the repository to an organization.

## Compatibility boundary

Brand identity changes; stored project state does not.

The following remain stable:

- `.agent-runtime` and work-unit schema version `0.4`;
- `agent-project-governance.workspace-snapshot.v1` and other persisted IDs;
- authority digests and `matched | changed | unknown` semantics;
- the five existing Skill IDs;
- `APG_*` V1 acceptance and historical evidence markers.

Code that validates the new package identity must name the preserved legacy
schema identity separately. Reading legacy state must not rewrite it.

## Historical boundary

Historical APG contracts, trial records, releases, Issues, pull requests, and
commit messages remain APG evidence. In particular,
`docs/apg-v1-contract.md` and
`docs/apg-v1-three-task-value-evaluation.md` retain their names and claims.
Current docs may explain that RepoKeel is evaluated against the frozen APG V1
contract, but must not relabel that contract.

## Delivery sequence

1. PR 1 changes product, plugin, marketplace, archive, validator, tests, README,
   current docs, and adds `docs/migrating-from-apg.md`. Old repository URLs may
   remain temporarily.
2. Squash-merge PR 1 after independent review and CI.
3. Rename the GitHub repository to `jayjcc8-cloud/repokeel`; verify redirected
   old URLs and preserved GitHub settings/data; update local remotes and topics.
4. PR 2 changes only canonical URLs, badges, source metadata, and install
   commands. Squash-merge it after independent review and CI.
5. Run fresh RepoKeel and real APG v0.4.1-to-RepoKeel host smokes.
6. Record `REPOKEEL_V0_5_RELEASE_READY=YES`; do not tag or publish.

The old slug `jayjcc8-cloud/agent-project-governance` is permanently reserved
and must never be recreated, because doing so would break GitHub's redirect.

## Product copy

The README opens with:

```text
# RepoKeel

Persistent project state for AI coding agents.

Preserve the state of the work,
not the state of the conversation.
```

The product is described through persistent project state, task-source
realignment, Git/worktree evidence, recovery, and safe continuation rather than
as a generic governance layer.

## Package identity

| Surface | Required value |
|---|---|
| Manifest `name` | `repokeel` |
| Manifest `displayName` | `RepoKeel` |
| Marketplace and entry `name` | `repokeel` |
| Release archive | `repokeel-v0.5.0.zip` |
| Checksum | `repokeel-v0.5.0.zip.sha256` |
| Archive root | `repokeel/` |
| Author/developer | `RepoKeel contributors` |

## Validation

Tests must prove new package identity, new release identity, acceptance of old
APG runtime fixtures, preservation of legacy schema IDs, no state rewrite, and
preservation of historical documents. Existing behavior tests continue to
pass.

The final host gates are:

- fresh RepoKeel candidate: bootstrap, checkpoint, resume, package validation;
- real APG `v0.4.1`: create/checkpoint old state, end the old plugin lifecycle,
  install the candidate, then resume, inspect, evaluate, and resolve the old
  binding with unchanged state hashes and authority semantics.

## Completion

Issue #22 closes only when both PRs and merged-main CI pass, public GitHub
identity is RepoKeel, the old URL redirects, both host smokes pass, legacy state
and history remain unchanged, and no tag or release has been created.
