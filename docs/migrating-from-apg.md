# Migrating from Agent Project Governance

Agent Project Governance was renamed to RepoKeel starting with the unreleased
`v0.5.0` candidate.

```text
v0.4.x and earlier: Agent Project Governance / agent-project-governance
v0.5.0 and later:   RepoKeel / repokeel
```

This is a breaking plugin-identity migration. An existing APG installation does
not automatically become a RepoKeel installation. The supported transition is
to finish every task that could still reference the installed APG plugin,
remove APG through the supported Codex plugin lifecycle, and then install
RepoKeel as a separate plugin identity.

Until RepoKeel `v0.5.0` is published, validate the current source candidate
directly in a disposable or explicitly authorized checkout:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
```

After RepoKeel `v0.5.0` is published, use its versioned source and follow the
release notes for the exact supported installation command. The repository's
marketplace entry intentionally pins that release tag and therefore cannot
install an unpublished `main` candidate.

## What remains compatible

Project runtime state remains compatible. RepoKeel intentionally preserves:

- `.agent-runtime` and existing work-unit formats;
- `agent-project-governance.workspace-snapshot.v1` and other historical schema
  identifiers;
- authority digest and recovery semantics;
- the existing Skill IDs `context-governance`, `project-bootstrap`,
  `eng-task-start`, `eng-bounded-delivery`, and `eng-verified-closeout`;
- historical `APG_*` evidence markers.

Reading an old work unit does not rename or rewrite it merely because the
product identity changed. Brand identity changes; stored project state does
not.

## What does not remain compatible automatically

Plugin installation identity is not project-state identity. The APG plugin ID
is `agent-project-governance`; the RepoKeel plugin ID is `repokeel`. They must
not be installed together as duplicate entries, and RepoKeel does not claim an
automatic in-place upgrade from APG.

## Historical evidence

APG `v0.4.x` and earlier releases, the frozen APG V1 contract, trial records,
Issues, pull requests, and commit history retain their original names. RepoKeel
is currently evaluated against that pre-rename contract; the historical record
is not relabeled.

After the GitHub repository rename, the old
`jayjcc8-cloud/agent-project-governance` URL remains reserved as a redirect to
`jayjcc8-cloud/repokeel`. It must never be recreated as a compatibility
repository, because doing so would break the redirect.
