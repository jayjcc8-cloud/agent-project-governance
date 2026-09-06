# Documentation

This index separates RepoKeel's public starting path from the frozen APG
contracts and historical evidence that predate the product rename.

## Getting started

- [Repository Quick Start](../README.md#quick-start)
- [Contributing to RepoKeel](../CONTRIBUTING.md)
- [Migrating from APG](migrating-from-apg.md)
- [`project-bootstrap` workflow](../skills/project-bootstrap/SKILL.md)
- [`context-governance` workflow](../skills/context-governance/SKILL.md)

## Core contract

- [APG V1 core contract](apg-v1-contract.md) is the frozen pre-rename contract
  against which RepoKeel is currently evaluated.
- [APG V1 three-real-task value evaluation](apg-v1-three-task-value-evaluation.md)
  defines the evidence required before V1 acceptance.

## Capability boundaries

- [Capability boundaries and production posture](capability-boundaries.md)
  lists supported, unsupported, and intentionally advisory behavior.

## Compatibility and validation

- [Compatibility smoke protocol](compatibility-smoke.md) records the verified
  Spec Kit, Superpowers, and bridge compatibility baseline.
- [CI workflow](../.github/workflows/ci.yml) compiles scripts, runs unit tests,
  and validates the package across supported operating systems and Python
  versions.

## Experiments and historical evidence

- [Trial and value-evaluation index](trials.md) explains how to read current
  product evidence and older mechanism trials.
- [`trial-records/`](trial-records/) contains paired recovery, drift, and
  handoff records. These records are historical evidence, not current product
  acceptance.
- [`superpowers/plans/`](superpowers/plans/) contains maintainer implementation
  records and is not required reading for users.
