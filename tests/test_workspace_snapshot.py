from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "context-governance" / "scripts" / "workspace_snapshot.py"
WORK_UNIT = ROOT / "skills" / "context-governance" / "scripts" / "work_unit.py"


def load_snapshot_module():
    spec = importlib.util.spec_from_file_location("workspace_snapshot", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_snapshot_module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-q", "--initial-branch=main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        (self.repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-qm", "fixture")

    def git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.repo), *arguments],
            check=True,
            capture_output=True,
        )
        return completed.stdout.decode().strip()

    def test_clean_local_snapshot(self) -> None:
        result = self.module.snapshot(self.repo, base="main", target_branch="main")
        self.assertTrue(result["tracked_and_untracked_clean"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["remote_freshness"], "NOT_CHECKED_LOCAL_REFS_ONLY")
        self.assertEqual(result["writer_exclusivity"], "NOT_PROVEN")

    def test_unknown_untracked_and_tracked_modification_are_preserved(self) -> None:
        unknown = self.repo / "unknown.txt"
        tracked = self.repo / "tracked.txt"
        unknown.write_text("keep", encoding="utf-8")
        tracked.write_text("modified", encoding="utf-8")
        result = self.module.snapshot(self.repo)
        self.assertFalse(result["tracked_and_untracked_clean"])
        self.assertTrue(result["admission_conflicts_observed"])
        self.assertEqual(unknown.read_text(encoding="utf-8"), "keep")
        self.assertEqual(tracked.read_text(encoding="utf-8"), "modified")

    def test_unusual_filename_uses_nul_parsing(self) -> None:
        unusual = "tab\tand\nnewline.txt"
        parsed = self.module.parse_status(b"?? " + os.fsencode(unusual) + b"\x00")
        self.assertEqual(parsed, [{"status": "??", "path": unusual}])
        if os.name != "nt":
            (self.repo / unusual).write_text("data", encoding="utf-8")
            paths = [row["path"] for row in self.module.snapshot(self.repo)["changes"]]
            self.assertIn(unusual, paths)

    def test_rename_uses_nul_parsing(self) -> None:
        self.git("mv", "tracked.txt", "renamed.txt")
        row = self.module.snapshot(self.repo)["changes"][0]
        self.assertEqual(row["path"], "renamed.txt")
        self.assertEqual(row["original_path"], "tracked.txt")

    def test_branch_checked_out_in_other_worktree_is_located(self) -> None:
        other = self.root / "other checkout"
        self.git("worktree", "add", "-q", "-b", "feature/task", str(other))
        result = self.module.snapshot(self.repo, target_branch="feature/task")
        self.assertEqual(
            Path(result["target_branch_owners"][0]["worktree"]).resolve(), other.resolve()
        )
        self.assertIn(
            "target_branch_checked_out_elsewhere_inspect_existing_worktree",
            result["issues"],
        )
        self.assertTrue(other.is_dir())

    def test_detached_and_unborn_repositories_are_explicit(self) -> None:
        self.git("checkout", "-q", "--detach")
        self.assertTrue(self.module.snapshot(self.repo)["detached"])
        unborn = self.root / "unborn"
        subprocess.run(
            ["git", "init", "-q", "--initial-branch=main", str(unborn)], check=True
        )
        result = self.module.snapshot(unborn)
        self.assertIsNone(result["head"])
        self.assertIn("unborn_repository_no_commit", result["warnings"])

    def test_expected_head_and_missing_local_base_are_conflicts(self) -> None:
        head = self.git("rev-parse", "HEAD")
        self.assertNotIn(
            "expected_head_mismatch", self.module.snapshot(self.repo, expect_head=head)["issues"]
        )
        result = self.module.snapshot(
            self.repo, expect_head="0" * 40, base="origin/not-fetched"
        )
        self.assertIn("expected_head_mismatch", result["issues"])
        self.assertIn("requested_base_unavailable_locally", result["issues"])
        with self.assertRaises(self.module.SnapshotError):
            self.module.snapshot(self.repo, expect_head="abc123")

    def test_ahead_behind_uses_local_refs_only(self) -> None:
        self.git("branch", "base")
        (self.repo / "tracked.txt").write_text("next", encoding="utf-8")
        self.git("commit", "-qam", "next")
        relation = self.module.snapshot(self.repo, base="base")["base"]["relation"]
        self.assertEqual(relation, {"head_only_commits": 1, "base_only_commits": 0})

    def test_upstream_does_not_expose_remote_credentials(self) -> None:
        secret_url = "https://user:SECRET@example.invalid/org/repo"
        self.git("remote", "add", "origin", secret_url)
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("branch", "--set-upstream-to", "origin/main", "main")
        result = self.module.snapshot(self.repo)
        self.assertEqual(result["upstream"]["name"], "origin/main")
        self.assertNotIn("SECRET", json.dumps(result))

    def test_subdirectory_resolves_root_and_runtime_state_is_excluded(self) -> None:
        subdirectory = self.repo / "subdir"
        subdirectory.mkdir()
        runtime = self.repo / ".agent-runtime" / "state.json"
        runtime.parent.mkdir()
        runtime.write_text("derived", encoding="utf-8")
        result = self.module.snapshot(subdirectory)
        self.assertEqual(Path(result["repo_root"]).resolve(), self.repo.resolve())
        self.assertTrue(result["tracked_and_untracked_clean"])

    def test_ignored_files_are_not_certified_or_removed(self) -> None:
        (self.repo / ".gitignore").write_text("private.data\n", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore")
        private = self.repo / "private.data"
        private.write_text("must retain", encoding="utf-8")
        result = self.module.snapshot(self.repo)
        self.assertTrue(result["tracked_and_untracked_clean"])
        self.assertFalse(result["ignored_files_checked"])
        self.assertTrue(private.exists())

    def test_invalid_branch_and_malformed_porcelain_are_rejected(self) -> None:
        with self.assertRaises(self.module.SnapshotError):
            self.module.snapshot(self.repo, target_branch="../not-a-ref")
        with self.assertRaises(self.module.SnapshotError):
            self.module.parse_status(b"R  destination\x00")
        parsed = self.module.parse_worktrees(
            b"worktree /tmp/a\x00HEAD " + b"a" * 40 + b"\x00detached\x00locked reason\x00\x00"
        )
        self.assertTrue(parsed[0]["detached"])
        self.assertEqual(parsed[0]["locked"], "reason")

    def test_head_movement_is_reported(self) -> None:
        original = self.module.commit_sha
        count = 0

        def moving(repo: Path, ref: str):
            nonlocal count
            if ref == "HEAD":
                count += 1
                if count > 1:
                    return "0" * 40
            return original(repo, ref)

        with mock.patch.object(self.module, "commit_sha", side_effect=moving):
            result = self.module.snapshot(self.repo)
        self.assertIn("head_changed_during_observation", result["issues"])

    def test_snapshot_does_not_change_index_or_head(self) -> None:
        index = self.repo / ".git" / "index"
        before = (index.read_bytes(), index.stat().st_mtime_ns, self.git("rev-parse", "HEAD"))
        self.module.snapshot(self.repo)
        after = (index.read_bytes(), index.stat().st_mtime_ns, self.git("rev-parse", "HEAD"))
        self.assertEqual(before, after)

    def test_inspect_workspace_cli_is_read_only_and_has_check_status(self) -> None:
        (self.repo / "untracked").write_text("keep", encoding="utf-8")
        index = self.repo / ".git" / "index"
        before = (
            (self.repo / "tracked.txt").read_bytes(),
            (self.repo / "untracked").read_bytes(),
            index.read_bytes(),
            index.stat().st_mtime_ns,
            self.git("rev-parse", "HEAD"),
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(WORK_UNIT),
                "inspect-workspace",
                "--project-root",
                str(self.repo),
                "--check",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["admission_conflicts_observed"])
        self.assertFalse((self.repo / ".agent-runtime").exists())
        after = (
            (self.repo / "tracked.txt").read_bytes(),
            (self.repo / "untracked").read_bytes(),
            index.read_bytes(),
            index.stat().st_mtime_ns,
            self.git("rev-parse", "HEAD"),
        )
        self.assertEqual(after, before)

    def test_inspect_workspace_cli_sanitizes_missing_repo_error(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(WORK_UNIT),
                "inspect-workspace",
                "--project-root",
                str(self.root / "absent"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("project root is not a directory", completed.stderr)


if __name__ == "__main__":
    unittest.main()
