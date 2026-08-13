from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
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
            archive = Path(directory) / "agent-project-governance.zip"
            count = packager.package(ROOT, archive)
            result = validator.validate_archive(archive, "v0.3.2")
        self.assertGreater(count, 0)
        self.assertTrue(result["archive_valid"], result)
        self.assertEqual(result["hook_commands_checked"], 5)

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


if __name__ == "__main__":
    unittest.main()
