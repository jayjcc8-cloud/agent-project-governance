#!/usr/bin/env python3
"""Validate the developer-preview plugin package without third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional


PLUGIN_NAME = "agent-project-governance"
VERSION_RE = re.compile(r"^0\.[0-9]+\.[0-9]+(?:\+codex\.[A-Za-z0-9.-]+)?$")
HOOK_COMMAND = (
    "sh -c 'adapter=\"$PLUGIN_ROOT/skills/context-governance/scripts/hook_adapter.py\"; "
    'fallback="{\\"continue\\":true,\\"systemMessage\\":\\"Context governance hook '
    'unavailable; continuing without governance advice.\\"}"; '
    'if command -v python3 >/dev/null 2>&1 && [ -r "$adapter" ]; then '
    'output="$(python3 "$adapter" 2>/dev/null)" && [ -n "$output" ] && '
    '{ printf "%s\\n" "$output"; exit 0; }; fi; '
    'printf "%s\\n" "$fallback"; exit 0\''
)
HOOK_EVENTS = {"SessionStart", "PreCompact", "SubagentStart", "SubagentStop", "Stop"}


class ValidationError(RuntimeError):
    pass


def _validate_release_workflow(release_workflow: str) -> None:
    if "--prerelease" not in release_workflow:
        raise ValidationError("developer-preview releases must be marked as prereleases")
    if 'sha256sum "dist/' in release_workflow:
        raise ValidationError("release checksum must contain a portable asset basename")
    if 'sha256sum "agent-project-governance-${GITHUB_REF_NAME}.zip"' not in release_workflow:
        raise ValidationError("release workflow must checksum the downloadable asset basename")


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


def _hook_commands(hooks: dict[str, Any]) -> list[str]:
    events = hooks.get("hooks")
    if not isinstance(events, dict) or set(events) != HOOK_EVENTS:
        raise ValidationError("hook event set differs from the advisory contract")
    commands: list[str] = []
    for groups in events.values():
        if not isinstance(groups, list):
            raise ValidationError("hook event groups must be arrays")
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise ValidationError("hook group is invalid")
            for hook in group["hooks"]:
                if not isinstance(hook, dict) or hook.get("type") != "command":
                    raise ValidationError("all governance hooks must be commands")
                command = hook.get("command")
                if command != HOOK_COMMAND:
                    raise ValidationError("hook command must use the reviewed fail-open launcher")
                commands.append(command)
    if len(commands) != len(HOOK_EVENTS):
        raise ValidationError("expected exactly one command for every advisory hook event")
    return commands


def _exercise_hook(root: Path, plugin_root: Path) -> None:
    if os.name == "nt" or shutil.which("sh") is None:
        return
    payload = {
        "hook_event_name": "Stop",
        "session_id": "package-validation",
        "cwd": str(root),
        "model": "package-validation",
    }
    environment = os.environ.copy()
    environment["PLUGIN_ROOT"] = str(plugin_root)
    try:
        result = subprocess.run(
            ["sh", "-c", HOOK_COMMAND],
            input=json.dumps(payload),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError("hook launcher exceeded its five-second fail-open budget") from exc
    if result.returncode != 0:
        raise ValidationError(f"hook launcher did not fail open: {result.stderr.strip()}")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("hook launcher did not emit one valid JSON object") from exc
    if not isinstance(output, dict) or output.get("continue") is not True or "decision" in output:
        raise ValidationError("hook launcher emitted a blocking or invalid response")


def _exercise_hooks(root: Path) -> int:
    if os.name == "nt" or shutil.which("sh") is None:
        return 0
    _exercise_hook(root, root)
    with tempfile.TemporaryDirectory() as directory:
        _exercise_hook(root, Path(directory))
    return 2


def validate(
    root: Path,
    expected_tag: Optional[str] = None,
    exercise_hooks: bool = True,
    source_layout: bool = True,
) -> dict[str, Any]:
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
    hook_commands = _hook_commands(hooks)

    skill_names = []
    for skill_file in sorted((root / "skills").glob("*/SKILL.md")):
        skill_names.append(_skill_frontmatter(skill_file)["name"])
    if skill_names != ["context-governance", "project-bootstrap"]:
        raise ValidationError("expected exactly the two governance skills")

    python_files = sorted((root / "skills").glob("*/scripts/*.py"))
    python_files.extend(sorted((root / "scripts").glob("*.py")))
    for path in python_files:
        _python39(path)

    if source_layout:
        marketplace = _object(root / ".agents" / "plugins" / "marketplace.json")
        entries = marketplace.get("plugins")
        if (
            not isinstance(entries, list)
            or len(entries) != 1
            or entries[0].get("name") != PLUGIN_NAME
        ):
            raise ValidationError("repo marketplace must expose exactly this plugin")
        source = entries[0].get("source")
        if not isinstance(source, dict) or source.get("source") != "url":
            raise ValidationError("public marketplace entry must use a Git-backed root URL")
        if source.get("ref") != f"v{version}":
            raise ValidationError("marketplace ref must pin the manifest release tag")
        release_workflow = (root / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        _validate_release_workflow(release_workflow)
    hook_runs = _exercise_hooks(root) if exercise_hooks else 0
    return {
        "valid": True,
        "plugin": PLUGIN_NAME,
        "version": version,
        "skills": skill_names,
        "python_files_checked": len(python_files),
        "hook_commands_checked": len(hook_commands),
        "hook_runs": hook_runs,
        "source_layout": source_layout,
    }


def validate_archive(archive: Path, expected_tag: Optional[str] = None) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(archive) as package:
            members = package.infolist()
            if not members:
                raise ValidationError("release archive is empty")
            for member in members:
                path = Path(member.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise ValidationError(f"unsafe release archive member: {member.filename}")
                mode = member.external_attr >> 16
                if (mode & 0o170000) == 0o120000:
                    raise ValidationError(f"release archive contains a symlink: {member.filename}")
            roots = {Path(member.filename).parts[0] for member in members}
            if roots != {PLUGIN_NAME}:
                raise ValidationError("release archive must contain exactly one plugin root")
            with tempfile.TemporaryDirectory() as directory:
                package.extractall(directory)
                result = validate(
                    Path(directory) / PLUGIN_NAME,
                    expected_tag,
                    source_layout=False,
                )
    except zipfile.BadZipFile as exc:
        raise ValidationError(f"invalid release archive: {exc}") from exc
    return {**result, "archive": str(archive), "archive_valid": True}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="validate-package")
    parser.add_argument("--root", default=".")
    parser.add_argument("--archive")
    parser.add_argument("--tag")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.archive:
            result = validate_archive(Path(args.archive).expanduser().resolve(), args.tag)
        else:
            result = validate(Path(args.root).expanduser().resolve(), args.tag)
    except (ValidationError, OSError) as exc:
        print(f"validate-package: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
