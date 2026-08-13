from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "context-governance"
    / "scripts"
    / "work_unit.py"
)


def load_work_unit_module():
    spec = importlib.util.spec_from_file_location("context_governance_work_unit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkUnitTests(unittest.TestCase):
    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments, "--project-root", str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def initialize(self, root: Path, *, actor: str = "main") -> Path:
        tasks = root / "specs" / "001" / "tasks.md"
        tasks.parent.mkdir(parents=True)
        tasks.write_text("- [ ] T001 Build the feature\n", encoding="utf-8")
        completed = self.run_cli(
            root,
            "init",
            "--work-unit",
            "feature-001",
            "--actor",
            actor,
            "--authority",
            "tasks",
            "specs/001/tasks.md",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return tasks

    def checkpoint(self, root: Path, *, summary: str = "Contracts pass.") -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            root,
            "checkpoint",
            "--work-unit",
            "feature-001",
            "--actor",
            "main",
            "--summary",
            summary,
            "--next-action",
            "Run integration test.",
            "--finding",
            "tasks.md is authoritative.",
        )

    def state_path(self, root: Path) -> Path:
        return root / ".agent-runtime" / "work-units" / "feature-001" / "state.json"

    def write_legacy_state(self, root: Path) -> Path:
        tasks = root / "specs" / "001" / "tasks.md"
        tasks.parent.mkdir(parents=True)
        tasks.write_text("- [ ] T001 Legacy\n", encoding="utf-8")
        digest = hashlib.sha256(tasks.read_bytes()).hexdigest()
        path = self.state_path(root)
        path.parent.mkdir(parents=True)
        timestamp = "2026-08-09T00:00:00+00:00"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "work_unit_id": "feature-001",
                    "actor_id": "main",
                    "parent_work_unit_id": None,
                    "status": "active",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "authorities": [
                        {"kind": "tasks", "path": "specs/001/tasks.md", "sha256": digest}
                    ],
                    "checkpoint": None,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_checkpoint_and_resume_preserve_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = self.initialize(root)
            checkpoint = self.checkpoint(root)
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            state = json.loads(checkpoint.stdout)
            self.assertEqual(state["schema_version"], "0.3")
            self.assertEqual(state["revision"], 2)
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
            self.assertEqual(tasks.read_text(encoding="utf-8"), "- [ ] T001 Build the feature\n")

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
            tasks = self.initialize(root)
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

    def test_evaluate_is_read_only_and_orders_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = self.initialize(root)
            self.assertEqual(self.checkpoint(root).returncode, 0)
            tasks.write_text("- [x] T001 Build the feature\n", encoding="utf-8")
            before = self.state_path(root).read_bytes()
            evaluated = self.run_cli(
                root,
                "evaluate",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--event",
                "pre-compact",
                "--signal",
                "goal-changed",
                "--signal",
                "repeated-failure",
            )
            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            result = json.loads(evaluated.stdout)
            self.assertEqual(result["primary_action"], "RECONCILE")
            self.assertEqual(
                [item["action"] for item in result["recommendations"]],
                ["RECONCILE", "UPDATE_SPEC", "CHECKPOINT", "DEBUG_REVIEW", "COMPACT"],
            )
            self.assertTrue(all(item["blocking"] is False for item in result["recommendations"]))
            self.assertEqual(self.state_path(root).read_bytes(), before)

    def test_every_signal_maps_to_the_documented_action(self) -> None:
        expected = {
            "goal-changed": "UPDATE_SPEC",
            "implementation-drift": "CONVERGE",
            "feature-complete": "CLOSE",
            "context-noisy": "CHECKPOINT",
            "repeated-failure": "DEBUG_REVIEW",
            "durable-decision": "PROMOTE_ADR",
            "durable-agent-rule": "PROMOTE_AGENTS",
            "independent-work": "WORKTREE",
            "new-work-unit": "NEW_THREAD",
            "exploration-heavy": "SUBAGENT",
            "handoff-required": "HANDOFF",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            for signal, action in expected.items():
                evaluated = self.run_cli(
                    root,
                    "evaluate",
                    "--work-unit",
                    "feature-001",
                    "--actor",
                    "main",
                    "--signal",
                    signal,
                )
                self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
                actions = [item["action"] for item in json.loads(evaluated.stdout)["recommendations"]]
                self.assertIn(action, actions, signal)

    def test_resume_and_evaluate_do_not_migrate_v01(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_legacy_state(root)
            before = path.read_bytes()
            for command in ("resume", "evaluate"):
                result = self.run_cli(
                    root,
                    command,
                    "--work-unit",
                    "feature-001",
                    "--actor",
                    "main",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(path.read_bytes(), before)

    def test_explicit_migration_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_legacy_state(root)
            first = self.run_cli(
                root, "migrate", "--work-unit", "feature-001", "--actor", "main"
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(json.loads(first.stdout)["migrated"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], "0.3")
            second = self.run_cli(
                root, "migrate", "--work-unit", "feature-001", "--actor", "main"
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertFalse(json.loads(second.stdout)["migrated"])

    def test_checkpoint_upgrades_v01_and_increments_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_legacy_state(root)
            checkpoint = self.checkpoint(root, summary="Legacy upgraded.")
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            state = json.loads(checkpoint.stdout)
            self.assertEqual(state["schema_version"], "0.3")
            self.assertEqual(state["revision"], 2)

    def test_bindings_are_hashed_isolated_and_removed_on_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.assertEqual(self.checkpoint(root).returncode, 0)
            for arguments in (
                ("--session", "session-main"),
                ("--session", "session-main", "--agent-id", "agent-1"),
            ):
                bound = self.run_cli(
                    root,
                    "bind",
                    "--work-unit",
                    "feature-001",
                    "--actor",
                    "main",
                    *arguments,
                )
                self.assertEqual(bound.returncode, 0, bound.stderr)
            bindings = list((root / ".agent-runtime" / "session-bindings").glob("*.json"))
            self.assertEqual(len(bindings), 2)
            self.assertTrue(all(path.stem != "session-main" for path in bindings))
            closed = self.run_cli(
                root,
                "close",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "Feature complete.",
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertEqual(json.loads(closed.stdout)["bindings_removed"], 2)
            self.assertEqual(list((root / ".agent-runtime" / "session-bindings").glob("*.json")), [])

    def test_binding_cannot_overwrite_another_actor_or_work_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            bound = self.run_cli(
                root,
                "bind",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--session",
                "shared-session",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr)
            other = self.run_cli(
                root,
                "init",
                "--work-unit",
                "feature-002",
                "--actor",
                "reviewer-1",
            )
            self.assertEqual(other.returncode, 0, other.stderr)
            rejected = self.run_cli(
                root,
                "bind",
                "--work-unit",
                "feature-002",
                "--actor",
                "reviewer-1",
                "--session",
                "shared-session",
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("already bound", rejected.stderr)

    def test_resolve_binding_is_read_only_and_actor_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            bound = self.run_cli(
                root,
                "bind",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--session",
                "session-main",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr)
            runtime = root / ".agent-runtime"
            before = {
                path.relative_to(runtime): path.read_bytes()
                for path in runtime.rglob("*.json")
            }

            resolved = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resolve-binding",
                    "--project-root",
                    str(root),
                    "--session",
                    "session-main",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            result = json.loads(resolved.stdout)
            self.assertTrue(result["found"])
            self.assertEqual(result["binding"]["work_unit_id"], "feature-001")
            self.assertEqual(result["binding"]["actor_id"], "main")

            subagent = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resolve-binding",
                    "--project-root",
                    str(root),
                    "--session",
                    "session-main",
                    "--agent-id",
                    "agent-1",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(subagent.returncode, 1, subagent.stderr)
            self.assertEqual(json.loads(subagent.stdout)["reason_code"], "BINDING_NOT_FOUND")
            after = {
                path.relative_to(runtime): path.read_bytes()
                for path in runtime.rglob("*.json")
            }
            self.assertEqual(after, before)

    def test_missing_mutation_does_not_create_runtime_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_cli(
                root,
                "migrate",
                "--work-unit",
                "missing-unit",
                "--actor",
                "main",
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / ".agent-runtime").exists())

    def test_close_requires_checkpoint_and_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = self.initialize(root)
            no_checkpoint = self.run_cli(
                root,
                "close",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "Done.",
            )
            self.assertEqual(no_checkpoint.returncode, 1)
            self.assertEqual(json.loads(no_checkpoint.stdout)["reason_code"], "CHECKPOINT_REQUIRED")
            self.assertEqual(self.checkpoint(root).returncode, 0)
            tasks.write_text("changed\n", encoding="utf-8")
            changed = self.run_cli(
                root,
                "close",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "Done.",
            )
            self.assertEqual(changed.returncode, 1)
            self.assertEqual(json.loads(changed.stdout)["reason_code"], "AUTHORITY_CHANGED")

    def test_invalid_stored_digest_and_path_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            path = self.state_path(root)
            for key, value in (("sha256", "bad"), ("path", "../outside.md")):
                state = json.loads(path.read_text(encoding="utf-8"))
                original = state["authorities"][0][key]
                state["authorities"][0][key] = value
                path.write_text(json.dumps(state), encoding="utf-8")
                result = self.run_cli(
                    root, "resume", "--work-unit", "feature-001", "--actor", "main"
                )
                self.assertEqual(result.returncode, 2)
                state["authorities"][0][key] = original
                path.write_text(json.dumps(state), encoding="utf-8")

    def test_authority_symlink_outside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            outside_file = Path(outside) / "tasks.md"
            outside_file.write_text("outside\n", encoding="utf-8")
            link = root / "tasks.md"
            try:
                link.symlink_to(outside_file)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            result = self.run_cli(
                root,
                "init",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--authority",
                "tasks",
                "tasks.md",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("inside the project root", result.stderr)

    def test_stale_lock_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            lock = self.state_path(root).parent / ".state.lock"
            lock.write_text("stale", encoding="utf-8")
            old = time.time() - 60
            os.utime(lock, (old, old))
            checkpoint = self.checkpoint(root)
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            self.assertFalse(lock.exists())

    def test_two_concurrent_checkpoints_serialize(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            base = [
                sys.executable,
                str(SCRIPT),
                "checkpoint",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--summary",
                "Concurrent checkpoint.",
                "--next-action",
                "Continue.",
                "--project-root",
                str(root),
            ]
            first = subprocess.Popen(base, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            second = subprocess.Popen(base, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            _, first_error = first.communicate(timeout=10)
            _, second_error = second.communicate(timeout=10)
            self.assertEqual(first.returncode, 0, first_error)
            self.assertEqual(second.returncode, 0, second_error)
            state = json.loads(self.state_path(root).read_text(encoding="utf-8"))
            self.assertEqual(state["checkpoint"]["sequence"], 2)
            self.assertEqual(state["revision"], 3)
            self.assertEqual(list(self.state_path(root).parent.glob(".state.*")), [])

    def test_github_authority_ignores_transport_noise_and_detects_governance_change(self) -> None:
        module = load_work_unit_module()
        baseline = {
            "number": 61,
            "title": "Lifecycle coordinator",
            "body": "Design repair",
            "state": "open",
            "state_reason": None,
            "locked": False,
            "labels": [{"name": "architecture"}, {"name": "phase-1"}],
            "assignees": [{"login": "jayjcc8-cloud"}],
            "milestone": None,
            "updated_at": "2026-08-10T01:00:00Z",
            "comments": 4,
        }
        noisy = {**baseline, "updated_at": "2026-08-11T01:00:00Z", "comments": 99}
        changed = {**noisy, "body": "Accepted design"}
        url = "https://github.com/jayjcc8-cloud/ea-quant/issues/61"
        with mock.patch.object(module, "_github_fetch", return_value=baseline):
            stored = module._github_authority("issue", url)
        state = {"authorities": [stored]}
        with mock.patch.object(module, "_github_fetch", return_value=noisy):
            matches, statuses = module._authority_status(Path.cwd(), state)
        self.assertTrue(matches)
        self.assertTrue(statuses[0]["matches_checkpoint"])
        self.assertNotIn("body", stored)
        with mock.patch.object(module, "_github_fetch", return_value=changed):
            matches, statuses = module._authority_status(Path.cwd(), state)
        self.assertFalse(matches)
        self.assertFalse(statuses[0]["matches_checkpoint"])

    def test_github_authority_parser_and_hook_safe_status(self) -> None:
        module = load_work_unit_module()
        parsed = module._parser().parse_args(
            [
                "init",
                "--project-root",
                ".",
                "--work-unit",
                "feature-001",
                "--actor",
                "main",
                "--github-authority",
                "pr",
                "https://github.com/acme/widget/pull/42",
            ]
        )
        self.assertEqual(parsed.github_authority[0][0], "pr")
        with mock.patch.object(
            module,
            "_github_fetch",
            return_value={"number": 42, "title": "Change", "state": "open"},
        ):
            authority = module._github_authority("pr", parsed.github_authority[0][1])
        matches, statuses = module._authority_status(
            Path.cwd(), {"authorities": [authority]}, fetch_remote=False
        )
        self.assertTrue(matches)
        self.assertFalse(statuses[0]["checked"])
        self.assertIsNone(statuses[0]["matches_checkpoint"])

    def test_migrate_v02_preserves_revision_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.assertEqual(self.checkpoint(root).returncode, 0)
            path = self.state_path(root)
            state = json.loads(path.read_text(encoding="utf-8"))
            state["schema_version"] = "0.2"
            state["revision"] = 9
            path.write_text(json.dumps(state), encoding="utf-8")
            migrated = self.run_cli(
                root, "migrate", "--work-unit", "feature-001", "--actor", "main"
            )
            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            result = json.loads(migrated.stdout)
            self.assertTrue(result["migrated"])
            self.assertEqual(result["state"]["schema_version"], "0.3")
            self.assertEqual(result["state"]["revision"], 9)
            self.assertEqual(result["state"]["checkpoint"]["sequence"], 1)


if __name__ == "__main__":
    unittest.main()
