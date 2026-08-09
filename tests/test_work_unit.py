from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "context-governance"
    / "scripts"
    / "work_unit.py"
)


class WorkUnitTests(unittest.TestCase):
    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments, "--project-root", str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def initialize(self, root: Path) -> None:
        tasks = root / "specs" / "001" / "tasks.md"
        tasks.parent.mkdir(parents=True)
        tasks.write_text("- [ ] T001 Build the feature\n", encoding="utf-8")
        completed = self.run_cli(
            root,
            "init",
            "--work-unit",
            "feature-001",
            "--actor",
            "main",
            "--authority",
            "tasks",
            "specs/001/tasks.md",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_checkpoint_and_resume_preserve_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            checkpoint = self.run_cli(
                root,
                "checkpoint",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "Contracts pass.",
                "--next-action",
                "Run integration test.",
                "--finding",
                "tasks.md is authoritative.",
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            resumed = self.run_cli(
                root,
                "resume",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--strict",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            result = json.loads(resumed.stdout)
            self.assertTrue(result["authorities_match_checkpoint"])
            self.assertEqual(result["checkpoint"]["sequence"], 1)
            self.assertEqual(
                (root / "specs" / "001" / "tasks.md").read_text(encoding="utf-8"),
                "- [ ] T001 Build the feature\n",
            )

    def test_actor_cannot_read_another_work_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            rejected = self.run_cli(
                root,
                "resume",
                "--work-unit",
                "feature-001",
                "--actor",
                "reviewer-1",
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("belongs to actor", rejected.stderr)

    def test_strict_resume_detects_authority_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            tasks = root / "specs" / "001" / "tasks.md"
            tasks.write_text("- [x] T001 Build the feature\n", encoding="utf-8")
            changed = self.run_cli(
                root,
                "resume",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--strict",
            )
            self.assertEqual(changed.returncode, 1, changed.stderr)
            result = json.loads(changed.stdout)
            self.assertFalse(result["authorities_match_checkpoint"])
            self.assertFalse(result["authority_status"][0]["matches_checkpoint"])

    def test_checkpoint_rejects_empty_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            rejected = self.run_cli(
                root,
                "checkpoint",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "   ",
                "--next-action",
                "Run integration test.",
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("summary cannot be empty", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
