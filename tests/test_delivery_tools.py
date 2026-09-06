from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TRIAL_SUMMARY = ROOT / "skills" / "context-governance" / "scripts" / "trial_summary.py"
COMPATIBILITY_SMOKE = ROOT / "skills" / "project-bootstrap" / "scripts" / "compatibility_smoke.py"
PACKAGE_RELEASE = ROOT / "scripts" / "package_release.py"
VALIDATE_PACKAGE = ROOT / "scripts" / "validate_package.py"


def load_module(name: str, path: Path):
    scripts = str(path.parent)
    sys.path.insert(0, scripts)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(scripts)


class DeliveryToolTests(unittest.TestCase):
    def test_release_archive_is_validated_from_extracted_plugin(self) -> None:
        packager = load_module("package_release_test", PACKAGE_RELEASE)
        validator = load_module("validate_package_archive_test", VALIDATE_PACKAGE)
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "repokeel.zip"
            count = packager.package(ROOT, archive)
            result = validator.validate_archive(archive, "v0.5.0")
        self.assertGreater(count, 0)
        self.assertTrue(result["archive_valid"], result)
        self.assertEqual(result["hook_commands_checked"], 5)
        self.assertEqual(result["workspace_runs"], 1)
        self.assertEqual(
            result["skills"],
            [
                "context-governance",
                "eng-bounded-delivery",
                "eng-task-start",
                "eng-verified-closeout",
                "project-bootstrap",
            ],
        )

    def test_release_archive_contains_runtime_references_and_shared_helper(self) -> None:
        packager = load_module("package_release_contents_test", PACKAGE_RELEASE)
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "repokeel.zip"
            packager.package(ROOT, archive)
            with zipfile.ZipFile(archive) as package:
                names = set(package.namelist())
        prefix = "repokeel/"
        for relative in (
            "skills/context-governance/assets/handoff.md",
            "skills/context-governance/scripts/workspace_snapshot.py",
            "skills/eng-task-start/references/workspace.md",
            "skills/eng-bounded-delivery/assets/review.md",
            "skills/eng-bounded-delivery/references/domain-patterns.md",
        ):
            self.assertIn(prefix + relative, names)

    def test_extracted_package_default_bootstrap_is_framework_neutral(self) -> None:
        packager = load_module("package_release_bootstrap_test", PACKAGE_RELEASE)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            archive = temporary / "repokeel.zip"
            extracted = temporary / "extracted"
            project = temporary / "external-project"
            project.mkdir()
            (project / "README.md").write_text("project\n", encoding="utf-8")
            packager.package(ROOT, archive)
            with zipfile.ZipFile(archive) as package:
                package.extractall(extracted)
            script = (
                extracted
                / "repokeel"
                / "skills"
                / "project-bootstrap"
                / "scripts"
                / "bootstrap.py"
            )
            environment = os.environ.copy()
            environment["PATH"] = ""
            applied = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--project-root",
                    str(project),
                    "--json",
                ],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            policy = json.loads(
                (project / ".agent-governance" / "context-policy.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("project's already accepted", agents)
            self.assertNotIn("Treat Spec Kit specifications", agents)
            self.assertEqual(policy["authority"]["task_source"], "project-defined")
            self.assertEqual(policy["dependencies"], {})

    def test_source_package_metadata_prepares_one_unreleased_preview(self) -> None:
        validator = load_module("validate_package_source_test", VALIDATE_PACKAGE)
        result = validator.validate(ROOT, exercise_hooks=False)
        self.assertEqual(result["version"], "0.5.0")
        self.assertEqual(result["workspace_runs"], 1)
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
        )
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertEqual(marketplace["plugins"][0]["source"]["ref"], "v0.5.0")

    def test_release_checksum_uses_downloadable_asset_basename(self) -> None:
        validator = load_module("validate_package_release_workflow_test", VALIDATE_PACKAGE)
        valid = (
            'sha256sum "repokeel-${GITHUB_REF_NAME}.zip" '
            '> "repokeel-${GITHUB_REF_NAME}.zip.sha256"\n--prerelease'
        )
        validator._validate_release_workflow(valid)
        with self.assertRaisesRegex(validator.ValidationError, "portable asset basename"):
            validator._validate_release_workflow(
                'sha256sum "dist/repokeel-${GITHUB_REF_NAME}.zip"\n'
                '--prerelease'
            )

    def test_trial_summary_applies_relative_and_absolute_thresholds(self) -> None:
        module = load_module("trial_summary_test", TRIAL_SUMMARY)
        directional = module.summarize(
            [116.522, 115.979, 144.616], [66.787, 57.059, 88.413], 50.0
        )
        self.assertEqual(directional["verdict"], "directional_benefit")
        self.assertFalse(directional["passed_relative_threshold"])
        self.assertTrue(directional["passed_absolute_five_minute_threshold"])
        proven = module.summarize([120, 125, 130], [50, 55, 60], 50.0)
        self.assertEqual(proven["verdict"], "effect_threshold_met")

    def test_compatibility_smoke_runs_governance_lifecycle(self) -> None:
        module = load_module("compatibility_smoke_test", COMPATIBILITY_SMOKE)
        lifecycle = module._governance_smoke()
        self.assertTrue(lifecycle["passed"], lifecycle)
        self.assertTrue(all(lifecycle["checks"].values()))

    def test_compatibility_smoke_requires_exact_versions_and_evidence(self) -> None:
        module = load_module("compatibility_smoke_evidence_test", COMPATIBILITY_SMOKE)
        dependencies = [
            {"name": "spec_kit", "status": "verified", "version": "0.11.1"},
            {"name": "superpowers", "status": "verified", "version": "6.0.0"},
            {
                "name": "speckit_superpowers_bridge",
                "status": "verified",
                "version": "1.1.0",
            },
        ]
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            module.bootstrap, "_report", return_value={"dependencies": dependencies}
        ):
            result = module.evaluate(
                Path(directory), {"ready": True}, {"status": "complete"}
            )
        self.assertTrue(result["passed"], result)
        dependencies[0] = {**dependencies[0], "status": "newer_unverified"}
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            module.bootstrap, "_report", return_value={"dependencies": dependencies}
        ):
            result = module.evaluate(
                Path(directory), {"ready": True}, {"status": "complete"}
            )
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["pinned_dependencies_verified"])

    def test_compatibility_smoke_accepts_real_bridge_readiness_shape(self) -> None:
        module = load_module("compatibility_smoke_bridge_readiness_test", COMPATIBILITY_SMOKE)
        readiness = {
            "required_tools": {"status": "ready", "items": []},
            "namespace": {"status": "ready"},
            "package_files": {"status": "ready", "missing": []},
            "bridge_state": {
                "status": "warning",
                "feature_directory": None,
                "next": "/speckit-specify",
            },
            "agents": {"status": "ready", "items": []},
            "overall_status": "warning",
            "next": "/speckit-specify",
        }
        self.assertTrue(module._evidence_true(readiness, kind="readiness"))
        readiness["required_tools"] = {"status": "warning", "items": []}
        self.assertFalse(module._evidence_true(readiness, kind="readiness"))

    def test_compatibility_smoke_rejects_failed_bridge_state(self) -> None:
        module = load_module("compatibility_smoke_failed_bridge_test", COMPATIBILITY_SMOKE)
        readiness = {
            "required_tools": {"status": "ready"},
            "namespace": {"status": "ready"},
            "package_files": {"status": "ready"},
            "bridge_state": {"status": "failed"},
            "agents": {"status": "ready"},
            "overall_status": "failed",
        }
        self.assertFalse(module._evidence_true(readiness, kind="readiness"))


if __name__ == "__main__":
    unittest.main()
