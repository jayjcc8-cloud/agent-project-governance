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
    # A normal task never reads recovery state or asks for lifecycle records.
    if event != "PreCompact" and not (
        event == "SessionStart" and payload.get("source") in ("resume", "clear", "compact")
    ):
        return {"continue": True}
    root = Path(cwd).expanduser().resolve()
    if not root.is_dir():
        return {"continue": True}
    agent_id = payload.get("agent_id")
    if not isinstance(agent_id, str):
        agent_id = None
    context = _binding_context(root, session_id, agent_id)
    if context is None:
        return {"continue": True}
    if event == "SessionStart":
        return _context_output("SessionStart", _checkpoint_text(context))
    return {
        "continue": True,
        "systemMessage": (
            f"Context governance recommends CHECKPOINT for work unit "
            f"{context['binding']['work_unit_id']} before compaction. Compaction remains allowed."
        ),
    }



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
