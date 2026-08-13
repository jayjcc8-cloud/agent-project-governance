from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Union


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "skills" / "context-governance" / "scripts" / "hook_adapter.py"
WORK_UNIT = ROOT / "skills" / "context-governance" / "scripts" / "work_unit.py"
HOOKS_JSON = ROOT / "hooks" / "hooks.json"


class HookTests(unittest.TestCase):
    def run_hook(self, payload: Union[dict[str, object], str]) -> subprocess.CompletedProcess[str]:
        input_text = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=input_text,
            check=False,
            capture_output=True,
            text=True,
        )

    def run_work_unit(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(WORK_UNIT), *arguments, "--project-root", str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_hook_command(
        self, plugin_root: Path, payload: dict[str, object]
    ) -> subprocess.CompletedProcess[str]:
        command = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]["Stop"][0][
            "hooks"
        ][0]["command"]
        environment = os.environ.copy()
        environment["PLUGIN_ROOT"] = str(plugin_root)
        return subprocess.run(
            ["sh", "-c", command],
            input=json.dumps(payload),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=environment,
        )

    def initialize_bound_unit(self, root: Path) -> None:
        authority = root / "tasks.md"
        authority.write_text("task\n", encoding="utf-8")
        initialized = self.run_work_unit(
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
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        checkpoint = self.run_work_unit(
            root,
            "checkpoint",
            "--work-unit",
            "feature-001",
            "--actor",
            "main",
            "--summary",
            "Bound checkpoint.",
            "--next-action",
            "Continue safely.",
        )
        self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
        bound = self.run_work_unit(
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

    def base_payload(self, root: Path, event: str) -> dict[str, object]:
        return {
            "hook_event_name": event,
            "session_id": "session-main",
            "cwd": str(root),
            "model": "test",
        }

    def test_unbound_session_start_supplies_id_without_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_hook(self.base_payload(Path(directory), "SessionStart"))
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            context = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("session-main", context)
            self.assertIn("No work unit is bound", context)
            self.assertNotIn("decision", output)

    def test_bound_session_start_reads_only_its_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            before = (root / ".agent-runtime" / "work-units" / "feature-001" / "state.json").read_bytes()
            result = self.run_hook(self.base_payload(root, "SessionStart"))
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("feature-001", context)
            self.assertIn("Bound checkpoint", context)
            after = (root / ".agent-runtime" / "work-units" / "feature-001" / "state.json").read_bytes()
            self.assertEqual(after, before)

    def test_subagent_never_inherits_main_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            payload = self.base_payload(root, "SubagentStart")
            payload.update({"agent_id": "agent-1", "agent_type": "worker"})
            started = self.run_hook(payload)
            context = json.loads(started.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("distinct work unit", context)
            self.assertNotIn("Bound checkpoint", context)
            payload["hook_event_name"] = "SubagentStop"
            stopped = self.run_hook(payload)
            message = json.loads(stopped.stdout)["systemMessage"]
            self.assertIn("No session-bound work unit", message)

    def test_precompact_and_stop_are_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            for event in ("PreCompact", "Stop"):
                result = self.run_hook(self.base_payload(root, event))
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertTrue(output["continue"])
                self.assertNotIn("decision", output)
                self.assertIn("feature-001", output["systemMessage"])

    def test_invalid_input_never_blocks(self) -> None:
        result = self.run_hook("not-json")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["continue"])
        self.assertNotIn("decision", output)

    @unittest.skipIf(shutil.which("sh") is None, "POSIX hook launcher is not supported")
    def test_hook_launcher_passes_through_adapter_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = self.base_payload(Path(directory), "Stop")
            result = self.run_hook_command(ROOT, payload)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["continue"])
            self.assertIn("No session-bound work unit", output["systemMessage"])

    @unittest.skipIf(shutil.which("sh") is None, "POSIX hook launcher is not supported")
    def test_hook_launcher_fails_open_after_plugin_directory_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_plugin = Path(directory) / "retired-plugin-build"
            payload = self.base_payload(Path(directory), "Stop")
            for _ in range(100):
                result = self.run_hook_command(missing_plugin, payload)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertTrue(output["continue"])
                self.assertNotIn("decision", output)
                self.assertIn("unavailable", output["systemMessage"])

    def test_hook_config_uses_default_discovery_and_advisory_events(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest)
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        self.assertEqual(
            set(config["hooks"]),
            {"SessionStart", "PreCompact", "SubagentStart", "SubagentStop", "Stop"},
        )
        for groups in config["hooks"].values():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertEqual(hook["type"], "command")
                    self.assertIn("$PLUGIN_ROOT", hook["command"])
                    self.assertTrue(hook["command"].startswith("sh -c"))
                    self.assertIn("exit 0", hook["command"])


if __name__ == "__main__":
    unittest.main()
