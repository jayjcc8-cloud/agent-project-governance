# Contributing to Agent Project Governance

Thanks for helping improve APG. Contributions should make long-running agent
work easier to understand, resume, or verify without creating a second source
of project truth.

## Choose the right starting point

- Small documentation or test-only fixes may go directly to a pull request.
- Product or behavior changes should start with an Issue.
- Large architecture changes should be discussed before implementation.
- Usage questions and early ideas belong in GitHub Discussions.
- Security reports must follow [SECURITY.md](SECURITY.md), not a public Issue.

## Set up the repository

Fork and clone the repository, then create a short-lived branch from `main`:

```bash
git switch main
git pull --ff-only
git switch -c docs/clearer-quick-start
```

Use a branch name that describes the change:

- `feat/<issue>-<description>`
- `fix/<issue>-<description>`
- `docs/<description>`
- `chore/<description>`
- `test/<description>`

APG has no runtime dependency installation step. Development validation uses
Python 3.9 or newer.

## Run validation

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
```

CI repeats compilation, tests, and package validation on Ubuntu, macOS, and
Windows with Python 3.9 and 3.13.

## Open a pull request

Keep the change focused and include:

- what changed and why;
- the related Issue when one exists;
- exact validation commands and results;
- any known limitation or intentionally untested path.

Do not mix product behavior, release changes, or unrelated cleanup into a
documentation or community-maintenance PR.

## Clean up merged branches

Delete a branch only when it has no open pull request, no active task or
binding, and no worktree containing required work. One of these delivery checks
must also pass:

- the branch head is reachable from the current `main`; or
- squash equivalence is proven: the associated pull request is merged, its
  recorded head SHA equals the branch head, the pull-request head tree equals
  the merge-commit tree, and that merge commit is reachable from current
  `main`.

`git rev-list origin/main..origin/<branch>` remains useful diagnostic evidence,
but a nonzero count is not by itself a deletion blocker after a squash merge.
Commit topology and delivered content are separate facts.

Before removing an associated worktree, confirm that it is clean, has no active
task binding, and contains no unpushed required work. Remove a clean worktree
normally; never use force to bypass a failed safety check. If any fact is
missing or contradictory, preserve the branch and investigate it separately.

## Changes that will not be accepted

APG is not a project manager, orchestration engine, IDE, or replacement for
GitHub, Git, specifications, review, or CI. Changes that create a parallel task
database, hidden authority, automatic approval, or a second governance engine
are outside the current product boundary.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
