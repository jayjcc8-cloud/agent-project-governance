# RepoKeel

Reusable development knowledge for AI coding agents.

> Retrieve once. Learn when needed. Recover only after interruption.

[![CI](https://github.com/jayjcc8-cloud/repokeel/actions/workflows/ci.yml/badge.svg)](https://github.com/jayjcc8-cloud/repokeel/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/jayjcc8-cloud/repokeel?include_prereleases&label=latest%20preview)](https://github.com/jayjcc8-cloud/repokeel/releases/tag/v0.4.1)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

RepoKeel's normal loop is `RETRIEVE -> EXECUTE -> CONDITIONAL_LEARN`.
Search once for knowledge directly relevant to the real task. Execute using the
project's existing tools and authorities. After acceptance, save or update only
new or outdated reusable knowledge; otherwise stop without a knowledge write.

Recovery is optional and event-driven for actual context loss, interruption,
handoff, or long-running task resume. Normal tasks need no work unit, binding,
checkpoint, or close record. Existing recovery state and CLI readers remain usable.

GitHub Issues or explicit user tasks own requirements; Git owns code; PR/main own
delivery; CI and explicit acceptance evidence own verification. RepoKeel owns
reusable knowledge only. It ships as a skills-only Codex plugin, with fail-open
recovery hooks and no second task lifecycle or acceptance authority.

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

In a source-enabled session, ask RepoKeel to search for knowledge relevant to the
current task. At acceptance, check for new or outdated knowledge and skip writing
when neither exists. Use the project's authorized knowledge route; no new knowledge
store or plugin installation is required by the loop.

Existing bootstrap remains an explicit compatibility helper, not a task-start
requirement. It never installs dependencies or overwrites project policy. For
source usage and contributor setup, see [Contributing](CONTRIBUTING.md).

The latest published preview is the legacy APG `v0.4.1` release. Existing APG
installations do not automatically become RepoKeel installations; see
[Migrating from APG](docs/migrating-from-apg.md).

## How it works

```text
Real task -> relevant knowledge search -> product work -> accepted
                                                    -> new/update knowledge?
                                                       no: stop / yes: write
Actual interruption only -> recover
```

The five existing skill IDs remain compatible, not a mandatory chain:

| Workflow | Purpose |
|---|---|
| `eng-task-start` | One bounded knowledge retrieval at task start. |
| `eng-verified-closeout` | Conditional learning after acceptance. |
| `context-governance` | Exceptional recovery using existing records. |
| `project-bootstrap` | Explicit compatibility setup helper. |
| `eng-bounded-delivery` | Optional guidance subordinate to project delivery rules. |

See the [current V1 contract](docs/apg-v1-contract.md). The three EA pilot tasks
are complete; their SHRINK decision removes routine recovery and duplicate records.

## Current status

| Item | Status |
|---|---|
| Current product | RepoKeel |
| Current candidate | `v0.5.0`, not released |
| Latest published legacy preview | APG `v0.4.1` |
| V1 scope | SHRINK: retrieval, conditional learning, exceptional recovery |
| Core Python support | Python 3.9+ on macOS, Linux, and Windows |
| Advisory hooks | Supported on macOS and Linux; Windows remains experimental |

CI compiles the Python entry points, runs the full unit suite, and validates
the package on Ubuntu, macOS, and Windows with Python 3.9 and 3.13.

See [Capability boundaries](docs/capability-boundaries.md) for the supported
and unsupported matrix. The completed pilot decision is recorded in EA #176; it is not a recurring
per-task evaluation requirement.

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
[current V1 contract](docs/apg-v1-contract.md),
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
