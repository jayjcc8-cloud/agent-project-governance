# Optional domain patterns

Load this reference only when the authorized task reaches one of these domains.
These are prompts for project-specific contracts and regressions, not universal
rules or proof that a defect exists.

## Identity and deterministic artifacts

Separate attempt identity, lineage identity, and semantic-result identity. Define
which projection excludes operational metadata and test both expected equality
and expected inequality. Do not add seed plumbing when the path has no randomness.

## Terminal and durable publication

Define the accepted terminal vocabulary and mandatory validation order. A normal
business rejection may still be a successful simulation. If durability is
claimed, specify the atomic publication and sync boundary; storage failure cannot
guarantee that a failure artifact was itself persisted.

## Funding, risk, and time visibility

Test idempotency and no-partial-mutation at actual execution boundaries. Current
prices do not prove affordability at a later fill. Admit evidence by the
project's declared visibility frontier rather than by a generic timestamp rule.

## Recovery and packaging

Name supported uninterrupted and recovered boundaries; do not turn a marker file
into a writer-lock claim. Validate distributable artifacts outside the source
checkout and confirm that CI jobs and coverage gates actually ran for the current
candidate.
