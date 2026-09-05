from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock


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
    def run_cli(
        self, root: Path, command: str, *, profile: Optional[str] = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = ""
        arguments = [
            sys.executable,
            str(SCRIPT),
            command,
            "--project-root",
            str(root),
            "--json",
        ]
        if profile is not None:
            arguments.extend(("--profile", profile))
        return subprocess.run(
            arguments,
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
            actions = {item["path"]: item["action"] for item in report["operations"]}
            self.assertEqual(report["profile"], "existing-project")
            self.assertEqual(actions["AGENTS.md"], "create")
            self.assertEqual(actions["docs/adr/README.md"], "not_applicable")
            self.assertTrue(report["core_ready"])
            self.assertTrue(report["ready"])

    def test_apply_creates_only_missing_files_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            applied = self.run_cli(root, "apply")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            report = json.loads(applied.stdout)
            self.assertEqual(
                report["created"],
                [".agent-governance/context-policy.json", "AGENTS.md", ".gitignore"],
            )
            self.assertTrue((root / ".agent-governance" / "context-policy.json").is_file())
            self.assertFalse((root / "docs" / "adr").exists())
            self.assertEqual((root / ".gitignore").read_text(encoding="utf-8"), ".agent-runtime/\n")
            second = self.run_cli(root, "apply")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["created"], [])

    def test_default_and_explicit_existing_project_create_neutral_content(self) -> None:
        with tempfile.TemporaryDirectory() as default_directory, tempfile.TemporaryDirectory() as explicit_directory:
            default_root = Path(default_directory)
            explicit_root = Path(explicit_directory)
            (default_root / "README.md").write_text("project\n", encoding="utf-8")
            (explicit_root / "README.md").write_text("project\n", encoding="utf-8")

            default = self.run_cli(default_root, "apply")
            explicit = self.run_cli(
                explicit_root, "apply", profile="existing-project"
            )
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertEqual(explicit.returncode, 0, explicit.stderr)

            default_agents = (default_root / "AGENTS.md").read_text(encoding="utf-8")
            explicit_agents = (explicit_root / "AGENTS.md").read_text(encoding="utf-8")
            default_policy = json.loads(
                (default_root / ".agent-governance" / "context-policy.json").read_text(
                    encoding="utf-8"
                )
            )
            explicit_policy = json.loads(
                (explicit_root / ".agent-governance" / "context-policy.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(default_agents, explicit_agents)
            self.assertEqual(default_policy, explicit_policy)
            self.assertIn("project's already accepted", default_agents)
            self.assertNotIn("Treat Spec Kit specifications", default_agents)
            self.assertNotIn("Use Superpowers", default_agents)
            self.assertEqual(
                default_policy["authority"]["task_source"], "project-defined"
            )
            self.assertEqual(default_policy["dependencies"], {})

    def test_existing_files_are_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents = root / "AGENTS.md"
            policy = root / ".agent-governance" / "context-policy.json"
            ignore = root / ".gitignore"
            agents.write_text("user-owned\n", encoding="utf-8")
            policy.parent.mkdir(parents=True)
            policy.write_text('{"user": "owned"}\n', encoding="utf-8")
            ignore.write_text("build/\n", encoding="utf-8")
            before = {
                "agents": agents.read_bytes(),
                "policy": policy.read_bytes(),
                "ignore": ignore.read_bytes(),
            }
            planned = self.run_cli(root, "plan")
            checked = self.run_cli(root, "check")
            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            for output in (planned, checked):
                operations = {
                    item["path"]: item for item in json.loads(output.stdout)["operations"]
                }
                self.assertEqual(
                    operations["AGENTS.md"]["asset"], "AGENTS-existing-project.md"
                )
                self.assertEqual(
                    operations[".agent-governance/context-policy.json"]["asset"],
                    "context-policy-existing-project.json",
                )
                self.assertFalse(
                    any(
                        "Spec Kit" in rule or "Superpowers" in rule
                        for rule in operations["AGENTS.md"]["reconciliation"][
                            "missing_template_rules"
                        ]
                    )
                )
            self.assertEqual(agents.read_bytes(), before["agents"])
            self.assertEqual(policy.read_bytes(), before["policy"])
            self.assertEqual(ignore.read_bytes(), before["ignore"])
            applied = self.run_cli(root, "apply")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            report = json.loads(applied.stdout)
            actions = {item["path"]: item["action"] for item in report["operations"]}
            self.assertEqual(actions["AGENTS.md"], "user_owned")
            self.assertEqual(actions[".gitignore"], "user_owned")
            operations = {item["path"]: item for item in report["operations"]}
            agents_advice = operations["AGENTS.md"]["reconciliation"]
            self.assertEqual(agents_advice["strategy"], "manual_merge")
            self.assertEqual(agents_advice["reason_code"], "USER_OWNED_AGENTS_DIFFERS")
            self.assertGreater(len(agents_advice["missing_template_rules"]), 0)
            self.assertFalse(
                any(
                    "Spec Kit" in rule or "Superpowers" in rule
                    for rule in agents_advice["missing_template_rules"]
                )
            )
            self.assertEqual(
                operations[".gitignore"]["reconciliation"],
                {"strategy": "append_line_manually", "line": ".agent-runtime/"},
            )
            self.assertEqual(agents.read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(policy.read_text(encoding="utf-8"), '{"user": "owned"}\n')
            self.assertEqual(ignore.read_text(encoding="utf-8"), "build/\n")
            second = self.run_cli(root, "apply")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["created"], [])

    def test_default_existing_project_does_not_probe_optional_frameworks(self) -> None:
        module = load_bootstrap_module()
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            module, "_detect_spec_kit", side_effect=AssertionError("must not probe Spec Kit")
        ), mock.patch.object(
            module, "_detect_superpowers", side_effect=AssertionError("must not probe Superpowers")
        ), mock.patch.object(
            module, "_detect_bridge", side_effect=AssertionError("must not probe bridge")
        ):
            root = Path(directory)
            (root / "AGENTS.md").write_text("user-owned\n", encoding="utf-8")
            before = (root / "AGENTS.md").read_bytes()
            report = module._report(root, profile="existing-project")
            self.assertTrue(report["ready"])
            self.assertTrue(report["core_ready"])
            self.assertEqual(
                {item["status"] for item in report["dependencies"]}, {"not_applicable"}
            )
            self.assertEqual(
                {item["path"]: item["action"] for item in report["operations"]}[
                    "AGENTS.md"
                ],
                "user_owned",
            )
            self.assertEqual((root / "AGENTS.md").read_bytes(), before)

    def test_explicit_spec_kit_stack_preserves_missing_dependency_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checked = self.run_cli(root, "check", profile="spec-kit-stack")
            self.assertEqual(checked.returncode, 1, checked.stderr)
            result = json.loads(checked.stdout)
            self.assertEqual(result["profile"], "spec-kit-stack")
            statuses = {item["name"]: item["status"] for item in result["dependencies"]}
            self.assertEqual(statuses["spec_kit"], "missing")
            self.assertEqual(statuses["superpowers"], "missing")
            self.assertEqual(statuses["speckit_superpowers_bridge"], "missing")

    def test_explicit_spec_kit_stack_apply_retains_legacy_asset_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            applied = self.run_cli(root, "apply", profile="spec-kit-stack")
            self.assertEqual(applied.returncode, 1, applied.stderr)
            result = json.loads(applied.stdout)
            self.assertEqual(len(result["created"]), 5)
            self.assertTrue((root / "docs" / "adr" / "README.md").is_file())
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            policy = json.loads(
                (root / ".agent-governance" / "context-policy.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("Treat Spec Kit specifications", agents)
            self.assertIn("Use Superpowers", agents)
            self.assertEqual(policy["authority"]["task_source"], "spec-kit")
            self.assertEqual(
                policy["dependencies"],
                {
                    "spec_kit": "external",
                    "superpowers": "external",
                    "speckit_superpowers_bridge": "external",
                },
            )

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
