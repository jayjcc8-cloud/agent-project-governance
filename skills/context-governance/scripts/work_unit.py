#!/usr/bin/env python3
"""Deterministic actor-scoped work-unit checkpoint and resume state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_TEXT_LENGTH = 4096
_MAX_LIST_ITEMS = 32


class GovernanceError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identifier(value: str, label: str) -> str:
    if _ID_PATTERN.fullmatch(value) is None:
        raise GovernanceError(
            f"{label} must be 1-128 letters, digits, dots, underscores, or hyphens"
        )
    return value


def _bounded_text(value: str, label: str) -> str:
    text = value.strip()
    if not text:
        raise GovernanceError(f"{label} cannot be empty")
    if len(text) > _MAX_TEXT_LENGTH:
        raise GovernanceError(
            f"{label} exceeds the {_MAX_TEXT_LENGTH}-character checkpoint limit"
        )
    return text


def _bounded_list(values: list[str], label: str) -> list[str]:
    if len(values) > _MAX_LIST_ITEMS:
        raise GovernanceError(f"{label} accepts at most {_MAX_LIST_ITEMS} entries")
    return [_bounded_text(value, label) for value in values]


def _project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise GovernanceError(f"project root is not a directory: {value}")
    return root


def _unit_path(root: Path, work_unit_id: str) -> Path:
    work_unit = _identifier(work_unit_id, "work-unit ID")
    path = root / ".agent-runtime" / "work-units" / work_unit / "state.json"
    if not path.parent.resolve().is_relative_to(root):
        raise GovernanceError("work-unit state escapes the project root")
    return path


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _authority(root: Path, kind: str, value: str) -> dict[str, str]:
    _identifier(kind, "authority kind")
    candidate = Path(value)
    path = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if not path.is_relative_to(root):
        raise GovernanceError(f"authority must be inside the project root: {value}")
    if not path.is_file():
        raise GovernanceError(f"authority is not a file: {value}")
    return {
        "kind": kind,
        "path": path.relative_to(root).as_posix(),
        "sha256": _digest(path),
    }


def _read_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GovernanceError(f"work unit does not exist: {path.parent.name}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"cannot read work-unit state: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != SCHEMA_VERSION:
        raise GovernanceError("unsupported or invalid work-unit state")
    if document.get("work_unit_id") != path.parent.name:
        raise GovernanceError("work-unit state ID does not match its directory")
    actor_id = document.get("actor_id")
    if not isinstance(actor_id, str):
        raise GovernanceError("work-unit state has an invalid actor ID")
    _identifier(actor_id, "stored actor ID")
    authorities = document.get("authorities")
    if not isinstance(authorities, list):
        raise GovernanceError("work-unit state has invalid authorities")
    for item in authorities:
        if not isinstance(item, dict):
            raise GovernanceError("work-unit state has an invalid authority entry")
        if not all(isinstance(item.get(key), str) for key in ("kind", "path", "sha256")):
            raise GovernanceError("work-unit state has an incomplete authority entry")
    return document


def _require_actor(state: dict[str, Any], actor_id: str) -> None:
    actor = _identifier(actor_id, "actor ID")
    if state.get("actor_id") != actor:
        raise GovernanceError(
            f"work unit belongs to actor {state.get('actor_id')!r}, not {actor!r}"
        )


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".state.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _print(document: dict[str, Any]) -> None:
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))


def _init(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    if path.exists():
        raise GovernanceError(f"work unit already exists: {args.work_unit}")
    actor = _identifier(args.actor, "actor ID")
    parent = (
        _identifier(args.parent_work_unit, "parent work-unit ID")
        if args.parent_work_unit
        else None
    )
    if parent == args.work_unit:
        raise GovernanceError("a work unit cannot be its own parent")
    authorities = [_authority(root, kind, value) for kind, value in args.authority]
    created_at = _now()
    state = {
        "schema_version": SCHEMA_VERSION,
        "work_unit_id": args.work_unit,
        "actor_id": actor,
        "parent_work_unit_id": parent,
        "status": "active",
        "created_at": created_at,
        "updated_at": created_at,
        "authorities": authorities,
        "checkpoint": None,
    }
    _write_state(path, state)
    _print(state)
    return 0


def _checkpoint(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    state = _read_state(path)
    _require_actor(state, args.actor)
    if state.get("status") != "active":
        raise GovernanceError("only active work units can be checkpointed")
    refreshed = [
        _authority(root, str(item["kind"]), str(item["path"]))
        for item in state.get("authorities", [])
    ]
    prior = state.get("checkpoint")
    sequence = int(prior.get("sequence", 0)) + 1 if isinstance(prior, dict) else 1
    recorded_at = _now()
    summary = _bounded_text(args.summary, "summary")
    next_action = _bounded_text(args.next_action, "next action")
    findings = _bounded_list(args.finding, "finding")
    failed_attempts = _bounded_list(args.failed_attempt, "failed attempt")
    state["authorities"] = refreshed
    state["checkpoint"] = {
        "sequence": sequence,
        "recorded_at": recorded_at,
        "summary": summary,
        "next_action": next_action,
        "findings": findings,
        "failed_attempts": failed_attempts,
    }
    state["updated_at"] = recorded_at
    _write_state(path, state)
    _print(state)
    return 0


def _resume(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    state = _read_state(path)
    _require_actor(state, args.actor)
    statuses: list[dict[str, Any]] = []
    matches = True
    for item in state.get("authorities", []):
        authority_path = (root / str(item["path"])).resolve()
        exists = authority_path.is_relative_to(root) and authority_path.is_file()
        current_digest = _digest(authority_path) if exists else None
        item_matches = exists and current_digest == item.get("sha256")
        matches = matches and item_matches
        statuses.append(
            {
                "kind": item.get("kind"),
                "path": item.get("path"),
                "exists": exists,
                "checkpoint_sha256": item.get("sha256"),
                "current_sha256": current_digest,
                "matches_checkpoint": item_matches,
            }
        )
    _print(
        {
            "schema_version": SCHEMA_VERSION,
            "work_unit_id": state.get("work_unit_id"),
            "actor_id": state.get("actor_id"),
            "parent_work_unit_id": state.get("parent_work_unit_id"),
            "status": state.get("status"),
            "checkpoint": state.get("checkpoint"),
            "authorities_match_checkpoint": matches,
            "authority_status": statuses,
        }
    )
    return 1 if args.strict and not matches else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="work-unit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "checkpoint", "resume"):
        command = subparsers.add_parser(name)
        command.add_argument("--project-root", required=True)
        command.add_argument("--work-unit", required=True)
        command.add_argument("--actor", required=True)
    initialize = subparsers.choices["init"]
    initialize.add_argument("--parent-work-unit")
    initialize.add_argument("--authority", nargs=2, action="append", default=[])
    checkpoint = subparsers.choices["checkpoint"]
    checkpoint.add_argument("--summary", required=True)
    checkpoint.add_argument("--next-action", required=True)
    checkpoint.add_argument("--finding", action="append", default=[])
    checkpoint.add_argument("--failed-attempt", action="append", default=[])
    resume = subparsers.choices["resume"]
    resume.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            return _init(args)
        if args.command == "checkpoint":
            return _checkpoint(args)
        return _resume(args)
    except GovernanceError as exc:
        print(f"context-governance: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
