#!/usr/bin/env python3
"""Read-only adapter from Codex lifecycle hook JSON to governance advice."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import work_unit


_MAX_CONTEXT_CHARS = 5000


def _emit(document: dict[str, Any]) -> int:
    encoded = json.dumps(document, ensure_ascii=False)
    if len(encoded) > _MAX_CONTEXT_CHARS:
        document = {
            "continue": True,
            "systemMessage": "Context governance output exceeded its safety limit; run $context-governance manually.",
        }
    print(json.dumps(document, ensure_ascii=False))
    return 0


def _context_output(event: str, text: str) -> dict[str, Any]:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": text,
        },
    }


def _binding_context(
    root: Path, session_id: str, agent_id: Optional[str]
) -> Optional[dict[str, Any]]:
    binding = work_unit._read_binding(root, session_id, agent_id)
    if binding is None:
        return None
    try:
        state = work_unit._read_state(
            work_unit._unit_path(root, str(binding["work_unit_id"]))
        )
        work_unit._require_actor(state, str(binding["actor_id"]))
        matches, statuses = work_unit._authority_status(root, state, fetch_remote=False)
    except (work_unit.GovernanceError, OSError):
        return None
    return {
        "binding": binding,
        "state": state,
        "authorities_match": matches,
        "remote_check_required": any(item.get("checked") is False for item in statuses),
    }


def _checkpoint_text(context: dict[str, Any]) -> str:
    binding = context["binding"]
    state = context["state"]
    checkpoint = state.get("checkpoint")
    if isinstance(checkpoint, dict):
        checkpoint_text = (
            f"Checkpoint {checkpoint['sequence']}: {checkpoint['summary']} "
            f"Next: {checkpoint['next_action']}"
        )
    else:
        checkpoint_text = "No checkpoint has been recorded."
    match_text = "match" if context["authorities_match"] else "changed; reconcile before continuing"
    remote_text = (
        " Remote GitHub authorities were not fetched by this hook; run explicit resume or evaluate."
        if context.get("remote_check_required")
        else ""
    )
    return (
        f"Bound work unit {binding['work_unit_id']} owned by actor {binding['actor_id']}. "
        f"Local authorities {match_text}.{remote_text} {checkpoint_text}"
    )


def _main(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    if not all(isinstance(value, str) and value for value in (event, session_id, cwd)):
        return {
            "continue": True,
            "systemMessage": "Context governance received incomplete hook input; no state was read.",
        }
    root = Path(cwd).expanduser().resolve()
    if not root.is_dir():
        return {"continue": True}

    if event == "SubagentStart":
        agent_id = payload.get("agent_id")
        actor_hint = f"subagent-{agent_id}" if isinstance(agent_id, str) and agent_id else "a distinct subagent actor"
        return _context_output(
            "SubagentStart",
            f"Context governance isolation: use {actor_hint} with a distinct work unit and optional parent-work-unit. "
            "Do not bind or read the main agent's work unit.",
        )

    agent_id = payload.get("agent_id") if event == "SubagentStop" else None
    if not isinstance(agent_id, str):
        agent_id = None
    context = _binding_context(root, session_id, agent_id)

    if event == "SessionStart":
        if context is None:
            return _context_output(
                "SessionStart",
                f"Context governance session ID: {session_id}. No work unit is bound. "
                "Select the intended actor-owned work unit, resume it explicitly, then bind this session; do not guess from another actor's state.",
            )
        return _context_output("SessionStart", _checkpoint_text(context))

    if event == "PreCompact":
        detail = (
            f" for work unit {context['binding']['work_unit_id']}"
            if context is not None
            else " after explicitly selecting the current work unit"
        )
        return {
            "continue": True,
            "systemMessage": f"Context governance recommends CHECKPOINT{detail} before compaction. Compaction remains allowed.",
        }

    if event in ("SubagentStop", "Stop"):
        if context is None:
            message = "No session-bound work unit was read; checkpoint manually if durable work remains."
        else:
            message = (
                f"Context governance recommends CHECKPOINT or CLOSE for work unit "
                f"{context['binding']['work_unit_id']}."
            )
        return {"continue": True, "systemMessage": message}

    return {"continue": True}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be an object")
        return _emit(_main(payload))
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        return _emit(
            {
                "continue": True,
                "systemMessage": f"Context governance hook skipped invalid input: {exc}",
            }
        )


if __name__ == "__main__":
    raise SystemExit(main())
