#!/usr/bin/env python3
"""Verify pinned handoff evidence and the local governance lifecycle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

import bootstrap


WORK_UNIT = (
    Path(__file__).resolve().parents[2]
    / "context-governance"
    / "scripts"
    / "work_unit.py"
)


class SmokeError(RuntimeError):
    pass


def _load_object(path: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SmokeError(f"cannot read {label} evidence: {exc}") from exc
    if not isinstance(value, dict):
        raise SmokeError(f"{label} evidence must be a JSON object")
    return value


def _evidence_true(value: dict[str, Any], *, kind: str) -> bool:
    if kind == "readiness":
        return value.get("ready") is True or value.get("status") in {"ready", "verified", "ok"}
    return value.get("complete") is True or value.get("status") in {"complete", "completed"}


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WORK_UNIT), *arguments, "--project-root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def _governance_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        authority = root / "tasks.md"
        authority.write_text("- [ ] T001 Smoke\n", encoding="utf-8")
        common = ("--work-unit", "compatibility-smoke", "--actor", "main")
        initialized = _run(root, "init", *common, "--authority", "tasks", "tasks.md")
        checkpointed = _run(
            root,
            "checkpoint",
            *common,
            "--summary",
            "Pinned handoff completed.",
            "--next-action",
            "Verify resume and close.",
        )
        bound = _run(root, "bind", *common, "--session", "compatibility-smoke-session")
        resumed = _run(root, "resume", *common, "--strict")
        authority.write_text("- [x] T001 Smoke\n", encoding="utf-8")
        drifted = _run(root, "resume", *common, "--strict")
        reconciled = _run(root, "evaluate", *common)
        authority.write_text("- [ ] T001 Smoke\n", encoding="utf-8")
        isolated = _run(
            root,
            "resume",
            "--work-unit",
            "compatibility-smoke",
            "--actor",
            "another-actor",
        )
        closed = _run(root, "close", *common, "--summary", "Compatibility smoke complete.")
        reconcile_action = None
        try:
            reconcile_action = json.loads(reconciled.stdout).get("primary_action")
        except json.JSONDecodeError:
            pass
        checks = {
            "init": initialized.returncode == 0,
            "checkpoint": checkpointed.returncode == 0,
            "bind": bound.returncode == 0,
            "strict_resume": resumed.returncode == 0,
            "authority_drift": drifted.returncode == 1 and reconcile_action == "RECONCILE",
            "actor_isolation": isolated.returncode == 2,
            "close": closed.returncode == 0,
        }
        return {"passed": all(checks.values()), "checks": checks}


def evaluate(
    root: Path, readiness: dict[str, Any], handoff: dict[str, Any]
) -> dict[str, Any]:
    report = bootstrap._report(root)
    dependencies = {item["name"]: item for item in report["dependencies"]}
    expected_dependencies = {"spec_kit", "superpowers", "speckit_superpowers_bridge"}
    exact_versions = set(dependencies) == expected_dependencies and all(
        item["status"] == "verified" for item in dependencies.values()
    )
    lifecycle = _governance_smoke()
    checks = {
        "pinned_dependencies_verified": exact_versions,
        "bridge_readiness_verified": _evidence_true(readiness, kind="readiness"),
        "handoff_completed": _evidence_true(handoff, kind="handoff"),
        "governance_lifecycle": lifecycle["passed"],
    }
    return {
        "schema_version": "0.3",
        "passed": all(checks.values()),
        "checks": checks,
        "dependencies": dependencies,
        "governance": lifecycle,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="compatibility-smoke")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--bridge-readiness", required=True)
    parser.add_argument("--handoff-result", required=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = bootstrap._project_root(args.project_root)
        readiness = _load_object(args.bridge_readiness, "bridge readiness")
        handoff = _load_object(args.handoff_result, "handoff")
        result = evaluate(root, readiness, handoff)
    except (SmokeError, bootstrap.BootstrapError) as exc:
        print(f"compatibility-smoke: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for name, passed in result["checks"].items():
            print(f"{'PASS' if passed else 'FAIL':>4}  {name}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
