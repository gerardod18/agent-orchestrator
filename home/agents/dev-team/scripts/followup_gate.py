#!/usr/bin/env python3
"""Advisory gate: while a PR follow-up is active for a repo, the parent session
may not edit files. Subagents (implementer) are exempt.

  followup_gate.py on|off|status     run from inside the repo
  followup_gate.py                   PreToolUse hook mode (reads JSON on stdin)

Not a security boundary: Bash can still write files. It stops the common slip
of the orchestrator "just fixing" review comments itself.
"""
import hashlib, json, os, subprocess, sys, time

DIR = os.path.expanduser("~/.agents/dev-team/.followup-active")
TTL = 12 * 3600  # stale flags expire so a forgotten 'off' never blocks edits for long
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def root(path):
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None


def flag(repo):
    return os.path.join(DIR, hashlib.sha1(repo.encode()).hexdigest() + ".json")


def active(repo):
    try:
        return time.time() - json.load(open(flag(repo)))["ts"] < TTL
    except Exception:
        return False


def main():
    if len(sys.argv) > 1:
        repo = root(os.getcwd())
        if not repo:
            sys.exit("run inside a git repo")
        if sys.argv[1] == "on":
            os.makedirs(DIR, exist_ok=True)
            json.dump({"repo": repo, "ts": time.time()}, open(flag(repo), "w"))
            print(f"follow-up gate ON for {repo} (expires in 12h)")
        elif sys.argv[1] == "off":
            if os.path.exists(flag(repo)):
                os.remove(flag(repo))
            print(f"follow-up gate OFF for {repo}")
        else:
            print("ON" if active(repo) else "OFF")
        return
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") not in EDIT_TOOLS or data.get("agent_id"):
        return
    repo = root(data.get("cwd") or os.getcwd())
    target = (data.get("tool_input") or {}).get("file_path", "")
    if not repo or not active(repo) or target.startswith(os.path.expanduser("~/claude-plans")):
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "PR follow-up is active: the parent coordinates and never edits code. "
            "Dispatch dev-team-implementer with the finding batch instead."}}))


main()
