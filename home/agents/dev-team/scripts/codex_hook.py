#!/usr/bin/env python3
"""Advisory hooks for an explicitly started development-team run."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def active(event):
    cwd = Path(event.get("cwd") or ".")
    root_result = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True)
    if root_result.returncode:
        return None
    root = Path(root_result.stdout.strip()).resolve()
    sys.path.insert(0, str(Path(__file__).parent))
    from state import home_for
    pointer = home_for(root) / "active.json"
    if not pointer.is_file():
        return None
    state = json.loads(Path(json.loads(pointer.read_text())["stateFile"]).read_text())
    if state.get("repo") != str(root) or state.get("stage") in ("ready_local", "cancelled", "blocked"):
        return None
    session = state.get("sessionId")
    if session and session != event.get("session_id"):
        return None
    return root, state


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                    "permissionDecision": "deny",
                                    "permissionDecisionReason": reason}}


def main():
    event = json.load(sys.stdin)
    match = active(event)
    if not match:
        return
    root, state = match
    name = event.get("hook_event_name")
    if name == "SessionStart":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": name,
            "additionalContext": "Active dev-team run " + state["runId"] +
            "; stage " + state["stage"] + ". Read its state and revalidate the Git snapshot before resuming."}}))
    elif name == "SubagentStart":
        role = event.get("agent_type", "")
        if role.startswith("dev_team_") or role.startswith("dev-team-"):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": name,
                "additionalContext": "You belong to dev-team run " + state["runId"] +
                ". Follow the approved scope, preserve pre-existing changes, and report evidence to the lead."}}))
    elif name == "PreToolUse":
        tool = event.get("tool_name", "")
        payload = event.get("tool_input") or {}
        command = payload.get("command", "") if isinstance(payload, dict) else ""
        if tool == "apply_patch" and isinstance(command, str):
            for path in re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", command, re.M):
                resolved = (root / path).resolve()
                if resolved == root or root in resolved.parents:
                    parts = resolved.relative_to(root).parts
                    if parts and (parts[0] in (".agents", ".claude", ".codex", ".cursor") or
                                  resolved.name in ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md")):
                        print(json.dumps(deny("Personal agent configuration must not be edited inside a repository.")))
                        return



if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        # Hooks are advisory; an unreadable state must not break unrelated work.
        pass
