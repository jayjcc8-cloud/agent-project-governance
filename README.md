# Agent Project Governance

Durable task and context continuity for long-running AI engineering work.

[![CI](https://github.com/jayjcc8-cloud/agent-project-governance/actions/workflows/ci.yml/badge.svg)](https://github.com/jayjcc8-cloud/agent-project-governance/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/jayjcc8-cloud/agent-project-governance?include_prereleases&label=latest%20preview)](https://github.com/jayjcc8-cloud/agent-project-governance/releases/tag/v0.4.1)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Long-running coding agents lose context. Agent Project Governance (APG) helps
them recover the task, repository state, and safe next action without creating
a second project-management system.

## Why APG?

AI engineering work rarely ends in one uninterrupted session. Context gets
compacted, tasks move between agents, branches diverge, and the authoritative
Issue or PR changes. APG keeps a small, inspectable continuity record so work
can resume from project facts instead of reconstructed chat history.

## What APG does

- Checkpoints and resumes actor-owned work units.
- Realigns local work with authoritative task sources such as GitHub Issues,
  pull requests, and repository files.
- Inspects Git and worktree boundaries before an agent writes or closes work.
- Recommends a safe next action when context, authority, or budget changes.
- Bootstraps missing governance files without overwriting existing policy.

APG ships as a skills-only Codex plugin. Its hooks are advisory and fail open;
GitHub, Git, accepted specifications, Issues, PRs, and CI remain authoritative.

## Quick Start

The latest published developer preview is `v0.4.1`. With Codex CLI installed:

```bash
codex plugin marketplace add jayjcc8-cloud/agent-project-governance --ref v0.4.1
codex plugin add agent-project-governance@agent-project-governance
```

Open a Git repository in Codex and ask:

> Inspect this project with APG and preview its governance setup. Do not change
> existing files.

Review the preview. If you want APG to add only missing governance files, ask:

> Apply the APG project bootstrap to this repository, then run its health check.

APG never installs optional dependencies and never overwrites an existing
policy file. For direct source usage and contributor setup, see
[Contributing](CONTRIBUTING.md).

## How it works

```text
Task authority
      |
      v
     APG
  +---+---+
  |   |   |
 Git  |  Context
    Worktree
      |
      v
Safe continuation
```

The current development branch contains five focused entry points:

| Workflow | Purpose |
|---|---|
| `project-bootstrap` | Preview or add missing local governance assets. |
| `context-governance` | Checkpoint, resume, bind, realign, and close work units. |
| `eng-task-start` | Refresh task, Git, worktree, and authorization facts. |
| `eng-bounded-delivery` | Keep implementation and review inside the task contract. |
| `eng-verified-closeout` | Verify the candidate, CI, merge, and cleanup separately. |

These workflows are not a mandatory chain. The
[APG V1 core contract](docs/apg-v1-contract.md) defines the smaller product
boundary.

## Current status

| Item | Status |
|---|---|
| Project maturity | Developer Preview |
| Latest published preview | `v0.4.1` |
| Current `main` | `v0.5.0` development candidate, not released |
| APG V1 acceptance | `PENDING_THREE_REAL_PRODUCT_TASKS` |
| Core Python support | Python 3.9+ on macOS, Linux, and Windows |
| Advisory hooks | Supported on macOS and Linux; Windows remains experimental |

CI compiles the Python entry points, runs the full unit suite, and validates
the package on Ubuntu, macOS, and Windows with Python 3.9 and 3.13.

See [Capability boundaries](docs/capability-boundaries.md) for the supported
and unsupported matrix. A green mechanism test does not by itself promote APG
V1; three real product tasks must demonstrate concrete continuity value.

## Who should use APG?

APG is for maintainers using coding agents on work that spans sessions,
worktrees, or changing task sources. It is most useful when safe continuation
matters more than autonomous orchestration.

## What APG does NOT do

APG does not replace your issue tracker, specification system, project plan,
review process, CI, or release authority. It does not run a multi-agent
orchestrator, approve conclusions, create worktrees on its own, or silently
rewrite project policy.

## Documentation

Start with the [documentation index](docs/README.md), then use the
[core contract](docs/apg-v1-contract.md) and
[capability boundaries](docs/capability-boundaries.md) for precise product
semantics.

## Contributing

External contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md)
for setup, validation, branch naming, and scope guidance. Look for
[`good first issue`](https://github.com/jayjcc8-cloud/agent-project-governance/labels/good%20first%20issue)
or
[`help wanted`](https://github.com/jayjcc8-cloud/agent-project-governance/labels/help%20wanted)
to get started.

## Security

Please do not report exploitable vulnerabilities in a public Issue. Follow the
private reporting instructions in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
