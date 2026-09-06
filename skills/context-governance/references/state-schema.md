# Runtime State Schema v0.4

`.agent-runtime/work-units/<work-unit-id>/state.json` is private derived memory, not a project plan. It must remain excluded from version control.

Required fields:

- `schema_version`: `0.4`;
- `revision`: positive monotonic integer for successful mutations;
- `work_unit_id`, `actor_id`, and optional `parent_work_unit_id`;
- `status`: `active` or `closed`;
- `created_at`, `updated_at`, nullable `closed_at`, and nullable `close_summary`;
- `authorities`: either canonical project-relative paths with kind and SHA-256, or GitHub Issue/PR entries with provider, resource type, repository, number, canonical URL, projection version, and SHA-256;
- `checkpoint`: null or the latest durable checkpoint.

A checkpoint contains a monotonic sequence, timestamp, concise summary, one next action, bounded findings and failed attempts, and an optional bounded string-to-string `state` mapping for current material fields such as HEAD, review verdict, finding count, or repair usage. The mapping is part of the latest canonical snapshot, not an event log. Older schema `0.4` checkpoints without it remain valid and read as an empty mapping. Local file contents, GitHub Issue/PR contents, task lists, decisions from `evaluate`, and chat transcripts are forbidden. GitHub `github-v2` digests cover stable Issue/PR governance fields plus PR review-thread resolution and status-check rollups. They exclude volatile transport metadata such as update timestamps, comment counts, reactions, and Actions logs.

`checkpoint --event ...` merges supplied `KEY=VALUE` entries into the canonical
mapping and inherits omitted checkpoint fields. It refreshes evidence only for a
declared evidence-change, finding/review change, recovery, or handoff event. If
canonical content and refreshed authority digests are unchanged, it does not
increment sequence/revision, update timestamps, or write the file. Its output is
a deterministic changed-field delta and never the full snapshot. Explicit
`resume` remains the full canonical recovery operation.

Explicit `resume` emits current normalized GitHub evidence and read-only git HEAD/cleanliness transiently as part of the recovery contract. Evidence and command timings are never written to state. Valid v0.3 GitHub entries are compared with the legacy `github-v1` projection until the next checkpoint promotes them atomically.

The recovery contract uses `authority_verdict: matched | changed | unknown`. Remote unavailability and incomplete bounded connections produce `unknown`, leave per-authority `matches_checkpoint` null, and never populate the drift list. No failure result is persisted.

Session bindings live under `.agent-runtime/session-bindings/<sha256>.json`. The filename hashes session and optional agent IDs. Bindings contain the exact work unit and actor and are not inherited by subagents.

Invariants:

1. Only the matching actor may mutate, resume, evaluate, bind, or close a work unit.
2. Checkpoint refreshes authority hashes only after every authority exists inside the project root.
3. Resume and evaluate are read-only and tolerate valid v0.1/v0.2/v0.3 state.
4. Migrate and the next checkpoint upgrade v0.1/v0.2/v0.3 atomically without losing fields or resetting an existing revision.
5. Close requires a checkpoint and unchanged authorities.
6. Mutations use an exclusive short-lived lock, same-directory temporary file, file `fsync`, atomic replacement, and POSIX directory `fsync` where available.
7. Explicit lifecycle commands read all GitHub authorities in a work unit through one authenticated GraphQL snapshot; hooks never make remote requests and label remote checks as pending.
8. Concurrent identical checkpoints serialize; after the first material write,
   later identical calls are no-ops rather than new revisions.
