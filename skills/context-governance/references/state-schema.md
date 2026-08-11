# Runtime State Schema v0.3

`.agent-runtime/work-units/<work-unit-id>/state.json` is private derived memory, not a project plan. It must remain excluded from version control.

Required fields:

- `schema_version`: `0.3`;
- `revision`: positive monotonic integer for successful mutations;
- `work_unit_id`, `actor_id`, and optional `parent_work_unit_id`;
- `status`: `active` or `closed`;
- `created_at`, `updated_at`, nullable `closed_at`, and nullable `close_summary`;
- `authorities`: either canonical project-relative paths with kind and SHA-256, or GitHub Issue/PR entries with provider, resource type, repository, number, canonical URL, and SHA-256;
- `checkpoint`: null or the latest durable checkpoint.

A checkpoint contains a monotonic sequence, timestamp, concise summary, one next action, and bounded findings and failed attempts. Local file contents, GitHub Issue/PR contents, task lists, decisions from `evaluate`, and chat transcripts are forbidden. GitHub digests cover stable governance fields and exclude volatile transport metadata such as update timestamps, comment counts, and reactions.

Session bindings live under `.agent-runtime/session-bindings/<sha256>.json`. The filename hashes session and optional agent IDs. Bindings contain the exact work unit and actor and are not inherited by subagents.

Invariants:

1. Only the matching actor may mutate, resume, evaluate, bind, or close a work unit.
2. Checkpoint refreshes authority hashes only after every authority exists inside the project root.
3. Resume and evaluate are read-only and tolerate valid v0.1/v0.2 state.
4. Migrate and the next checkpoint upgrade v0.1/v0.2 atomically without losing fields or resetting a v0.2 revision.
5. Close requires a checkpoint and unchanged authorities.
6. Mutations use an exclusive short-lived lock, same-directory temporary file, file `fsync`, atomic replacement, and POSIX directory `fsync` where available.
7. Explicit lifecycle commands may read GitHub authorities through authenticated `gh api`; hooks never make remote requests and label remote checks as pending.
