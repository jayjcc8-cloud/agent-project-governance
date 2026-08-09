# Runtime State Schema v0.1

`.agent-runtime/work-units/<work-unit-id>/state.json` is private, derived runtime memory. It is not a
project plan and should be excluded from version control.

Required top-level fields:

- `schema_version`: exactly `0.1`;
- `work_unit_id`: stable ID for one coherent unit of work;
- `actor_id`: exclusive owner such as `main`, `implementer-1`, or `reviewer-1`;
- `parent_work_unit_id`: optional causal parent, never an ownership shortcut;
- `status`: currently only `active`;
- `created_at` and `updated_at`: UTC timestamps;
- `authorities`: canonical file references with `kind`, project-relative `path`, and SHA-256 digest;
- `checkpoint`: null or the latest durable checkpoint.

A checkpoint contains a monotonic `sequence`, `recorded_at`, concise `summary`, one `next_action`,
and bounded lists of `findings` and `failed_attempts`.

Invariants:

1. Only the matching `actor_id` may checkpoint or resume a work unit.
2. Authority contents are never copied into runtime state.
3. Checkpoint refreshes authority hashes after confirming every authority still exists.
4. Resume is read-only and reports whether current authority hashes match the checkpoint.
5. State writes use a private temporary file, `fsync`, and atomic replacement.
