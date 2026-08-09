#!/usr/bin/env python3
"""Preview, apply, and check a repository's Agent Project Governance setup."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.2"
_VERSION_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")
_BRIDGE_NAME = "speckit-superpowers-bridge"


class BootstrapError(RuntimeError):
    """Invalid bootstrap input or unreadable local state."""


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise BootstrapError(f"project root is not a directory: {value}")
    return root


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BootstrapError(f"JSON file must contain an object: {path}")
    return value


def _compatibility() -> dict[str, Any]:
    return _load_json(_skill_root() / "references" / "compatibility.json")


def _version(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = _VERSION_RE.search(value)
    return tuple(int(part) for part in match.groups()) if match else None


def _version_text(value: tuple[int, int, int] | None) -> str | None:
    return ".".join(str(part) for part in value) if value else None


def _classify_version(
    installed: tuple[int, int, int] | None,
    *,
    minimum: str,
    verified: str,
) -> str:
    if installed is None:
        return "unknown_version"
    minimum_value = _version(minimum)
    verified_value = _version(verified)
    assert minimum_value is not None and verified_value is not None
    if installed < minimum_value:
        return "incompatible"
    if installed == verified_value:
        return "verified"
    if installed > verified_value:
        return "newer_unverified"
    return "unknown_version"


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _detect_spec_kit(root: Path, compatibility: dict[str, Any]) -> dict[str, Any]:
    config = compatibility["spec_kit"]
    executable = shutil.which("specify")
    project_present = (root / ".specify").is_dir()
    result = _run([executable, "--version"]) if executable else None
    installed = _version((result.stdout + result.stderr) if result else None)
    if not executable or not project_present:
        status = "missing"
    else:
        status = _classify_version(
            installed,
            minimum=config["minimum"],
            verified=config["verified"],
        )
    return {
        "name": "spec_kit",
        "status": status,
        "version": _version_text(installed),
        "cli_present": bool(executable),
        "project_present": project_present,
        "verified_version": config["verified"],
        "instruction": config["install"],
    }


def _plugin_inventory() -> dict[str, Any] | None:
    executable = shutil.which("codex")
    if not executable:
        return None
    result = _run([executable, "plugin", "list", "--available", "--json"])
    if result is None or result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _detect_superpowers(compatibility: dict[str, Any]) -> dict[str, Any]:
    config = compatibility["superpowers"]
    inventory = _plugin_inventory()
    installed_entry = None
    available_entry = None
    if inventory:
        for entry in inventory.get("installed", []):
            if isinstance(entry, dict) and entry.get("name") == "superpowers":
                installed_entry = entry
                break
        for entry in inventory.get("available", []):
            if isinstance(entry, dict) and entry.get("name") == "superpowers":
                available_entry = entry
                break
    if installed_entry and installed_entry.get("enabled"):
        installed = _version(str(installed_entry.get("version", "")))
        status = _classify_version(
            installed,
            minimum=config["minimum"],
            verified=config["verified"],
        )
    else:
        installed = None
        status = "missing"
    candidate = available_entry or installed_entry or {}
    plugin_id = candidate.get("pluginId") if isinstance(candidate, dict) else None
    instruction = f"codex plugin add {plugin_id}" if plugin_id else config["install_fallback"]
    return {
        "name": "superpowers",
        "status": status,
        "version": _version_text(installed),
        "installed": bool(installed_entry),
        "enabled": bool(installed_entry and installed_entry.get("enabled")),
        "verified_version": config["verified"],
        "instruction": instruction,
    }


def _bridge_version(directory: Path) -> tuple[int, int, int] | None:
    candidates = list(directory.rglob("verified-versions.json"))
    candidates.extend(directory.glob("extension.y*ml"))
    candidates.extend(directory.glob("manifest.y*ml"))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.search(
            r"(?:bridge|speckit-superpowers-bridge)[^\n\r]{0,160}?(\d+\.\d+\.\d+)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return _version(match.group(1))
    return None


def _detect_bridge(root: Path, compatibility: dict[str, Any]) -> dict[str, Any]:
    config = compatibility["speckit_superpowers_bridge"]
    directory = root / ".specify" / "extensions" / _BRIDGE_NAME
    if not directory.is_dir():
        status = "missing"
        installed = None
    else:
        installed = _bridge_version(directory)
        status = _classify_version(
            installed,
            minimum=config["minimum"],
            verified=config["verified"],
        )
    return {
        "name": "speckit_superpowers_bridge",
        "status": status,
        "version": _version_text(installed),
        "project_present": directory.is_dir(),
        "verified_version": config["verified"],
        "instruction": config["install"],
    }


def _asset(name: str) -> bytes:
    return (_skill_root() / "assets" / name).read_bytes()


def _file_operations(root: Path) -> list[dict[str, Any]]:
    mappings = (
        (".agent-governance/context-policy.json", "context-policy.json"),
        ("AGENTS.md", "AGENTS.md"),
        ("docs/adr/README.md", "adr-README.md"),
        ("docs/adr/ADR-template.md", "ADR-template.md"),
    )
    operations: list[dict[str, Any]] = []
    for target_name, asset_name in mappings:
        path = root / target_name
        expected = _asset(asset_name)
        if not path.exists():
            action = "create"
        elif path.is_file() and path.read_bytes() == expected:
            action = "skip"
        else:
            action = "conflict"
        operations.append({"path": target_name, "action": action, "asset": asset_name})
    ignore = root / ".gitignore"
    expected_line = ".agent-runtime/"
    if not ignore.exists():
        ignore_action = "create"
    elif ignore.is_file() and expected_line in {
        line.strip() for line in ignore.read_text(encoding="utf-8").splitlines()
    }:
        ignore_action = "skip"
    else:
        ignore_action = "conflict"
    operations.append(
        {"path": ".gitignore", "action": ignore_action, "expected_line": expected_line}
    )
    return operations


def _repository_kind(root: Path) -> str:
    ignored = {".git", ".agent-runtime"}
    entries = [path for path in root.iterdir() if path.name not in ignored]
    return "greenfield" if not entries else "brownfield"


def _report(root: Path) -> dict[str, Any]:
    compatibility = _compatibility()
    dependencies = [
        _detect_spec_kit(root, compatibility),
        _detect_superpowers(compatibility),
        _detect_bridge(root, compatibility),
    ]
    operations = _file_operations(root)
    ready = all(item["status"] == "verified" for item in dependencies) and all(
        item["action"] == "skip" for item in operations
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": str(root),
        "repository_kind": _repository_kind(root),
        "ready": ready,
        "operations": operations,
        "dependencies": dependencies,
    }


def _atomic_create(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(str(temporary), str(path))
        except FileExistsError as exc:
            raise BootstrapError(f"refusing to overwrite existing file: {path}") from exc
        except OSError:
            # Windows or a restricted filesystem may not allow hard links. Exclusive
            # creation still preserves the never-overwrite contract.
            try:
                with path.open("xb") as target:
                    target.write(content)
                    target.flush()
                    os.fsync(target.fileno())
            except FileExistsError as exc:
                raise BootstrapError(f"refusing to overwrite existing file: {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _apply(root: Path, report: dict[str, Any]) -> list[str]:
    created: list[str] = []
    for operation in report["operations"]:
        if operation["action"] != "create":
            continue
        target = root / operation["path"]
        content = (
            b".agent-runtime/\n"
            if operation["path"] == ".gitignore"
            else _asset(operation["asset"])
        )
        _atomic_create(target, content)
        created.append(operation["path"])
    return created


def _print_human(command: str, report: dict[str, Any]) -> None:
    print(f"Project governance {command}: {report['project_root']}")
    print(f"Repository: {report['repository_kind']}")
    for operation in report["operations"]:
        print(f"{operation['action']:>8}  {operation['path']}")
    for dependency in report["dependencies"]:
        suffix = f" {dependency['version']}" if dependency.get("version") else ""
        print(f"{dependency['status']:>18}  {dependency['name']}{suffix}")
        if dependency["status"] != "verified":
            print(f"  Next: {dependency['instruction']}")
    if report.get("created"):
        print("Created: " + ", ".join(report["created"]))
    print("Ready: " + ("yes" if report["ready"] else "no"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "check", "apply"):
        command = subparsers.add_parser(name)
        command.add_argument("--project-root", required=True)
        command.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = _project_root(args.project_root)
        report = _report(root)
        if args.command == "apply":
            created = _apply(root, report)
            report = {**_report(root), "created": created}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_human(args.command, report)
        if args.command == "plan":
            return 0
        return 0 if report["ready"] else 1
    except (BootstrapError, OSError) as exc:
        print(f"project-bootstrap: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
