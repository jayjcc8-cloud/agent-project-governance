#!/usr/bin/env python3
"""Deterministic actor-scoped work-unit governance for local AI projects."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Optional


SCHEMA_VERSION = "0.4"
LEGACY_SCHEMA_VERSIONS = {"0.1", "0.2", "0.3"}
SUPPORTED_SCHEMA_VERSIONS = LEGACY_SCHEMA_VERSIONS | {SCHEMA_VERSION}
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)/(?P<resource>issues|pull)/(?P<number>[1-9][0-9]*)/?$"
)
_MAX_TEXT_LENGTH = 4096
_MAX_LIST_ITEMS = 32
_MAX_EXTERNAL_ID_LENGTH = 512
_LOCK_TIMEOUT_SECONDS = 5.0
_STALE_LOCK_SECONDS = 30.0
_GITHUB_LEGACY_PROJECTION = "github-v1"
_GITHUB_PROJECTION = "github-v2"
_GITHUB_PROJECTIONS = {_GITHUB_LEGACY_PROJECTION, _GITHUB_PROJECTION}

EVENTS = (
    "manual",
    "session-start",
    "pre-compact",
    "subagent-start",
    "subagent-stop",
    "stop",
)
SIGNALS = (
    "goal-changed",
    "implementation-drift",
    "feature-complete",
    "context-noisy",
    "repeated-failure",
    "durable-decision",
    "durable-agent-rule",
    "independent-work",
    "new-work-unit",
    "exploration-heavy",
    "handoff-required",
)
_ACTION_PRIORITY = {
    "RECONCILE": 0,
    "UPDATE_SPEC": 1,
    "CONVERGE": 2,
    "CLOSE": 3,
    "CHECKPOINT": 4,
    "DEBUG_REVIEW": 5,
    "PROMOTE_ADR": 6,
    "PROMOTE_AGENTS": 7,
    "WORKTREE": 8,
    "NEW_THREAD": 9,
    "SUBAGENT": 10,
    "HANDOFF": 11,
    "COMPACT": 12,
    "RESUME": 13,
    "CONTINUE": 14,
}


class GovernanceError(RuntimeError):
    """Invalid input, state, ownership, path, or I/O condition."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identifier(value: str, label: str) -> str:
    if _ID_PATTERN.fullmatch(value) is None:
        raise GovernanceError(
            f"{label} must be 1-128 letters, digits, dots, underscores, or hyphens"
        )
    return value


def _external_identifier(value: str, label: str) -> str:
    text = value.strip()
    if not text or len(text) > _MAX_EXTERNAL_ID_LENGTH or "\x00" in text:
        raise GovernanceError(
            f"{label} must be 1-{_MAX_EXTERNAL_ID_LENGTH} non-null characters"
        )
    return text


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


def _timestamp(value: Any, label: str, *, nullable: bool = False) -> Optional[str]:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise GovernanceError(f"work-unit state has an invalid {label}")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GovernanceError(f"work-unit state has an invalid {label}") from exc
    return value


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


def _binding_key(session_id: str, agent_id: Optional[str]) -> str:
    session = _external_identifier(session_id, "session ID")
    agent = _external_identifier(agent_id, "agent ID") if agent_id else ""
    return hashlib.sha256(f"{session}\0{agent}".encode("utf-8")).hexdigest()


