# Workspace inspection boundaries

`work_unit.py inspect-workspace` observes local Git state only. It does not
fetch, checkout, write the index or config, clean files, create or remove a
worktree, inspect CI, or prove exclusive ownership.

Use `--check` when a caller wants exit `1` for observed admission conflicts. The
flag is not a merge or security gate. `--expect-head` accepts only a full commit
SHA obtained from an independently current source; a mismatch never authorizes a
reset. `--base` and ahead/behind counts use existing local refs only.

For a branch checked out in another worktree, inspect that location and confirm
handoff before writing. Local-ahead commits may be valid unpublished work.
Detached HEAD can be fine for review but needs a deliberate branch before new
writing. An unborn repository has no trusted base SHA. After a squash merge,
`git branch --merged` alone does not prove whether all branch work was preserved.

Output includes local paths. Redact those paths before publishing evidence. The
command excludes `.agent-runtime` from dirty-state admission but does not inspect
ignored files, file contents, submodule worktrees, LFS state, processes, or
writer leases.
