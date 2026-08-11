#!/usr/bin/env python3
"""Validate the developer-preview plugin package without third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


PLUGIN_NAME = "agent-project-governance"
VERSION_RE = re.compile(r"^0\.[0-9]+\.[0-9]+(?:\+codex\.[A-Za-z0-9.-]+)?$")


class ValidationError(RuntimeError):
    pass


def _object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON root must be an object: {path}")
    return value


def _skill_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if "[TODO:" in text:
        raise ValidationError(f"placeholder remains in {path}")
    match = re.match(r"^---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
    if match is None:
        raise ValidationError(f"missing YAML frontmatter: {path}")
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    if set(fields) != {"name", "description"}:
        raise ValidationError(f"skill frontmatter must contain only name and description: {path}")
    if fields["name"] != path.parent.name or not fields["description"]:
        raise ValidationError(f"invalid skill identity: {path}")
    return fields


def _python39(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    try:
        try:
            ast.parse(source, filename=str(path), feature_version=(3, 9))
        except TypeError:
            ast.parse(source, filename=str(path), feature_version=9)
    except SyntaxError as exc:
        raise ValidationError(f"not valid Python 3.9 syntax: {path}:{exc.lineno}: {exc.msg}") from exc


def validate(root: Path, expected_tag: Optional[str] = None) -> dict[str, Any]:
    manifest = _object(root / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != PLUGIN_NAME:
        raise ValidationError("plugin name and folder identity differ")
    version = manifest.get("version")
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise ValidationError("plugin version is not a supported developer-preview SemVer")
    if "hooks" in manifest:
        raise ValidationError("plugin manifest must rely on default hook discovery")
    if expected_tag is not None and expected_tag != f"v{version}":
        raise ValidationError(f"tag {expected_tag} does not match manifest version {version}")

    hooks = _object(root / "hooks" / "hooks.json")
    expected_events = {"SessionStart", "PreCompact", "SubagentStart", "SubagentStop", "Stop"}
    if set(hooks.get("hooks", {})) != expected_events:
        raise ValidationError("hook event set differs from the advisory contract")

    skill_names = []
    for skill_file in sorted((root / "skills").glob("*/SKILL.md")):
        skill_names.append(_skill_frontmatter(skill_file)["name"])
    if skill_names != ["context-governance", "project-bootstrap"]:
        raise ValidationError("expected exactly the two governance skills")

    python_files = sorted((root / "skills").glob("*/scripts/*.py"))
    python_files.extend(sorted((root / "scripts").glob("*.py")))
    for path in python_files:
        _python39(path)

    marketplace = _object(root / ".agents" / "plugins" / "marketplace.json")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1 or entries[0].get("name") != PLUGIN_NAME:
        raise ValidationError("repo marketplace must expose exactly this plugin")
    source = entries[0].get("source")
    if not isinstance(source, dict) or source.get("source") != "url":
        raise ValidationError("public marketplace entry must use a Git-backed root URL")
    if source.get("ref") != f"v{version}":
        raise ValidationError("marketplace ref must pin the manifest release tag")
    release_workflow = (root / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    if "--prerelease" not in release_workflow:
        raise ValidationError("developer-preview releases must be marked as prereleases")
    return {
        "valid": True,
        "plugin": PLUGIN_NAME,
        "version": version,
        "skills": skill_names,
        "python_files_checked": len(python_files),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="validate-package")
    parser.add_argument("--root", default=".")
    parser.add_argument("--tag")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = validate(Path(args.root).expanduser().resolve(), args.tag)
    except (ValidationError, OSError) as exc:
        print(f"validate-package: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
