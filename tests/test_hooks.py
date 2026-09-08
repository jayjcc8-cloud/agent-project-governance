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
        command = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]["SessionStart"][0][
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

    def test_normal_lifecycle_is_silent_without_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop"):
                payload = self.base_payload(root, event)
                payload["source"] = "startup"
                result = self.run_hook(payload)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {"continue": True})
            self.assertFalse((root / ".agent-runtime").exists())

    def test_bound_normal_start_and_stop_do_not_read_or_prompt_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            for event in ("SessionStart", "Stop", "SubagentStart", "SubagentStop"):
                payload = self.base_payload(root, event)
                payload["source"] = "startup"
                result = self.run_hook(payload)
                self.assertEqual(json.loads(result.stdout), {"continue": True})
            after = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def test_unbound_recovery_does_not_require_creating_a_work_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for event in ("SessionStart", "PreCompact"):
                payload = self.base_payload(root, event)
                payload["source"] = "resume"
                result = self.run_hook(payload)
                self.assertEqual(json.loads(result.stdout), {"continue": True})
            self.assertFalse((root / ".agent-runtime").exists())

    def test_actual_resume_reads_existing_checkpoint_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            state = root / ".agent-runtime/work-units/feature-001/state.json"
            before = state.read_bytes()
            for source in ("resume", "clear", "compact"):
                payload = self.base_payload(root, "SessionStart")
                payload["source"] = source
                result = self.run_hook(payload)
                self.assertEqual(result.returncode, 0, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("Bound checkpoint", context)
            self.assertEqual(state.read_bytes(), before)

    def test_precompact_of_bound_work_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize_bound_unit(root)
            result = self.run_hook(self.base_payload(root, "PreCompact"))
            output = json.loads(result.stdout)
            self.assertTrue(output["continue"])
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
            self.assertEqual(output, {"continue": True})

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
            {"SessionStart", "PreCompact"},
        )
        self.assertEqual(config["hooks"]["SessionStart"][0]["matcher"], "resume|clear|compact")
        for groups in config["hooks"].values():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertEqual(hook["type"], "command")
                    self.assertIn("$PLUGIN_ROOT", hook["command"])
                    self.assertTrue(hook["command"].startswith("sh -c"))
                    self.assertIn("exit 0", hook["command"])


if __name__ == "__main__":
    unittest.main()
