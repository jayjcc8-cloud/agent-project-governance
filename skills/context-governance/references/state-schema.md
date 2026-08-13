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

A checkpoint contains a monotonic sequence, timestamp, concise summary, one next action, and bounded findings and failed attempts. Local file contents, GitHub Issue/PR contents, task lists, decisions from `evaluate`, and chat transcripts are forbidden. GitHub `github-v2` digests cover stable Issue/PR governance fields plus PR review-thread resolution and status-check rollups. They exclude volatile transport metadata such as update timestamps, comment counts, reactions, and Actions logs.

Explicit `resume` emits current normalized GitHub evidence transiently as part of the recovery contract. Evidence and command timings are never written to state. Valid v0.3 GitHub entries are compared with the legacy `github-v1` projection until the next checkpoint promotes them atomically.

Session bindings live under `.agent-runtime/session-bindings/<sha256>.json`. The filename hashes session and optional agent IDs. Bindings contain the exact work unit and actor and are not inherited by subagents.

Invariants:

1. Only the matching actor may mutate, resume, evaluate, bind, or close a work unit.
2. Checkpoint refreshes authority hashes only after every authority exists inside the project root.
3. Resume and evaluate are read-only and tolerate valid v0.1/v0.2/v0.3 state.
4. Migrate and the next checkpoint upgrade v0.1/v0.2/v0.3 atomically without losing fields or resetting an existing revision.
5. Close requires a checkpoint and unchanged authorities.
6. Mutations use an exclusive short-lived lock, same-directory temporary file, file `fsync`, atomic replacement, and POSIX directory `fsync` where available.
7. Explicit lifecycle commands read all GitHub authorities in a work unit through one authenticated GraphQL snapshot; hooks never make remote requests and label remote checks as pending.
