from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_release.py"
WORK_UNIT = ROOT / "skills" / "context-governance" / "scripts" / "work_unit.py"
HISTORICAL_APG_DOCS = (
    ROOT / "docs" / "apg-v1-contract.md",
    ROOT / "docs" / "apg-v1-three-task-value-evaluation.md",
)
STABLE_SKILL_IDS = {
    "context-governance",
    "eng-bounded-delivery",
    "eng-task-start",
    "eng-verified-closeout",
    "project-bootstrap",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepoKeelIdentityTests(unittest.TestCase):
    def test_manifest_and_marketplace_use_repokeel_identity(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
        )
        self.assertEqual(manifest["name"], "repokeel")
        self.assertEqual(manifest["interface"]["displayName"], "RepoKeel")
        self.assertEqual(marketplace["name"], "repokeel")
        self.assertEqual(marketplace["interface"]["displayName"], "RepoKeel")
        self.assertEqual(len(marketplace["plugins"]), 1)
        self.assertEqual(marketplace["plugins"][0]["name"], "repokeel")

    def test_release_archive_uses_repokeel_root(self) -> None:
        packager = load_module("repokeel_package_release", PACKAGER)
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "repokeel-v0.5.0.zip"
            packager.package(ROOT, archive)
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
        self.assertTrue(names)
        self.assertTrue(all(name.startswith("repokeel/") for name in names))

    def test_release_workflow_uses_repokeel_asset_names(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
        self.assertIn('repokeel-${GITHUB_REF_NAME}.zip', workflow)
        self.assertIn('repokeel-${GITHUB_REF_NAME}.zip.sha256', workflow)
        self.assertNotIn('agent-project-governance-${GITHUB_REF_NAME}.zip', workflow)

    def test_legacy_apg_state_is_read_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "legacy-project"
            project.mkdir()
            subprocess.run(
                ["git", "init", "-q", "--initial-branch=main", str(project)],
                check=True,
            )
            tasks = project / "tasks.md"
            tasks.write_text("- [ ] Continue legacy APG work\n", encoding="utf-8")
            timestamp = "2026-08-20T00:00:00+00:00"
            state_path = (
                project
                / ".agent-runtime"
                / "work-units"
                / "legacy-apg"
                / "state.json"
            )
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1",
                        "work_unit_id": "legacy-apg",
                        "actor_id": "main",
                        "parent_work_unit_id": None,
                        "status": "active",
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "authorities": [
                            {
                                "kind": "tasks",
                                "path": "tasks.md",
                                "sha256": hashlib.sha256(tasks.read_bytes()).hexdigest(),
                            }
                        ],
                        "checkpoint": None,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            bound = self.run_work_unit(
                project,
                "bind",
                "--work-unit",
                "legacy-apg",
                "--actor",
                "main",
                "--session",
                "legacy-session",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr)
            before = self.runtime_bytes(project)

            resumed = self.run_work_unit(
                project,
                "resume",
                "--work-unit",
                "legacy-apg",
                "--actor",
                "main",
                "--strict",
            )
            inspected = self.run_work_unit(project, "inspect-workspace")
            evaluated = self.run_work_unit(
                project,
                "evaluate",
                "--work-unit",
                "legacy-apg",
                "--actor",
                "main",
            )
            resolved = self.run_work_unit(
                project,
                "resolve-binding",
                "--session",
                "legacy-session",
            )

            for result in (resumed, inspected, evaluated, resolved):
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(inspected.stdout)["schema"],
                "agent-project-governance.workspace-snapshot.v1",
            )
            self.assertTrue(json.loads(resolved.stdout)["found"])
            self.assertEqual(self.runtime_bytes(project), before)

    def test_skill_ids_and_historical_apg_contracts_are_preserved(self) -> None:
        self.assertEqual(
            {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")},
            STABLE_SKILL_IDS,
        )
        self.assertTrue(all(path.is_file() for path in HISTORICAL_APG_DOCS))
        self.assertTrue(all(path.read_text().startswith("# APG V1") for path in HISTORICAL_APG_DOCS))

    def run_work_unit(
        self, project: Path, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(WORK_UNIT),
                *arguments,
                "--project-root",
                str(project),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def runtime_bytes(self, project: Path) -> dict[Path, bytes]:
        runtime = project / ".agent-runtime"
        return {
            path.relative_to(runtime): path.read_bytes()
            for path in sorted(runtime.rglob("*.json"))
        }


if __name__ == "__main__":
    unittest.main()
