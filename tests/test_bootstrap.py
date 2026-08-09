from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "project-bootstrap"
    / "scripts"
    / "bootstrap.py"
)


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("project_bootstrap", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BootstrapTests(unittest.TestCase):
    def run_cli(self, root: Path, command: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = ""
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, "--project-root", str(root), "--json"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_plan_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = list(root.iterdir())
            planned = self.run_cli(root, "plan")
            self.assertEqual(planned.returncode, 0, planned.stderr)
            report = json.loads(planned.stdout)
            self.assertEqual(list(root.iterdir()), before)
            self.assertTrue(all(item["action"] == "create" for item in report["operations"]))
            self.assertFalse(report["ready"])

    def test_apply_creates_only_missing_files_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            applied = self.run_cli(root, "apply")
            self.assertEqual(applied.returncode, 1, applied.stderr)
            report = json.loads(applied.stdout)
            self.assertEqual(len(report["created"]), 5)
            self.assertTrue((root / ".agent-governance" / "context-policy.json").is_file())
            self.assertEqual((root / ".gitignore").read_text(encoding="utf-8"), ".agent-runtime/\n")
            second = self.run_cli(root, "apply")
            self.assertEqual(second.returncode, 1, second.stderr)
            self.assertEqual(json.loads(second.stdout)["created"], [])

    def test_existing_files_are_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents = root / "AGENTS.md"
            ignore = root / ".gitignore"
            agents.write_text("user-owned\n", encoding="utf-8")
            ignore.write_text("build/\n", encoding="utf-8")
            applied = self.run_cli(root, "apply")
            self.assertEqual(applied.returncode, 1, applied.stderr)
            report = json.loads(applied.stdout)
            actions = {item["path"]: item["action"] for item in report["operations"]}
            self.assertEqual(actions["AGENTS.md"], "conflict")
            self.assertEqual(actions[".gitignore"], "conflict")
            self.assertEqual(agents.read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(ignore.read_text(encoding="utf-8"), "build/\n")

    def test_check_returns_one_when_dependencies_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checked = self.run_cli(root, "check")
            self.assertEqual(checked.returncode, 1, checked.stderr)
            statuses = {item["name"]: item["status"] for item in json.loads(checked.stdout)["dependencies"]}
            self.assertEqual(statuses["spec_kit"], "missing")
            self.assertEqual(statuses["superpowers"], "missing")
            self.assertEqual(statuses["speckit_superpowers_bridge"], "missing")

    def test_compatibility_classifier_is_conservative(self) -> None:
        module = load_bootstrap_module()
        classify = module._classify_version
        self.assertEqual(
            classify((0, 11, 1), minimum="0.8.10", verified="0.11.1"), "verified"
        )
        self.assertEqual(
            classify((0, 16, 1), minimum="0.8.10", verified="0.11.1"),
            "newer_unverified",
        )
        self.assertEqual(
            classify((0, 7, 9), minimum="0.8.10", verified="0.11.1"), "incompatible"
        )
        self.assertEqual(
            classify(None, minimum="0.8.10", verified="0.11.1"), "unknown_version"
        )


if __name__ == "__main__":
    unittest.main()
