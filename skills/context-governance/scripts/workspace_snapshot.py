#!/usr/bin/env python3
"""Read-only local Git/worktree evidence for task intake and recovery.

The helper never fetches, checks out, cleans, writes Git configuration, or
claims writer exclusivity, CI success, or remote freshness.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple, Union


class SnapshotError(RuntimeError):
    """A local observation could not be completed accurately."""


def _git(
    repo: Path, *arguments: str, ok: Tuple[int, ...] = (0,)
) -> bytes:
    environment = os.environ.copy()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
    ):
        environment.pop(key, None)
    for key in list(environment):
        if key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(key)
    environment.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
        }
    )
    try:
        completed = subprocess.run(
            [
                "git",
                "--no-pager",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "gc.auto=0",
                "-c",
                "maintenance.auto=false",
                "-C",
                str(repo),
                *arguments,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=15,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SnapshotError("Git executable or requested directory unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise SnapshotError("Git observation timed out; no write was attempted") from exc
    except OSError as exc:
        raise SnapshotError("Unable to start Git observation") from exc
    if completed.returncode not in ok:
        operation = arguments[0] if arguments else "observation"
        raise SnapshotError(
            f"Git {operation} failed (exit {completed.returncode}); no write was attempted"
        )
    return completed.stdout


def _text(raw: bytes) -> str:
    return os.fsdecode(raw)


def commit_sha(repo: Path, ref: str) -> Optional[str]:
    if not ref or any(character in ref for character in ("\x00", "\n", "\r")):
        raise SnapshotError("Invalid commit reference")
    raw = _git(
        repo,
        "rev-parse",
        "--verify",
        "--quiet",
        "--end-of-options",
        f"{ref}^{{commit}}",
        ok=(0, 1),
    )
    value = raw.decode("ascii").strip()
    if value and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) is None:
        raise SnapshotError("Unexpected commit identity from Git")
    return value or None


def parse_worktrees(raw: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    record: dict[str, Any] = {}
    for token in raw.split(b"\x00"):
        if not token:
            if record:
                records.append(record)
                record = {}
            continue
        key, separator, value = token.partition(b" ")
        if key == b"worktree" and record:
            records.append(record)
            record = {}
        try:
            label = key.decode("ascii")
        except UnicodeDecodeError as exc:
            raise SnapshotError("Malformed worktree porcelain label") from exc
        record[label] = _text(value) if separator else True
    if record:
        records.append(record)
    return records


def parse_status(raw: bytes) -> list[dict[str, str]]:
    entries = raw.split(b"\x00")
    result: list[dict[str, str]] = []
    index = 0
    while index < len(entries):
        item = entries[index]
        index += 1
        if not item:
            continue
        if len(item) < 4 or item[2:3] != b" ":
            raise SnapshotError("Malformed porcelain status")
        try:
            code = item[:2].decode("ascii")
        except UnicodeDecodeError as exc:
            raise SnapshotError("Malformed porcelain status code") from exc
        row = {"status": code, "path": _text(item[3:])}
        if "R" in code or "C" in code:
            if index >= len(entries) or not entries[index]:
                raise SnapshotError("Missing rename/copy source path")
            row["original_path"] = _text(entries[index])
            index += 1
        result.append(row)
    return result


def snapshot(
    repo: Union[str, Path],
    *,
    base: Optional[str] = None,
    target_branch: Optional[str] = None,
    expect_head: Optional[str] = None,
) -> dict[str, Any]:
    try:
        path = Path(repo).expanduser().resolve(strict=True)
    except OSError as exc:
        raise SnapshotError("Requested repository path is unavailable") from exc
    if not path.is_dir():
        raise SnapshotError("Requested repository path is not a directory")
    if _git(path, "rev-parse", "--is-bare-repository").strip() == b"true":
        raise SnapshotError("Bare repositories have no writer checkout")
    top = Path(_text(_git(path, "rev-parse", "--show-toplevel")).rstrip("\n")).resolve()
    if expect_head is not None and re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", expect_head
    ) is None:
        raise SnapshotError("--expect-head requires a full lowercase commit SHA")
    if target_branch is not None:
        _git(top, "check-ref-format", f"refs/heads/{target_branch}")

    start_head = commit_sha(top, "HEAD")
    branch = (
        _text(
            _git(
                top,
                "symbolic-ref",
                "--quiet",
                "--short",
                "HEAD",
                ok=(0, 1),
            )
        ).strip()
        or None
    )
    worktrees = parse_worktrees(_git(top, "worktree", "list", "--porcelain", "-z"))
    changes = parse_status(
        _git(
            top,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            ".",
            ":(exclude).agent-runtime",
        )
    )
    issues: list[str] = []
    warnings: list[str] = []
    if start_head is None:
        warnings.append("unborn_repository_no_commit")
    if changes:
        issues.append("working_tree_has_changes_review_ownership")
    if expect_head is not None and start_head != expect_head:
        issues.append("expected_head_mismatch")
    if target_branch is not None and target_branch != branch:
        issues.append("current_branch_differs_from_requested_target")
    owners = (
        [
            item
            for item in worktrees
            if item.get("branch") == f"refs/heads/{target_branch}"
        ]
        if target_branch
        else []
    )
    other_owners = [
        item
        for item in owners
        if isinstance(item.get("worktree"), str)
        and Path(str(item["worktree"])).resolve() != top
    ]
    if other_owners:
        issues.append("target_branch_checked_out_elsewhere_inspect_existing_worktree")

    upstream_name: Optional[str] = None
    upstream_sha: Optional[str] = None
    if branch and start_head:
        upstream_name = (
            _text(
                _git(
                    top,
                    "for-each-ref",
                    "--format=%(upstream:short)",
                    f"refs/heads/{branch}",
                )
            ).strip()
            or None
        )
        if upstream_name:
            upstream_sha = commit_sha(top, upstream_name)
    base_sha = commit_sha(top, base) if base else None
    relation: Optional[dict[str, int]] = None
    if base and not base_sha:
        issues.append("requested_base_unavailable_locally")
    if start_head and base_sha:
        left, right = _git(
            top, "rev-list", "--left-right", "--count", f"{start_head}...{base_sha}"
        ).decode("ascii").split()
        relation = {"head_only_commits": int(left), "base_only_commits": int(right)}
    end_head = commit_sha(top, "HEAD")
    if end_head != start_head:
        issues.append("head_changed_during_observation")

    return {
        "schema": "agent-project-governance.workspace-snapshot.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "observation_only": True,
        "network_accessed": False,
        "remote_freshness": "NOT_CHECKED_LOCAL_REFS_ONLY",
        "writer_exclusivity": "NOT_PROVEN",
        "repo_root": str(top),
        "head": start_head,
        "head_at_end": end_head,
        "branch": branch,
        "detached": branch is None,
        "tracked_and_untracked_clean": not changes,
        "ignored_files_checked": False,
        "changes": changes,
        "worktrees": worktrees,
        "target_branch": target_branch,
        "target_branch_owners": owners,
        "upstream": {"name": upstream_name, "local_sha": upstream_sha},
        "base": {"ref": base, "local_sha": base_sha, "relation": relation},
        "issues": issues,
        "warnings": warnings,
        "admission_conflicts_observed": bool(issues),
        "not_a_merge_approval": True,
    }