def _binding_path(root: Path, session_id: str, agent_id: Optional[str]) -> Path:
    return (
        root
        / ".agent-runtime"
        / "session-bindings"
        / f"{_binding_key(session_id, agent_id)}.json"
    )


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _safe_relative_path(value: Any, label: str = "authority path") -> str:
    if not isinstance(value, str) or not value:
        raise GovernanceError(f"work-unit state has an invalid {label}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise GovernanceError(f"work-unit state has an unsafe {label}")
    normalized = pure.as_posix()
    if normalized in ("", "."):
        raise GovernanceError(f"work-unit state has an invalid {label}")
    return normalized


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


def _github_projection(payload: dict[str, Any], resource: str) -> dict[str, Any]:
    labels = sorted(
        str(item.get("name"))
        for item in (payload.get("labels") or [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    )
    assignees = sorted(
        str(item.get("login"))
        for item in (payload.get("assignees") or [])
        if isinstance(item, dict) and isinstance(item.get("login"), str)
    )
    milestone_value = payload.get("milestone")
    milestone = None
    if isinstance(milestone_value, dict):
        milestone = {
            "number": milestone_value.get("number"),
            "title": milestone_value.get("title"),
            "state": milestone_value.get("state"),
        }
    projected: dict[str, Any] = {
        "number": payload.get("number"),
        "title": payload.get("title"),
        "body": payload.get("body"),
        "state": payload.get("state"),
        "locked": payload.get("locked"),
        "labels": labels,
        "assignees": assignees,
        "milestone": milestone,
    }
    if resource == "issue":
        projected["state_reason"] = payload.get("state_reason")
    else:
        for name in ("base", "head"):
            value = payload.get(name)
            projected[name] = (
                {"ref": value.get("ref"), "sha": value.get("sha")}
                if isinstance(value, dict)
                else None
            )
        projected["draft"] = payload.get("draft")
        projected["merged_at"] = payload.get("merged_at")
    return projected


def _projection_digest(projection: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _github_identity(kind: str, value: str) -> dict[str, Any]:
    _identifier(kind, "authority kind")
    match = _GITHUB_URL_PATTERN.fullmatch(value.strip())
    if match is None:
        raise GovernanceError(
            "GitHub authority must be an https://github.com/OWNER/REPO/issues/N or /pull/N URL"
        )
    repository = f"{match.group('owner')}/{match.group('repo')}"
    resource = "issue" if match.group("resource") == "issues" else "pull"
    number = int(match.group("number"))
    return {
        "kind": kind,
        "provider": "github",
        "resource": resource,
        "repository": repository,
        "number": number,
        "url": f"https://github.com/{repository}/{'issues' if resource == 'issue' else 'pull'}/{number}",
    }


def _github_selection(resource: str) -> str:
    common = """
        number title body state locked
        labels(first: 100) { nodes { name } pageInfo { hasNextPage } }
        assignees(first: 100) { nodes { login } pageInfo { hasNextPage } }
        milestone { number title state }
    """
    if resource == "issue":
        return common + " stateReason"
    return common + """
        baseRefName baseRefOid headRefName headRefOid isDraft mergedAt
        reviewThreads(first: 100) {
          nodes { id isResolved isOutdated }
          pageInfo { hasNextPage }
        }
        statusCheckRollup {
          state
          contexts(first: 100) {
            nodes {
              __typename
              ... on CheckRun { name status conclusion }
              ... on StatusContext { context state }
            }
            pageInfo { hasNextPage }
          }
        }
    """


def _github_query(items: list[dict[str, Any]]) -> tuple[str, dict[tuple[str, str, int], tuple[str, str]]]:
    repositories: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    aliases: dict[tuple[str, str, int], tuple[str, str]] = {}
    for index, item in enumerate(items):
        repository = str(item["repository"])
        authority_alias = f"authority{index}"
        repositories.setdefault(repository, []).append((authority_alias, item))
    repository_fields: list[str] = []
    for repository_index, (repository, authorities) in enumerate(repositories.items()):
        owner, name = repository.split("/", 1)
        repository_alias = f"repository{repository_index}"
        authority_fields: list[str] = []
        for authority_alias, item in authorities:
            resource = str(item["resource"])
            field = "issue" if resource == "issue" else "pullRequest"
            number = int(item["number"])
            authority_fields.append(
                f"{authority_alias}: {field}(number: {number}) {{ {_github_selection(resource)} }}"
            )
            aliases[(repository, resource, number)] = (repository_alias, authority_alias)
        repository_fields.append(
            f"{repository_alias}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) "
            f"{{ {' '.join(authority_fields)} }}"
        )
    return "query { " + " ".join(repository_fields) + " }", aliases


def _github_graphql_fetch(items: list[dict[str, Any]]) -> dict[str, Any]:
    query, _ = _github_query(items)
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "--method", "POST", "-f", f"query={query}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GovernanceError(f"cannot read GitHub authority snapshot: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or f"gh exited {result.returncode}"
        raise GovernanceError(f"cannot read GitHub authority snapshot: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GovernanceError("GitHub authority snapshot returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GovernanceError("GitHub authority snapshot returned a non-object")
    if payload.get("errors"):
        raise GovernanceError("GitHub authority snapshot returned GraphQL errors")
    return payload


def _connection(payload: dict[str, Any], name: str) -> list[dict[str, Any]]:
    value = payload.get(name)
    if not isinstance(value, dict):
        return []
    page_info = value.get("pageInfo")
    if isinstance(page_info, dict) and page_info.get("hasNextPage") is True:
        raise GovernanceError(f"GitHub authority snapshot is incomplete: {name} exceeds 100 nodes")
    nodes = value.get("nodes")
    if not isinstance(nodes, list):
        return []
    return [node for node in nodes if isinstance(node, dict)]


def _lower_optional(value: Any) -> Optional[str]:
    return value.lower() if isinstance(value, str) and value else None


def _github_graphql_projection(payload: dict[str, Any], resource: str) -> tuple[dict[str, Any], dict[str, Any]]:
    milestone_value = payload.get("milestone")
    milestone = None
    if isinstance(milestone_value, dict):
        milestone = {
            "number": milestone_value.get("number"),
            "title": milestone_value.get("title"),
            "state": _lower_optional(milestone_value.get("state")),
        }
    labels = sorted(
        str(node["name"])
        for node in _connection(payload, "labels")
        if isinstance(node.get("name"), str)
    )
    assignees = sorted(
        str(node["login"])
        for node in _connection(payload, "assignees")
        if isinstance(node.get("login"), str)
    )
    core: dict[str, Any] = {
        "number": payload.get("number"),
        "title": payload.get("title"),
        "body": payload.get("body"),
        "state": _lower_optional(payload.get("state")),
        "locked": payload.get("locked"),
        "labels": labels,
        "assignees": assignees,
        "milestone": milestone,
    }
    evidence: dict[str, Any] = {
        "number": payload.get("number"),
        "title": payload.get("title"),
        "state": core["state"],
        "locked": payload.get("locked"),
        "labels": labels,
        "assignees": assignees,
        "body_sha256": hashlib.sha256(str(payload.get("body") or "").encode("utf-8")).hexdigest(),
    }
    if resource == "issue":
        state_reason = _lower_optional(payload.get("stateReason"))
        core["state_reason"] = state_reason
        evidence["state_reason"] = state_reason
        return core, evidence
    core.update(
        {
            "base": {"ref": payload.get("baseRefName"), "sha": payload.get("baseRefOid")},
            "head": {"ref": payload.get("headRefName"), "sha": payload.get("headRefOid")},
            "draft": payload.get("isDraft"),
            "merged_at": payload.get("mergedAt"),
        }
    )
    review_threads = sorted(
        (
            {
                "id": node.get("id"),
                "resolved": node.get("isResolved"),
                "outdated": node.get("isOutdated"),
            }
            for node in _connection(payload, "reviewThreads")
        ),
        key=lambda node: str(node.get("id")),
    )
    rollup = payload.get("statusCheckRollup")
    check_state = None
    checks: list[dict[str, Any]] = []
    if isinstance(rollup, dict):
        check_state = _lower_optional(rollup.get("state"))
        checks = sorted(
            (
                {
                    "type": node.get("__typename"),
                    "name": node.get("name") or node.get("context"),
                    "status": node.get("status"),
                    "conclusion": node.get("conclusion") or node.get("state"),
                }
                for node in _connection(rollup, "contexts")
            ),
            key=lambda node: (str(node.get("type")), str(node.get("name"))),
        )
    full = {
        **core,
        "review_threads": review_threads,
        "status_check_rollup": {"state": check_state, "checks": checks},
    }
    evidence.update(
        {
            "base": core["base"],
            "head": core["head"],
            "draft": core["draft"],
            "merged_at": core["merged_at"],
            "review_threads": {
                "total": len(review_threads),
                "unresolved": sum(1 for item in review_threads if item.get("resolved") is False),
            },
            "status_check_rollup": {"state": check_state, "checks": checks},
        }
    )
    return full, evidence


def _github_legacy_projection(full: dict[str, Any], resource: str) -> dict[str, Any]:
    projection = {
        name: copy.deepcopy(full.get(name))
        for name in ("number", "title", "body", "state", "locked", "labels", "assignees", "milestone")
    }
    if resource == "issue":
        projection["state_reason"] = full.get("state_reason")
    else:
        if projection["state"] == "merged":
            projection["state"] = "closed"
        projection.update(
            {
                "base": copy.deepcopy(full.get("base")),
                "head": copy.deepcopy(full.get("head")),
                "draft": full.get("draft"),
                "merged_at": full.get("merged_at"),
            }
        )
    return projection


def _github_snapshots(items: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    if not items:
        return {}
    _, aliases = _github_query(items)
    response = _github_graphql_fetch(items)
    data = response.get("data")
    if not isinstance(data, dict):
        raise GovernanceError("GitHub authority snapshot lacks data")
    snapshots: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in items:
        key = (str(item["repository"]), str(item["resource"]), int(item["number"]))
        repository_alias, authority_alias = aliases[key]
        repository_payload = data.get(repository_alias)
        payload = repository_payload.get(authority_alias) if isinstance(repository_payload, dict) else None
        if not isinstance(payload, dict) or payload.get("number") != item["number"]:
            raise GovernanceError(
                f"GitHub authority snapshot is missing {item['repository']}#{item['number']}"
            )
        full, evidence = _github_graphql_projection(payload, str(item["resource"]))
        snapshots[key] = {
            _GITHUB_LEGACY_PROJECTION: _github_legacy_projection(
                full, str(item["resource"])
            ),
            _GITHUB_PROJECTION: full,
            "evidence": evidence,
        }
    return snapshots


def _github_authorities(values: list[tuple[str, str]]) -> list[dict[str, Any]]:
    identities = [_github_identity(kind, value) for kind, value in values]
    snapshots = _github_snapshots(identities)
    authorities: list[dict[str, Any]] = []
    for identity in identities:
        key = (
            str(identity["repository"]),
            str(identity["resource"]),
            int(identity["number"]),
        )
        authorities.append(
            {
                **identity,
                "projection_version": _GITHUB_PROJECTION,
                "sha256": _projection_digest(snapshots[key][_GITHUB_PROJECTION]),
            }
        )
    return authorities


def _github_authority(kind: str, value: str) -> dict[str, Any]:
    return _github_authorities([(kind, value)])[0]


def _refresh_authority(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    if item.get("provider") == "github":
        return _github_authority(str(item["kind"]), str(item["url"]))
    return _authority(root, str(item["kind"]), str(item["path"]))


def _validate_checkpoint(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise GovernanceError("work-unit state has an invalid checkpoint")
    sequence = value.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise GovernanceError("work-unit state has an invalid checkpoint sequence")
    _timestamp(value.get("recorded_at"), "checkpoint timestamp")
    _bounded_text(value.get("summary", "") if isinstance(value.get("summary"), str) else "", "checkpoint summary")
    _bounded_text(
        value.get("next_action", "") if isinstance(value.get("next_action"), str) else "",
        "checkpoint next action",
    )
    for key, label in (("findings", "checkpoint findings"), ("failed_attempts", "checkpoint failed attempts")):
        items = value.get(key)
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise GovernanceError(f"work-unit state has invalid {label}")
        _bounded_list(items, label)


def _validate_state(document: Any, path: Path) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise GovernanceError("unsupported or invalid work-unit state")
    schema = document.get("schema_version")
    if schema not in SUPPORTED_SCHEMA_VERSIONS:
        raise GovernanceError("unsupported or invalid work-unit state")
    if document.get("work_unit_id") != path.parent.name:
        raise GovernanceError("work-unit state ID does not match its directory")
    _identifier(str(document.get("work_unit_id", "")), "stored work-unit ID")
    actor_id = document.get("actor_id")
    if not isinstance(actor_id, str):
        raise GovernanceError("work-unit state has an invalid actor ID")
    _identifier(actor_id, "stored actor ID")
    parent = document.get("parent_work_unit_id")
    if parent is not None:
        if not isinstance(parent, str):
            raise GovernanceError("work-unit state has an invalid parent work-unit ID")
        _identifier(parent, "stored parent work-unit ID")
        if parent == document.get("work_unit_id"):
            raise GovernanceError("a work unit cannot be its own parent")
    status = document.get("status")
    valid_statuses = {"active"} if schema == "0.1" else {"active", "closed"}
    if status not in valid_statuses:
        raise GovernanceError("work-unit state has an invalid status")
    _timestamp(document.get("created_at"), "created_at")
    _timestamp(document.get("updated_at"), "updated_at")
    authorities = document.get("authorities")
    if not isinstance(authorities, list):
        raise GovernanceError("work-unit state has invalid authorities")
    for item in authorities:
        if not isinstance(item, dict):
            raise GovernanceError("work-unit state has an invalid authority entry")
        kind = item.get("kind")
        if not isinstance(kind, str):
            raise GovernanceError("work-unit state has an invalid authority kind")
        _identifier(kind, "stored authority kind")
        provider = item.get("provider")
        if provider is None:
            _safe_relative_path(item.get("path"))
        elif provider == "github" and schema in {"0.3", SCHEMA_VERSION}:
            resource = item.get("resource")
            repository = item.get("repository")
            number = item.get("number")
            url = item.get("url")
            if resource not in {"issue", "pull"}:
                raise GovernanceError("work-unit state has an invalid GitHub resource")
            if not isinstance(repository, str) or re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
            ) is None:
                raise GovernanceError("work-unit state has an invalid GitHub repository")
            if not isinstance(number, int) or isinstance(number, bool) or number < 1:
                raise GovernanceError("work-unit state has an invalid GitHub number")
            url_match = _GITHUB_URL_PATTERN.fullmatch(url) if isinstance(url, str) else None
            if url_match is None:
                raise GovernanceError("work-unit state has an invalid GitHub URL")
            expected_resource = "issue" if url_match.group("resource") == "issues" else "pull"
            if (
                f"{url_match.group('owner')}/{url_match.group('repo')}" != repository
                or int(url_match.group("number")) != number
                or expected_resource != resource
            ):
                raise GovernanceError("work-unit state has inconsistent GitHub authority identity")
            projection_version = item.get("projection_version")
            if schema == SCHEMA_VERSION and projection_version not in _GITHUB_PROJECTIONS:
                raise GovernanceError("work-unit state has an invalid GitHub projection version")
            if schema == "0.3" and projection_version not in {None, _GITHUB_LEGACY_PROJECTION}:
                raise GovernanceError("legacy work-unit state has an invalid GitHub projection version")
        else:
            raise GovernanceError("work-unit state has an invalid authority provider")
        digest = item.get("sha256")
        if not isinstance(digest, str) or _DIGEST_PATTERN.fullmatch(digest) is None:
            raise GovernanceError("work-unit state has an invalid authority digest")
    _validate_checkpoint(document.get("checkpoint"))
    if schema != "0.1":
        revision = document.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise GovernanceError("work-unit state has an invalid revision")
        closed_at = _timestamp(document.get("closed_at"), "closed_at", nullable=True)
        close_summary = document.get("close_summary")
        if close_summary is not None:
            if not isinstance(close_summary, str):
                raise GovernanceError("work-unit state has an invalid close summary")
            _bounded_text(close_summary, "close summary")
        if status == "closed" and (closed_at is None or close_summary is None):
            raise GovernanceError("closed work-unit state lacks close metadata")
        if status == "active" and (closed_at is not None or close_summary is not None):
            raise GovernanceError("active work-unit state contains close metadata")
    return document


def _read_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GovernanceError(f"work unit does not exist: {path.parent.name}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"cannot read work-unit state: {exc}") from exc
    return _validate_state(document, path)


def _upgrade_state(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("schema_version") == SCHEMA_VERSION:
        return copy.deepcopy(state)
    upgraded = copy.deepcopy(state)
    upgraded["schema_version"] = SCHEMA_VERSION
    if state.get("schema_version") == "0.1":
        upgraded["revision"] = 1
        upgraded["closed_at"] = None
        upgraded["close_summary"] = None
    for item in upgraded.get("authorities", []):
        if item.get("provider") == "github" and "projection_version" not in item:
            item["projection_version"] = _GITHUB_LEGACY_PROJECTION
    return upgraded


def _require_actor(state: dict[str, Any], actor_id: str) -> None:
    actor = _identifier(actor_id, "actor ID")
    if state.get("actor_id") != actor:
        raise GovernanceError(
            f"work unit belongs to actor {state.get('actor_id')!r}, not {actor!r}"
        )


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(str(path), os.O_RDONLY)
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _write_document(path: Path, document: dict[str, Any]) -> None:
    _ensure_private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.stem}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(str(temporary), str(path))
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _mutation_lock(state_path: Path) -> Iterator[None]:
    _ensure_private_directory(state_path.parent)
    lock_path = state_path.parent / ".state.lock"
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    acquired = False
    while not acquired:
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(json.dumps({"pid": os.getpid(), "created_at": _now()}))
                stream.flush()
                os.fsync(stream.fileno())
            acquired = True
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > _STALE_LOCK_SECONDS:
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise GovernanceError(f"timed out waiting for work-unit lock: {state_path.parent.name}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if acquired:
            lock_path.unlink(missing_ok=True)
            _fsync_directory(state_path.parent)


def _print(document: dict[str, Any]) -> None:
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))


def _authority_status(
    root: Path, state: dict[str, Any], *, fetch_remote: bool = True
) -> tuple[bool, list[dict[str, Any]]]:
    statuses: list[dict[str, Any]] = []
    matches = True
    github_items = [
        item for item in state.get("authorities", []) if item.get("provider") == "github"
    ]
    github_snapshots = _github_snapshots(github_items) if fetch_remote and github_items else {}
    for item in state.get("authorities", []):
        if item.get("provider") == "github":
            projection_version = str(
                item.get("projection_version") or _GITHUB_LEGACY_PROJECTION
            )
            if not fetch_remote:
                statuses.append(
                    {
                        "kind": item.get("kind"),
                        "provider": "github",
                        "resource": item.get("resource"),
                        "repository": item.get("repository"),
                        "number": item.get("number"),
                        "url": item.get("url"),
                        "checked": False,
                        "completeness": "remote_check_required",
                        "projection_version": projection_version,
                        "checkpoint_sha256": item.get("sha256"),
                        "current_sha256": None,
                        "matches_checkpoint": None,
                    }
                )
                continue
            key = (
                str(item["repository"]),
                str(item["resource"]),
                int(item["number"]),
            )
            snapshot = github_snapshots[key]
            current_digest = _projection_digest(snapshot[projection_version])
            item_matches = current_digest == item.get("sha256")
            matches = matches and item_matches
            statuses.append(
                {
                    "kind": item.get("kind"),
                    "provider": "github",
                    "resource": item.get("resource"),
                    "repository": item.get("repository"),
                    "number": item.get("number"),
                    "url": item.get("url"),
                    "checked": True,
                    "completeness": "complete",
                    "projection_version": projection_version,
                    "upgrade_available": projection_version != _GITHUB_PROJECTION,
                    "checkpoint_sha256": item.get("sha256"),
                    "current_sha256": current_digest,
                    "matches_checkpoint": item_matches,
                    "evidence": snapshot["evidence"],
                }
            )
            continue
        relative = _safe_relative_path(item.get("path"))
        authority_path = (root / relative).resolve()
        exists = authority_path.is_relative_to(root) and authority_path.is_file()
        current_digest = _digest(authority_path) if exists else None
        item_matches = exists and current_digest == item.get("sha256")
        matches = matches and item_matches
        statuses.append(
            {
                "kind": item.get("kind"),
                "provider": "file",
                "path": relative,
                "checked": True,
                "completeness": "complete",
                "exists": exists,
                "checkpoint_sha256": item.get("sha256"),
                "current_sha256": current_digest,
                "matches_checkpoint": item_matches,
            }
        )
    return matches, statuses


def _base_output(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": state.get("schema_version"),
        "work_unit_id": state.get("work_unit_id"),
        "actor_id": state.get("actor_id"),
        "parent_work_unit_id": state.get("parent_work_unit_id"),
        "status": state.get("status"),
        "checkpoint": state.get("checkpoint"),
    }


def _init(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    actor = _identifier(args.actor, "actor ID")
    parent = _identifier(args.parent_work_unit, "parent work-unit ID") if args.parent_work_unit else None
    if parent == args.work_unit:
        raise GovernanceError("a work unit cannot be its own parent")
    authorities: list[dict[str, Any]] = [
        _authority(root, kind, value) for kind, value in args.authority
    ]
    authorities.extend(_github_authorities(args.github_authority))
    created_at = _now()
    state = {
        "schema_version": SCHEMA_VERSION,
        "revision": 1,
        "work_unit_id": args.work_unit,
        "actor_id": actor,
        "parent_work_unit_id": parent,
        "status": "active",
        "created_at": created_at,
        "updated_at": created_at,
        "closed_at": None,
        "close_summary": None,
        "authorities": authorities,
        "checkpoint": None,
    }
    with _mutation_lock(path):
        if path.exists():
            raise GovernanceError(f"work unit already exists: {args.work_unit}")
        _write_document(path, state)
    _print(state)
    return 0


def _checkpoint(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    if not path.is_file():
        raise GovernanceError(f"work unit does not exist: {args.work_unit}")
    with _mutation_lock(path):
        original = _read_state(path)
        _require_actor(original, args.actor)
        if original.get("status") != "active":
            raise GovernanceError("only active work units can be checkpointed")
        state = _upgrade_state(original)
        local_authorities = [
            _refresh_authority(root, item)
            for item in state.get("authorities", [])
            if item.get("provider") != "github"
        ]
        github_values = [
            (str(item["kind"]), str(item["url"]))
            for item in state.get("authorities", [])
            if item.get("provider") == "github"
        ]
        refreshed_github = _github_authorities(github_values)
        refreshed_by_identity = {
            (item["kind"], item["repository"], item["resource"], item["number"]): item
            for item in refreshed_github
        }
        local_iterator = iter(local_authorities)
        refreshed = []
        for item in state.get("authorities", []):
            if item.get("provider") == "github":
                refreshed.append(
                    refreshed_by_identity[
                        (item["kind"], item["repository"], item["resource"], item["number"])
                    ]
                )
            else:
                refreshed.append(next(local_iterator))
        prior = state.get("checkpoint")
        sequence = int(prior.get("sequence", 0)) + 1 if isinstance(prior, dict) else 1
        recorded_at = _now()
        state["authorities"] = refreshed
        state["checkpoint"] = {
            "sequence": sequence,
            "recorded_at": recorded_at,
            "summary": _bounded_text(args.summary, "summary"),
            "next_action": _bounded_text(args.next_action, "next action"),
            "findings": _bounded_list(args.finding, "finding"),
            "failed_attempts": _bounded_list(args.failed_attempt, "failed attempt"),
        }
        state["revision"] = int(state.get("revision", 0)) + 1
        state["updated_at"] = recorded_at
        _write_document(path, state)
    _print(state)
    return 0


def _resume(args: argparse.Namespace) -> int:
    started = time.monotonic()
    root = _project_root(args.project_root)
    state = _read_state(_unit_path(root, args.work_unit))
    _require_actor(state, args.actor)
    matches, statuses = _authority_status(root, state)
    output = _base_output(state)
    drift = [
        {
            key: item.get(key)
            for key in ("kind", "provider", "path", "repository", "resource", "number", "url")
            if item.get(key) is not None
        }
        for item in statuses
        if item.get("matches_checkpoint") is False
    ]
    completeness = (
        "complete"
        if all(item.get("completeness") == "complete" for item in statuses)
        else "incomplete"
    )
    output.update(
        {
            "recovery_contract_version": "0.1",
            "authorities_match_checkpoint": matches,
            "authority_status": statuses,
            "drift": drift,
            "completeness": completeness,
            "primary_action": "CONTINUE" if matches else "RECONCILE",
            "reason_code": "AUTHORITIES_MATCH" if matches else "AUTHORITY_CHANGED",
            "blocking": False,
            "diagnostics": {
                "total_ms": round((time.monotonic() - started) * 1000, 3),
                "persisted": False,
            },
        }
    )
    _print(output)
    return 1 if args.strict and not matches else 0


def _add_recommendation(
    recommendations: list[dict[str, Any]], action: str, reason_code: str
) -> None:
    if any(item["action"] == action for item in recommendations):
        return
    recommendations.append(
        {"action": action, "reason_code": reason_code, "blocking": False}
    )


def _decision_recommendations(
    *, matches: bool, status: str, event: str, signals: list[str]
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    if not matches:
        _add_recommendation(recommendations, "RECONCILE", "AUTHORITY_CHANGED")
    signal_rules = {
        "goal-changed": ("UPDATE_SPEC", "GOAL_CHANGED"),
        "implementation-drift": ("CONVERGE", "IMPLEMENTATION_DRIFT"),
        "feature-complete": ("CLOSE", "FEATURE_COMPLETE"),
        "context-noisy": ("CHECKPOINT", "CONTEXT_NOISY"),
        "repeated-failure": ("DEBUG_REVIEW", "REPEATED_FAILURE"),
        "durable-decision": ("PROMOTE_ADR", "DURABLE_DECISION"),
        "durable-agent-rule": ("PROMOTE_AGENTS", "DURABLE_AGENT_RULE"),
        "independent-work": ("WORKTREE", "INDEPENDENT_WORK"),
        "new-work-unit": ("NEW_THREAD", "NEW_WORK_UNIT"),
        "exploration-heavy": ("SUBAGENT", "EXPLORATION_HEAVY"),
        "handoff-required": ("HANDOFF", "HANDOFF_REQUIRED"),
    }
    for signal in signals:
        action, reason = signal_rules[signal]
        _add_recommendation(recommendations, action, reason)
    if status == "active" and event in ("pre-compact", "stop"):
        _add_recommendation(recommendations, "CHECKPOINT", event.replace("-", "_").upper())
    if event == "pre-compact" or "context-noisy" in signals:
        _add_recommendation(recommendations, "COMPACT", "CHECKPOINT_THEN_COMPACT")
    if event == "session-start":
        _add_recommendation(recommendations, "RESUME", "SESSION_STARTED")
    if not recommendations:
        reason = "WORK_UNIT_CLOSED_NO_ACTION" if status == "closed" else "NO_GOVERNANCE_TRIGGER"
        _add_recommendation(recommendations, "CONTINUE", reason)
    recommendations.sort(key=lambda item: _ACTION_PRIORITY[item["action"]])
    return recommendations


def _evaluate(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    state = _read_state(_unit_path(root, args.work_unit))
    _require_actor(state, args.actor)
    matches, statuses = _authority_status(root, state)
    signals = list(dict.fromkeys(args.signal))
    recommendations = _decision_recommendations(
        matches=matches,
        status=str(state.get("status")),
        event=args.event,
        signals=signals,
    )
    output = _base_output(state)
    output.update(
        {
            "event": args.event,
            "signals": signals,
            "authorities_match_checkpoint": matches,
            "authority_status": statuses,
            "primary_action": recommendations[0]["action"],
            "recommendations": recommendations,
            "blocking": False,
        }
    )
    _print(output)
    return 0


def _migrate(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    if not path.is_file():
        raise GovernanceError(f"work unit does not exist: {args.work_unit}")
    with _mutation_lock(path):
        original = _read_state(path)
        _require_actor(original, args.actor)
        if original.get("schema_version") == SCHEMA_VERSION:
            state = original
            migrated = False
        else:
            state = _upgrade_state(original)
            state["updated_at"] = _now()
            _write_document(path, state)
            migrated = True
    _print({"migrated": migrated, "state": state})
    return 0


def _remove_bindings(root: Path, work_unit_id: str, actor_id: str) -> int:
    directory = root / ".agent-runtime" / "session-bindings"
    if not directory.is_dir():
        return 0
    removed = 0
    for path in directory.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if document.get("work_unit_id") == work_unit_id and document.get("actor_id") == actor_id:
            path.unlink(missing_ok=True)
            removed += 1
    if removed:
        _fsync_directory(directory)
    return removed


def _close(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    path = _unit_path(root, args.work_unit)
    if not path.is_file():
        raise GovernanceError(f"work unit does not exist: {args.work_unit}")
    with _mutation_lock(path):
        original = _read_state(path)
        _require_actor(original, args.actor)
        if original.get("status") == "closed":
            _print({"closed": True, "already_closed": True, "state": original, "bindings_removed": 0})
            return 0
        if original.get("checkpoint") is None:
            _print({"closed": False, "reason_code": "CHECKPOINT_REQUIRED"})
            return 1
        matches, statuses = _authority_status(root, original)
        if not matches:
            _print(
                {
                    "closed": False,
                    "reason_code": "AUTHORITY_CHANGED",
                    "authority_status": statuses,
                }
            )
            return 1
        state = _upgrade_state(original)
        closed_at = _now()
        state["status"] = "closed"
        state["closed_at"] = closed_at
        state["close_summary"] = _bounded_text(args.summary, "close summary")
        state["updated_at"] = closed_at
        state["revision"] = int(state.get("revision", 0)) + 1
        _write_document(path, state)
    removed = _remove_bindings(root, args.work_unit, args.actor)
    _print({"closed": True, "already_closed": False, "state": state, "bindings_removed": removed})
    return 0


def _binding_document(
    *, session_id: str, agent_id: Optional[str], work_unit_id: str, actor_id: str
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "agent_id": agent_id,
        "work_unit_id": work_unit_id,
        "actor_id": actor_id,
        "bound_at": _now(),
    }


def _bind(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    session = _external_identifier(args.session, "session ID")
    agent = _external_identifier(args.agent_id, "agent ID") if args.agent_id else None
    state = _read_state(_unit_path(root, args.work_unit))
    _require_actor(state, args.actor)
    if state.get("status") != "active":
        raise GovernanceError("only active work units can be bound to a session")
    document = _binding_document(
        session_id=session,
        agent_id=agent,
        work_unit_id=args.work_unit,
        actor_id=args.actor,
    )
    path = _binding_path(root, session, agent)
    existing = _read_binding(root, session, agent)
    if existing is not None and (
        existing.get("work_unit_id") != args.work_unit
        or existing.get("actor_id") != args.actor
    ):
        raise GovernanceError("session is already bound to another work unit or actor")
    _write_document(path, document)
    _print(document)
    return 0


def _read_binding(
    root: Path, session_id: str, agent_id: Optional[str]
) -> Optional[dict[str, Any]]:
    path = _binding_path(root, session_id, agent_id)
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    required = ("session_id", "work_unit_id", "actor_id", "bound_at")
    if document.get("schema_version") not in {"0.2", "0.3", SCHEMA_VERSION} or not all(
        isinstance(document.get(key), str) for key in required
    ):
        return None
    if document.get("session_id") != session_id or document.get("agent_id") != agent_id:
        return None
    return document


def _resolve_binding(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    session = _external_identifier(args.session, "session ID")
    agent = _external_identifier(args.agent_id, "agent ID") if args.agent_id else None
    binding = _read_binding(root, session, agent)
    if binding is None:
        _print(
            {
                "found": False,
                "reason_code": "BINDING_NOT_FOUND",
                "session_id": session,
                "agent_id": agent,
            }
        )
        return 1
    state = _read_state(_unit_path(root, str(binding["work_unit_id"])))
    _require_actor(state, str(binding["actor_id"]))
    if state.get("status") != "active":
        _print(
            {
                "found": False,
                "reason_code": "BOUND_WORK_UNIT_CLOSED",
                "session_id": session,
                "agent_id": agent,
            }
        )
        return 1
    _print({"found": True, "binding": binding})
    return 0


def _unbind(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    _identifier(args.work_unit, "work-unit ID")
    _identifier(args.actor, "actor ID")
    session = _external_identifier(args.session, "session ID")
    agent = _external_identifier(args.agent_id, "agent ID") if args.agent_id else None
    path = _binding_path(root, session, agent)
    binding = _read_binding(root, session, agent)
    if binding is None:
        _print({"unbound": False, "already_unbound": True})
        return 0
    if binding.get("work_unit_id") != args.work_unit or binding.get("actor_id") != args.actor:
        raise GovernanceError("session binding belongs to another work unit or actor")
    path.unlink(missing_ok=True)
    _fsync_directory(path.parent)
    _print({"unbound": True, "already_unbound": False})
    return 0


def _add_common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--project-root", required=True)
    command.add_argument("--work-unit", required=True)
    command.add_argument("--actor", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="work-unit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "checkpoint", "resume", "evaluate", "migrate", "close", "bind", "unbind"):
        _add_common(subparsers.add_parser(name))
    resolve_binding = subparsers.add_parser("resolve-binding")
    resolve_binding.add_argument("--project-root", required=True)
    resolve_binding.add_argument("--session", required=True)
    resolve_binding.add_argument("--agent-id")
    initialize = subparsers.choices["init"]
    initialize.add_argument("--parent-work-unit")
    initialize.add_argument("--authority", nargs=2, action="append", default=[])
    initialize.add_argument("--github-authority", nargs=2, action="append", default=[])
    checkpoint = subparsers.choices["checkpoint"]
    checkpoint.add_argument("--summary", required=True)
    checkpoint.add_argument("--next-action", required=True)
    checkpoint.add_argument("--finding", action="append", default=[])
    checkpoint.add_argument("--failed-attempt", action="append", default=[])
    subparsers.choices["resume"].add_argument("--strict", action="store_true")
    evaluate = subparsers.choices["evaluate"]
    evaluate.add_argument("--event", choices=EVENTS, default="manual")
    evaluate.add_argument("--signal", choices=SIGNALS, action="append", default=[])
    subparsers.choices["close"].add_argument("--summary", required=True)
    for name in ("bind", "unbind"):
        command = subparsers.choices[name]
        command.add_argument("--session", required=True)
        command.add_argument("--agent-id")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    handlers = {
        "init": _init,
        "checkpoint": _checkpoint,
        "resume": _resume,
        "evaluate": _evaluate,
        "migrate": _migrate,
        "close": _close,
        "bind": _bind,
        "resolve-binding": _resolve_binding,
        "unbind": _unbind,
    }
    try:
        return handlers[args.command](args)
    except (GovernanceError, OSError) as exc:
        print(f"context-governance: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
