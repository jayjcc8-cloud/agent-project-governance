# RepoKeel

Persistent project state for AI coding agents.

> Preserve the state of the work, not the state of the conversation.

[![CI](https://github.com/jayjcc8-cloud/repokeel/actions/workflows/ci.yml/badge.svg)](https://github.com/jayjcc8-cloud/repokeel/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/jayjcc8-cloud/repokeel?include_prereleases&label=latest%20preview)](https://github.com/jayjcc8-cloud/repokeel/releases/tag/v0.4.1)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AI coding sessions are temporary. Your project's state is not.

RepoKeel keeps coding agents grounded in the real state of ongoing engineering
work: tasks, repository state, worktree boundaries, authority changes,
evidence, and the next safe action. Work resumes from project facts instead of
reconstructed chat history.

## What RepoKeel does

- Checkpoints and resumes actor-owned work units.
- Realigns local work with authoritative task sources such as GitHub Issues,
  pull requests, and repository files.
- Inspects Git and worktree boundaries before an agent writes or closes work.
- Recommends a safe next action when context, authority, or budget changes.
- Bootstraps missing project files without overwriting existing policy.

RepoKeel ships as a skills-only Codex plugin. Its hooks are advisory and fail
open; GitHub, Git, accepted specifications, Issues, PRs, and CI remain
authoritative.

## Quick Start

RepoKeel `v0.5.0` is an unreleased development candidate. Before its first
release, validate a source checkout directly:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
```

After RepoKeel `v0.5.0` is published, its versioned marketplace and plugin
install commands become the supported first-use path:

```bash
codex plugin marketplace add jayjcc8-cloud/repokeel --ref v0.5.0
codex plugin add repokeel@repokeel
```

The unreleased marketplace entry intentionally pins `v0.5.0`, so these
commands will resolve only after that tag is published; RepoKeel is not
advertised as an installable `main` snapshot.

After installing a published RepoKeel release, open a Git repository in Codex
and ask:

> Inspect this project with RepoKeel and preview its setup. Do not change
> existing files.

Review the preview. If you want RepoKeel to add only missing project files,
ask:

> Apply the RepoKeel project bootstrap to this repository, then run its health
> check.

RepoKeel never installs optional dependencies and never overwrites an existing
policy file. For direct source usage and contributor setup, see
[Contributing](CONTRIBUTING.md).

The latest published preview is the legacy APG `v0.4.1` release. Existing APG
installations do not automatically become RepoKeel installations; see
[Migrating from APG](docs/migrating-from-apg.md).

## How it works

```text
Task authority
      |
      v
  RepoKeel
  +---+---+
  |   |   |
 Git  |  Context
    Worktree
      |
      v
Safe continuation
```

The current development branch contains five stable workflow IDs:

| Workflow | Purpose |
|---|---|
| `project-bootstrap` | Preview or add missing local project assets. |
| `context-governance` | Checkpoint, resume, bind, realign, and close work units. |
| `eng-task-start` | Refresh task, Git, worktree, and authorization facts. |
| `eng-bounded-delivery` | Keep implementation and review inside the task contract. |
| `eng-verified-closeout` | Verify the candidate, CI, merge, and cleanup separately. |

These workflow IDs remain stable across the product rename and are not a
mandatory chain. RepoKeel is currently evaluated against the
[frozen APG V1 core contract](docs/apg-v1-contract.md) established before the
rename.

## Current status

| Item | Status |
|---|---|
| Current product | RepoKeel |
| Current candidate | `v0.5.0`, not released |
| Latest published legacy preview | APG `v0.4.1` |
| V1 acceptance | Pending against the frozen APG V1 contract |
| Core Python support | Python 3.9+ on macOS, Linux, and Windows |
| Advisory hooks | Supported on macOS and Linux; Windows remains experimental |

CI compiles the Python entry points, runs the full unit suite, and validates
the package on Ubuntu, macOS, and Windows with Python 3.9 and 3.13.

See [Capability boundaries](docs/capability-boundaries.md) for the supported
and unsupported matrix. A green mechanism test does not by itself satisfy the
historical APG V1 acceptance gate; three real product tasks must demonstrate
concrete continuity value.

## Who should use RepoKeel?

RepoKeel is for maintainers using coding agents on work that spans sessions,
worktrees, or changing task sources. It is most useful when safe continuation
matters more than autonomous orchestration.

## What RepoKeel does not do

RepoKeel does not replace your issue tracker, specification system, project
plan, review process, CI, or release authority. It does not run a multi-agent
orchestrator, approve conclusions, create worktrees on its own, or silently
rewrite project policy or stored project state.

## Documentation

Start with the [documentation index](docs/README.md), then use the
[historical APG V1 contract](docs/apg-v1-contract.md),
[migration guide](docs/migrating-from-apg.md), and
[capability boundaries](docs/capability-boundaries.md) for precise semantics.

## Contributing

External contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md)
for setup, validation, branch naming, and scope guidance. Look for
[`good first issue`](https://github.com/jayjcc8-cloud/repokeel/labels/good%20first%20issue)
or
[`help wanted`](https://github.com/jayjcc8-cloud/repokeel/labels/help%20wanted)
to get started.

## Security

Please do not report exploitable vulnerabilities in a public Issue. Follow the
private reporting instructions in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
