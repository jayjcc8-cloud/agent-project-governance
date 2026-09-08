# RepoKeel

- Treat Spec Kit specifications, plans, and `tasks.md` as canonical project truth.
- Use Superpowers and the Spec Kit–Superpowers bridge for implementation discipline and handoff.
- At a real task start, search once for directly relevant reusable knowledge. Report `RETRIEVAL_USED=YES|NO` and `REUSED_KNOWLEDGE=<references or NONE>`; no hit does not block work.
- After task acceptance, write knowledge only when `NEW_KNOWLEDGE=YES` or `UPDATE_NEEDED=YES`; otherwise `KNOWLEDGE_WRITE=SKIPPED`. Do not create routine summaries or duplicate Issue/PR/Git/CI evidence.
- Recovery is only for real context loss, interruption, handoff, or long-running task resume. Normal tasks need no work unit, binding, checkpoint, or close record. Existing recovery records remain readable.
- Promote knowledge only after actual reuse and through existing project conventions. RepoKeel owns reusable knowledge, not requirements, task lifecycle, risk approval, release, CI, or acceptance.
